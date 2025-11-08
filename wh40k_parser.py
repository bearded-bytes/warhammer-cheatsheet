#!/usr/bin/env python3
"""
Warhammer 40k BattleScribe Catalogue Parser
Converts .cat XML files to structured YAML format
"""

import xml.etree.ElementTree as ET
import yaml
import re
from typing import Dict, List, Optional, Any


class CatalogueParser:
    """Parse BattleScribe .cat XML files"""

    def __init__(self, xml_file: str, load_linked_catalogues: bool = True):
        self.xml_file = xml_file
        self.tree = ET.parse(xml_file)
        self.root = self.tree.getroot()
        self.namespace = {'bs': 'http://www.battlescribe.net/schema/catalogueSchema'}

        # Build an index of shared selection entries by ID for quick lookup
        self.shared_entries = {}
        self.shared_profiles = {}  # For abilities/profiles referenced by infoLinks
        self._build_shared_entries_index()
        self._build_shared_profiles_index()

        # Load linked catalogues if requested
        if load_linked_catalogues:
            self._load_linked_catalogues()

    def _build_shared_entries_index(self, root: Optional[ET.Element] = None):
        """Build an index of all sharedSelectionEntries by ID"""
        if root is None:
            root = self.root

        for entry in root.findall('.//bs:sharedSelectionEntries/bs:selectionEntry', self.namespace):
            entry_id = entry.get('id')
            if entry_id:
                self.shared_entries[entry_id] = entry

    def _build_shared_profiles_index(self, root: Optional[ET.Element] = None):
        """Build an index of all sharedProfiles by ID"""
        if root is None:
            root = self.root

        # Index profiles from sharedProfiles
        for profile in root.findall('.//bs:sharedProfiles/bs:profile', self.namespace):
            profile_id = profile.get('id')
            if profile_id:
                self.shared_profiles[profile_id] = profile

        # Also index profiles from sharedRules
        for rule in root.findall('.//bs:sharedRules/bs:rule', self.namespace):
            rule_id = rule.get('id')
            if rule_id:
                self.shared_profiles[rule_id] = rule

    def _load_linked_catalogues(self):
        """Load shared entries from linked catalogues"""
        import os

        base_dir = os.path.dirname(self.xml_file)

        for cat_link in self.root.findall('.//bs:catalogueLinks/bs:catalogueLink', self.namespace):
            cat_name = cat_link.get('name')
            if not cat_name:
                continue

            # Try to find the linked catalogue file
            linked_file = os.path.join(base_dir, f"{cat_name}.cat")

            if os.path.exists(linked_file):
                try:
                    print(f"  Loading linked catalogue: {cat_name}")
                    linked_tree = ET.parse(linked_file)
                    linked_root = linked_tree.getroot()

                    # Add shared entries and profiles from linked catalogue
                    self._build_shared_entries_index(linked_root)
                    self._build_shared_profiles_index(linked_root)
                except Exception as e:
                    print(f"  Warning: Could not load {cat_name}: {e}")

    def parse_unit_stats(self, profile: ET.Element) -> Dict[str, Any]:
        """Extract unit statistics (M, T, SV, W, LD, OC)"""
        stats = {}
        characteristics = profile.findall('.//bs:characteristic', self.namespace)
        for char in characteristics:
            name = char.get('name')
            value = char.text
            stats[name] = value
        return stats

    def parse_weapon(self, profile: ET.Element) -> Dict[str, Any]:
        """Extract weapon characteristics"""
        weapon = {
            'name': profile.get('name'),
            'type': profile.get('typeName'),
        }
        characteristics = profile.findall('.//bs:characteristic', self.namespace)
        for char in characteristics:
            name = char.get('name')
            value = char.text
            weapon[name] = value
        return weapon

    def parse_ability(self, profile: ET.Element) -> Dict[str, Any]:
        """Extract ability information"""
        ability = {
            'name': profile.get('name'),
        }

        # Try to find description in characteristic (for profile elements)
        desc_elem = profile.find('.//bs:characteristic[@name="Description"]', self.namespace)
        if desc_elem is not None and desc_elem.text:
            ability['description'] = desc_elem.text.strip()
        else:
            # Try to find description as direct child element (for rule elements)
            desc_elem = profile.find('./bs:description', self.namespace)
            if desc_elem is not None and desc_elem.text:
                ability['description'] = desc_elem.text.strip()

        # Try to categorize by phase
        ability['phase'] = self.categorize_ability_phase(
            ability['name'],
            ability.get('description', '')
        )

        return ability

    def categorize_ability_phase(self, name: str, description: str) -> str:
        """Categorize ability by game phase"""
        text = (name + ' ' + description).lower()

        # Command phase keywords
        if any(kw in text for kw in ['command phase', 'cp', 'stratagem', 'battle-shock']):
            return 'Command'

        # Movement phase keywords
        if any(kw in text for kw in ['movement phase', 'advance', 'fall back', 'deep strike',
                                      'reserves', 'redeploy', 'move', 'charge']):
            return 'Movement'

        # Shooting phase keywords
        if any(kw in text for kw in ['shooting phase', 'ranged attack', 'shoot', 'ranged weapon',
                                      'ballistic skill', 'bs']):
            return 'Shooting'

        # Fight phase keywords
        if any(kw in text for kw in ['fight phase', 'melee', 'close combat', 'fight',
                                      'weapon skill', 'ws', 'charge']):
            return 'Fight'

        # Aura abilities can apply any time
        if 'aura' in text:
            return 'Any'

        return 'Any'

    def parse_selection_entry(self, entry: ET.Element) -> Optional[Dict[str, Any]]:
        """Parse a selectionEntry (unit or character)"""
        unit = {
            'name': entry.get('name'),
            'id': entry.get('id'),
            'type': entry.get('type'),
        }

        # Get costs
        costs = {}
        for cost in entry.findall('.//bs:cost', self.namespace):
            cost_name = cost.get('name')
            cost_value = cost.get('value')
            if cost_name == 'pts':
                costs['points'] = int(float(cost_value))
        if costs:
            unit['costs'] = costs

        # Get categories (Character, Infantry, Vehicle, etc.) and faction keywords
        categories = []
        faction_keywords = []
        for cat_link in entry.findall('.//bs:categoryLink', self.namespace):
            cat_name = cat_link.get('name')
            if cat_name:
                if 'Faction:' in cat_name:
                    # Remove "Faction: " prefix and add to faction keywords
                    faction_keywords.append(cat_name.replace('Faction: ', ''))
                else:
                    categories.append(cat_name)
        if categories:
            unit['categories'] = categories
        if faction_keywords:
            unit['faction_keywords'] = faction_keywords

        # Get unit stats
        stats_profile = entry.find('.//bs:profile[@typeName="Unit"]', self.namespace)
        if stats_profile is not None:
            unit['stats'] = self.parse_unit_stats(stats_profile)

        # Get abilities (both direct profiles and infoLinks)
        abilities = []

        # Direct ability profiles
        for profile in entry.findall('.//bs:profile[@typeName="Abilities"]', self.namespace):
            ability = self.parse_ability(profile)
            if ability:
                abilities.append(ability)

        # Follow infoLinks to get referenced abilities (both profile and rule types)
        for info_link in entry.findall('.//bs:infoLink[@type="profile"]', self.namespace):
            target_id = info_link.get('targetId')
            name = info_link.get('name')

            # Apply modifiers to the name
            modifiers = info_link.findall('.//bs:modifier[@field="name"][@type="append"]', self.namespace)
            for modifier in modifiers:
                modifier_value = modifier.get('value')
                if modifier_value:
                    name = f"{name} {modifier_value}"

            if target_id and target_id in self.shared_profiles:
                linked_profile = self.shared_profiles[target_id]
                # Only parse if it's an Abilities type
                if linked_profile.get('typeName') == 'Abilities':
                    ability = self.parse_ability(linked_profile)
                    if ability:
                        # Update the ability name with the modified name
                        if name:
                            ability['name'] = name
                        # Mark as shared profile
                        ability['is_shared_rule'] = True
                        ability['rule_id'] = target_id
                        abilities.append(ability)

        # Also follow rule-type infoLinks (for abilities like Deep Strike)
        # But filter out weapon keywords that shouldn't be unit abilities
        weapon_keywords = {
            'Rapid Fire', 'Assault', 'Heavy', 'Pistol', 'Twin-linked',
            'Devastating Wounds', 'Lethal Hits', 'Sustained Hits', 'Anti-',
            'Melta', 'Blast', 'Torrent', 'Hazardous', 'Indirect Fire',
            'Lance', 'One Shot', 'Precision', 'Psychic', 'Ignores Cover'
        }

        for info_link in entry.findall('.//bs:infoLink[@type="rule"]', self.namespace):
            target_id = info_link.get('targetId')
            name = info_link.get('name')

            # Apply modifiers to the name (e.g., "Feel No Pain" + modifier "5+" = "Feel No Pain 5+")
            modifiers = info_link.findall('.//bs:modifier[@field="name"][@type="append"]', self.namespace)
            for modifier in modifiers:
                modifier_value = modifier.get('value')
                if modifier_value:
                    name = f"{name} {modifier_value}"

            # Skip weapon keywords
            if name and any(keyword in name for keyword in weapon_keywords):
                continue

            if target_id and target_id in self.shared_profiles:
                linked_rule = self.shared_profiles[target_id]
                ability = self.parse_ability(linked_rule)
                if ability:
                    # Update the ability name with the modified name
                    ability['name'] = name
                    # Mark as shared rule (likely faction ability)
                    ability['is_shared_rule'] = True
                    ability['rule_id'] = target_id
                    abilities.append(ability)
            elif name:
                # If we can't find the rule in shared profiles, add it with just the name
                # This ensures passive abilities like "Deep Strike" are captured
                abilities.append({
                    'name': name,
                    'description': f'The bearer has the {name} ability.',
                    'phase': 'Any'
                })

        if abilities:
            unit['abilities'] = abilities

        # Get weapons (both direct profiles and entryLinks)
        weapons = []

        # Direct weapon profiles
        for profile in entry.findall('.//bs:profile[@typeName="Ranged Weapons"]', self.namespace):
            weapon = self.parse_weapon(profile)
            weapon['weapon_type'] = 'Ranged'
            weapons.append(weapon)

        for profile in entry.findall('.//bs:profile[@typeName="Melee Weapons"]', self.namespace):
            weapon = self.parse_weapon(profile)
            weapon['weapon_type'] = 'Melee'
            weapons.append(weapon)

        # Follow entryLinks to get referenced weapons
        for entry_link in entry.findall('.//bs:entryLink', self.namespace):
            target_id = entry_link.get('targetId')
            if target_id and target_id in self.shared_entries:
                linked_entry = self.shared_entries[target_id]

                # Parse weapons from the linked entry
                for profile in linked_entry.findall('.//bs:profile[@typeName="Ranged Weapons"]', self.namespace):
                    weapon = self.parse_weapon(profile)
                    weapon['weapon_type'] = 'Ranged'
                    weapons.append(weapon)

                for profile in linked_entry.findall('.//bs:profile[@typeName="Melee Weapons"]', self.namespace):
                    weapon = self.parse_weapon(profile)
                    weapon['weapon_type'] = 'Melee'
                    weapons.append(weapon)

        if weapons:
            unit['weapons'] = weapons

        return unit

    def parse_catalogue(self, include_linked: bool = True) -> Dict[str, Any]:
        """Parse entire catalogue"""
        catalogue = {
            'name': self.root.get('name'),
            'revision': self.root.get('revision'),
            'units': []
        }

        # Parse shared selection entries (main units/characters)
        for entry in self.root.findall('.//bs:sharedSelectionEntries/bs:selectionEntry', self.namespace):
            unit = self.parse_selection_entry(entry)
            if unit:
                catalogue['units'].append(unit)

        # Parse units from linked catalogues if requested
        if include_linked:
            import os
            base_dir = os.path.dirname(self.xml_file)

            for cat_link in self.root.findall('.//bs:catalogueLinks/bs:catalogueLink', self.namespace):
                cat_name = cat_link.get('name')
                if not cat_name:
                    continue

                linked_file = os.path.join(base_dir, f"{cat_name}.cat")
                if os.path.exists(linked_file):
                    try:
                        print(f"  Parsing units from: {cat_name}")
                        linked_tree = ET.parse(linked_file)
                        linked_root = linked_tree.getroot()

                        # Parse units from linked catalogue
                        for entry in linked_root.findall('.//bs:sharedSelectionEntries/bs:selectionEntry', self.namespace):
                            # Only include units that would be importable (vehicles, common units, etc.)
                            # We can filter by type or just include all
                            unit = self.parse_selection_entry(entry)
                            if unit:
                                # Mark it as from a linked catalogue
                                unit['source_catalogue'] = cat_name
                                catalogue['units'].append(unit)
                    except Exception as e:
                        print(f"  Warning: Could not parse units from {cat_name}: {e}")

        return catalogue


def main():
    """Main function"""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python wh40k_parser.py <catalogue.cat> [output.yaml]")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else input_file.replace('.cat', '.yaml')

    print(f"Parsing {input_file}...")
    parser = CatalogueParser(input_file)
    catalogue = parser.parse_catalogue()

    print(f"Found {len(catalogue['units'])} units")
    print(f"Writing to {output_file}...")

    with open(output_file, 'w') as f:
        yaml.dump(catalogue, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

    print("Done!")


if __name__ == '__main__':
    main()
