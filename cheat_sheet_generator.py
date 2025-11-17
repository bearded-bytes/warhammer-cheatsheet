#!/usr/bin/env python3
"""
Generate Warhammer 40k game cheat sheets
Combines army list with catalogue data
"""

import yaml
import re
from typing import Dict, List, Optional, Any
from army_list_parser import ArmyListParser


class CheatSheetGenerator:
    """Generate formatted cheat sheets"""

    def __init__(self, catalogue_source):
        """
        Load the catalogue data

        Args:
            catalogue_source: Either a file path (str) or a dict of catalogue data
        """
        if isinstance(catalogue_source, dict):
            # Already loaded catalogue data
            self.catalogue = catalogue_source
        else:
            # File path - load from disk
            with open(catalogue_source, 'r') as f:
                self.catalogue = yaml.safe_load(f)

        # Will be populated during generation to track faction abilities
        self.faction_ability_rule_ids = set()

        # Build lookup index by name
        # Merge units with the same name to get complete data
        self.units_by_name = {}
        for unit in self.catalogue.get('units', []):
            name = unit['name']
            if name in self.units_by_name:
                existing = self.units_by_name[name]
                # Merge data from duplicate entries
                # Prefer stats from the entry that has them
                if 'stats' in unit and 'stats' not in existing:
                    existing['stats'] = unit['stats']
                # Merge abilities (avoid duplicates by name)
                if 'abilities' in unit:
                    if 'abilities' not in existing:
                        existing['abilities'] = []
                    existing_ability_names = {a['name'] for a in existing['abilities']}
                    for ability in unit['abilities']:
                        if ability['name'] not in existing_ability_names:
                            existing['abilities'].append(ability)
                # Merge weapons (avoid duplicates by profile)
                if 'weapons' in unit:
                    if 'weapons' not in existing:
                        existing['weapons'] = []
                    existing_weapon_sigs = {(w['name'], w.get('Range'), w.get('A'), w.get('weapon_type')) for w in existing['weapons']}
                    for weapon in unit['weapons']:
                        weapon_sig = (weapon['name'], weapon.get('Range'), weapon.get('A'), weapon.get('weapon_type'))
                        if weapon_sig not in existing_weapon_sigs:
                            existing['weapons'].append(weapon)
                # Merge categories
                if 'categories' in unit:
                    if 'categories' not in existing:
                        existing['categories'] = []
                    for cat in unit['categories']:
                        if cat not in existing['categories']:
                            existing['categories'].append(cat)
            else:
                # First time seeing this unit name
                self.units_by_name[name] = unit.copy()

    def find_unit(self, name: str) -> Optional[Dict[str, Any]]:
        """Find a unit in the catalogue by name"""
        # Try exact match first
        if name in self.units_by_name:
            return self.units_by_name[name]

        # Try case-insensitive match
        name_lower = name.lower()
        for unit_name, unit_data in self.units_by_name.items():
            if unit_name.lower() == name_lower:
                return unit_data

        # Try partial match (for variants)
        for unit_name, unit_data in self.units_by_name.items():
            if name_lower in unit_name.lower() or unit_name.lower() in name_lower:
                return unit_data

        return None

    def generate_cheat_sheet(self, army_list_text: str) -> Dict[str, Any]:
        """Generate a complete cheat sheet"""
        # Parse the army list
        parser = ArmyListParser(army_list_text)
        army = parser.parse()

        cheat_sheet = {
            'army_name': army['name'],
            'points': army['points'],
            'faction': army['faction'],
            'detachment': army['detachment'],
            'characters': [],
            'units': []
        }

        # Process characters (put warlord first)
        characters = army.get('characters', [])
        warlord = None
        other_chars = []

        for char in characters:
            if char.get('warlord'):
                warlord = self._enrich_unit(char)
            else:
                other_chars.append(self._enrich_unit(char))

        if warlord:
            cheat_sheet['characters'].append(warlord)
        cheat_sheet['characters'].extend(other_chars)

        # Process battleline units
        for unit in army.get('battleline', []):
            enriched = self._enrich_unit(unit)
            enriched['unit_type'] = 'Battleline'
            cheat_sheet['units'].append(enriched)

        # Process other units
        for unit in army.get('other_units', []):
            enriched = self._enrich_unit(unit)
            enriched['unit_type'] = 'Other'
            cheat_sheet['units'].append(enriched)

        # Extract faction abilities (shared rules that appear on many units)
        cheat_sheet['faction_abilities'] = self._extract_faction_abilities(cheat_sheet)

        return cheat_sheet

    def _is_character(self, unit: Dict[str, Any]) -> bool:
        """Determine if a unit is a character (single model)"""
        categories = unit.get('categories', [])
        return 'Character' in categories or 'Epic Hero' in categories

    def _is_faction_ability_by_description(self, ability: Dict[str, Any]) -> bool:
        """Check if ability is a faction ability based on its description"""
        description = ability.get('description', '')

        # Faction abilities have "If your Army Faction is" in description
        if 'If your Army Faction is' in description or 'If your army faction is' in description.lower():
            return True

        return False

    def _extract_faction_abilities(self, cheat_sheet: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract faction abilities (shared rules that appear on multiple units)"""
        all_units = cheat_sheet['characters'] + cheat_sheet['units']
        total_units = len(all_units)

        # Collect all shared rules that might be faction abilities
        # Track how many units have each ability
        ability_counts = {}  # rule_id -> (ability_data, count)

        for unit in all_units:
            # Check abilities by phase
            for phase_abilities in unit.get('abilities_by_phase', {}).values():
                for ability in phase_abilities:
                    if ability.get('is_shared_rule'):
                        rule_id = ability.get('rule_id')
                        if rule_id:
                            # Only consider if it looks like a faction ability
                            if self._is_faction_ability_by_description(ability):
                                if rule_id not in ability_counts:
                                    ability_counts[rule_id] = (ability, 0)
                                ability_counts[rule_id] = (ability_counts[rule_id][0], ability_counts[rule_id][1] + 1)

            # Also check passive abilities (e.g., "Oath of Moment")
            for ability in unit.get('passive_abilities', []):
                if ability.get('is_shared_rule'):
                    rule_id = ability.get('rule_id')
                    if rule_id:
                        # Only consider if it looks like a faction ability
                        if self._is_faction_ability_by_description(ability):
                            if rule_id not in ability_counts:
                                ability_counts[rule_id] = (ability, 0)
                            ability_counts[rule_id] = (ability_counts[rule_id][0], ability_counts[rule_id][1] + 1)

        # Store ALL rule IDs with "If your Army Faction is" for filtering from individual units
        # (includes both faction-wide and detachment-specific abilities)
        for rule_id in ability_counts.keys():
            self.faction_ability_rule_ids.add(rule_id)

        # Filter: Only include abilities that appear on at least 50% of units FOR DISPLAY
        # This filters out detachment-specific abilities from the Faction Abilities section
        threshold = max(1, total_units * 0.5)  # At least 50% of units

        potential_faction_abilities = {}
        for rule_id, (ability, count) in ability_counts.items():
            if count >= threshold:
                potential_faction_abilities[rule_id] = ability

        # All identified faction abilities (only high-frequency ones)
        faction_abilities = list(potential_faction_abilities.values())

        return faction_abilities

    def _is_faction_ability(self, ability: Dict[str, Any]) -> bool:
        """Check if an ability is a faction ability"""
        if not ability.get('is_shared_rule'):
            return False
        rule_id = ability.get('rule_id')
        return rule_id in self.faction_ability_rule_ids

    def _is_passive_ability(self, ability: Dict[str, Any]) -> bool:
        """Determine if an ability is passive (simple keyword-style)"""
        name = ability.get('name', '')
        description = ability.get('description', '')

        # Known passive ability patterns
        passive_patterns = [
            'Deep Strike', 'Leader', 'Scout', 'Stealth', 'Infiltrators',
            'Oath of Moment', 'Extra Attacks', 'Fights First', 'Lone Operative',
            'Feel No Pain', 'Deadly Demise', 'Firing Deck', 'Hover',
            'Anti-', 'Sustained Hits', 'Devastating Wounds', 'Lethal Hits'
        ]

        # Check if it's a known passive ability
        for pattern in passive_patterns:
            if pattern in name:
                return True

        # Invulnerable Save is passive
        if 'Invulnerable Save' in name:
            return True

        # Short abilities that just reference having an ability are passive
        if description and 'The bearer has the' in description and len(description) < 100:
            return True

        return False

    def _clean_battlescribe_markup(self, text: str) -> str:
        """Remove BattleScribe markup from text"""
        import re
        # Remove ^^**text^^** or ^^*text*^^ or ^^text^^ patterns
        # Keep the text content but remove the markup
        text = re.sub(r'\^\^\*\*([^)^]+?)\^\^\*\*', r'**\1**', text)  # ^^**text^^** -> **text**
        text = re.sub(r'\^\^\*\*([^)^]+?)\^\^', r'**\1**', text)      # ^^**text^^ -> **text**
        text = re.sub(r'\^\^\*([^)^]+?)\*\^\^', r'*\1*', text)        # ^^*text*^^ -> *text*
        text = re.sub(r'\^\^([^)^]+?)\^\^', r'\1', text)              # ^^text^^ -> text
        return text

    def _markdown_to_html(self, text: str) -> str:
        """Convert markdown formatting to HTML"""
        import re
        # Convert **text** to <strong>text</strong>
        text = re.sub(r'\*\*([^*]+?)\*\*', r'<strong>\1</strong>', text)
        # Convert *text* to <em>text</em> (but not if it's already part of **)
        text = re.sub(r'(?<!\*)\*([^*]+?)\*(?!\*)', r'<em>\1</em>', text)
        # Convert double newlines to paragraph breaks, single newlines to <br>
        # First split by double newlines to identify paragraphs
        paragraphs = text.split('\n\n')
        formatted_paragraphs = []
        for para in paragraphs:
            # Within each paragraph, convert single newlines to <br>
            para = para.replace('\n', '<br>')
            formatted_paragraphs.append(para.strip())
        # Join paragraphs with double line breaks for spacing
        text = '<br><br>'.join([p for p in formatted_paragraphs if p])
        return text

    def _format_passive_ability(self, ability: Dict[str, Any]) -> str:
        """Format a passive ability for display"""
        name = ability.get('name', '')
        description = ability.get('description', '')

        # Clean up BattleScribe markup
        description = self._clean_battlescribe_markup(description)

        # For Invulnerable Save, extract the value
        if 'Invulnerable Save' in name:
            # Description might be just the value like "4+" or a full sentence
            if description and description.strip().endswith('+'):
                return f"Invulnerable Save {description.strip()}"
            # Or it might say "This model has a 4+ invulnerable save"
            import re
            match = re.search(r'(\d\+)\s+invulnerable save', description)
            if match:
                return f"Invulnerable Save {match.group(1)}"
            return name

        # For Scout, extract distance if present
        if 'Scout' in name and description:
            # Look for distance pattern like "6\"" or "8\""
            import re
            match = re.search(r'(\d+)"', description)
            if match:
                return f"Scout {match.group(1)}\""

        # For abilities that just say "The bearer has the X ability", just return the name
        if 'The bearer has the' in description:
            return name

        # Otherwise return the name as-is
        return name

    def _enrich_unit(self, unit: Dict[str, Any]) -> Dict[str, Any]:
        """Enrich unit with catalogue data"""
        catalogue_unit = self.find_unit(unit['name'])

        enriched = {
            'name': unit['name'],
            'points': unit['points'],
            'warlord': unit.get('warlord', False),
            'selected_wargear': unit.get('wargear', []),
            'selected_models': unit.get('models', []),
            'enhancements': unit.get('enhancements', [])
        }

        if catalogue_unit:
            # Add stats
            if 'stats' in catalogue_unit:
                enriched['stats'] = catalogue_unit['stats']

            # Add abilities organized by phase
            if 'abilities' in catalogue_unit:
                abilities_by_phase = {
                    'Command': [],
                    'Movement': [],
                    'Shooting': [],
                    'Charge': [],
                    'Fight': [],
                    'Any': []
                }
                passive_abilities = []

                for ability in catalogue_unit['abilities']:
                    # Determine if this is a passive ability
                    if self._is_passive_ability(ability):
                        passive_abilities.append(ability)
                    else:
                        phase = ability.get('phase', 'Any')
                        ability_data = {
                            'name': ability['name'],
                            'description': self._clean_battlescribe_markup(ability.get('description', ''))
                        }
                        # Preserve metadata for faction ability filtering
                        if ability.get('is_shared_rule'):
                            ability_data['is_shared_rule'] = True
                            ability_data['rule_id'] = ability.get('rule_id')
                        abilities_by_phase[phase].append(ability_data)

                enriched['abilities_by_phase'] = abilities_by_phase
                enriched['passive_abilities'] = passive_abilities

            # Add weapons
            if 'weapons' in catalogue_unit:
                is_character = self._is_character(catalogue_unit)
                enriched['is_character'] = is_character

                # Get weapon counts from army list
                weapon_counts = self._get_weapon_counts(unit)

                # Deduplicate catalogue weapons first (by profile)
                unique_ranged = []
                unique_melee = []
                seen_profiles = set()

                for weapon in catalogue_unit['weapons']:
                    # Create profile signature
                    profile_key = (
                        weapon['name'],
                        weapon.get('Range', ''),
                        weapon.get('A', ''),
                        weapon.get('WS' if weapon.get('weapon_type') == 'Melee' else 'BS', ''),
                        weapon.get('S', ''),
                        weapon.get('AP', ''),
                        weapon.get('D', ''),
                        weapon.get('Keywords', '')
                    )

                    if profile_key not in seen_profiles:
                        seen_profiles.add(profile_key)
                        if weapon.get('weapon_type') == 'Melee':
                            unique_melee.append(weapon)
                        else:
                            unique_ranged.append(weapon)

                # Filter to only weapons that were selected
                selected_weapon_names = [w['name'] for w in unit.get('wargear', [])]
                # Also include weapons from models (for multi-model units)
                for model in unit.get('models', []):
                    for weapon in model.get('weapons', []):
                        selected_weapon_names.append(weapon['name'])

                weapons = {
                    'ranged': [],
                    'melee': []
                }

                for weapon in unique_ranged + unique_melee:
                    # Include weapon if it was selected or if no wargear specified (default loadout)
                    weapon_name = weapon['name']
                    if not selected_weapon_names or self._weapon_matches(weapon_name, selected_weapon_names):
                        # Lookup count using normalized name for matching
                        weapon_count = weapon_counts.get(self._normalize_weapon_name(weapon_name), 1)

                        weapon_data = {
                            'name': weapon['name'],
                            'range': weapon.get('Range', ''),
                            'attacks': weapon.get('A', ''),
                            'skill': weapon.get('WS' if weapon.get('weapon_type') == 'Melee' else 'BS', ''),
                            'strength': weapon.get('S', ''),
                            'ap': weapon.get('AP', ''),
                            'damage': weapon.get('D', ''),
                            'keywords': weapon.get('Keywords', ''),
                            'count': weapon_count
                        }

                        if weapon.get('weapon_type') == 'Melee':
                            weapons['melee'].append(weapon_data)
                        else:
                            weapons['ranged'].append(weapon_data)

                # Aggregate weapons for non-characters
                if not is_character:
                    weapons['ranged'] = self._aggregate_weapons(weapons['ranged'])
                    weapons['melee'] = self._aggregate_weapons(weapons['melee'])

                enriched['weapons'] = weapons

            # Add categories
            if 'categories' in catalogue_unit:
                enriched['categories'] = catalogue_unit['categories']

            # Add faction keywords
            if 'faction_keywords' in catalogue_unit:
                enriched['faction_keywords'] = catalogue_unit['faction_keywords']

        return enriched

    def _normalize_weapon_name(self, name: str) -> str:
        """Normalize weapon name for matching (lowercase, normalize special characters)"""
        # Convert to lowercase
        normalized = name.lower()
        # Normalize various dash/hyphen characters to regular hyphen
        normalized = normalized.replace('‑', '-').replace('–', '-').replace('—', '-')
        # Normalize quotes
        normalized = normalized.replace(''', "'").replace(''', "'").replace('"', '"').replace('"', '"')
        return normalized

    def _weapon_matches(self, weapon_name: str, selected_names: List[str]) -> bool:
        """Check if a weapon matches any selected weapon"""
        weapon_normalized = self._normalize_weapon_name(weapon_name)
        for selected in selected_names:
            selected_normalized = self._normalize_weapon_name(selected)
            if weapon_normalized == selected_normalized or weapon_normalized in selected_normalized or selected_normalized in weapon_normalized:
                return True
        return False

    def _get_weapon_counts(self, unit: Dict[str, Any]) -> Dict[str, int]:
        """Extract weapon counts from army list data (normalized)"""
        weapon_counts = {}

        # Count weapons from wargear list
        for wargear in unit.get('wargear', []):
            weapon_name = self._normalize_weapon_name(wargear['name'])
            count = wargear.get('count', 1)
            weapon_counts[weapon_name] = weapon_counts.get(weapon_name, 0) + count

        # Count weapons from models
        for model in unit.get('models', []):
            for weapon in model.get('weapons', []):
                weapon_name = self._normalize_weapon_name(weapon['name'])
                count = weapon.get('count', 1)
                weapon_counts[weapon_name] = weapon_counts.get(weapon_name, 0) + count

        return weapon_counts

    def _aggregate_weapons(self, weapons: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Aggregate weapons with identical profiles, summing their counts"""
        # Create a signature for each weapon based on its profile (excluding name and count)
        weapon_map = {}

        for weapon in weapons:
            # Create profile signature (all stats except count)
            profile_key = (
                weapon['name'],
                weapon['range'],
                weapon['attacks'],
                weapon['skill'],
                weapon['strength'],
                weapon['ap'],
                weapon['damage'],
                weapon['keywords']
            )

            if profile_key in weapon_map:
                # Sum the counts
                weapon_map[profile_key]['count'] += weapon.get('count', 1)
            else:
                # Add new weapon
                weapon_map[profile_key] = weapon.copy()

        # Return aggregated list
        return list(weapon_map.values())

    def format_yaml(self, cheat_sheet: Dict[str, Any]) -> str:
        """Format cheat sheet as YAML"""
        return yaml.dump(cheat_sheet, default_flow_style=False, sort_keys=False, allow_unicode=True, width=120)

    def _format_faction_ability_markdown(self, ability: Dict[str, Any], lines: List[str]):
        """Format a faction ability in compact markdown format"""
        import re

        name = ability['name']
        description = ability.get('description', '')
        phase = ability.get('phase', 'Any')

        # Clean markup
        description = self._clean_battlescribe_markup(description)

        # Compact formatting: put headers on same line as content
        lines.append(f"### {name}")
        lines.append(f"**Phase:** {phase}")
        lines.append("")

        # Split description into sections for better formatting
        # Replace multiple blank lines with double line breaks
        description = re.sub(r'\n\n\n+', '\n\n', description)

        # Format sections: put section headers and their first line together
        description = re.sub(r'\n\n(\*\*[^*]+\*\*)\n', r'\n\n\1 ', description)

        lines.append(description)
        lines.append("")
        lines.append("---")
        lines.append("")

    def _format_faction_ability_html(self, ability: Dict[str, Any]) -> str:
        """Format a faction ability in compact HTML format"""
        import re

        name = ability['name']
        description = ability.get('description', '')
        phase = ability.get('phase', 'Any')

        # Clean markup
        description = self._clean_battlescribe_markup(description)

        # Compact formatting for HTML
        # Replace multiple blank lines with double line breaks
        description = re.sub(r'\n\n\n+', '\n\n', description)

        # Format sections: put section headers and their content on same line
        description = re.sub(r'\n\n(\*\*[^*]+\*\*)\n', r'\n\n\1 ', description)

        # Convert markdown to HTML
        description_html = self._markdown_to_html(description)

        html = []
        html.append('        <div class="faction-ability">')
        html.append(f'            <div class="faction-ability-header">{name} <span class="phase-tag">({phase} Phase)</span></div>')
        html.append(f'            <div class="faction-ability-description">{description_html}</div>')
        html.append('        </div>')

        return '\n'.join(html)

    def format_markdown(self, cheat_sheet: Dict[str, Any]) -> str:
        """Format cheat sheet as Markdown for easy reading"""
        lines = []

        lines.append(f"# {cheat_sheet['army_name']} - {cheat_sheet['points']} Points")
        lines.append(f"**{cheat_sheet['faction']}** - {cheat_sheet['detachment']}")
        lines.append("")

        # Display faction abilities at the top
        faction_abilities = cheat_sheet.get('faction_abilities', [])
        if faction_abilities:
            lines.append("## Faction Abilities")
            lines.append("")
            for ability in faction_abilities:
                self._format_faction_ability_markdown(ability, lines)
            lines.append("")

        lines.append("## Characters")
        lines.append("")

        for char in cheat_sheet.get('characters', []):
            self._format_unit_markdown(char, lines)

        lines.append("## Units")
        lines.append("")

        for unit in cheat_sheet.get('units', []):
            self._format_unit_markdown(unit, lines)

        return '\n'.join(lines)

    def _calculate_unit_complexity(self, unit: Dict[str, Any]) -> int:
        """Calculate a complexity score for a unit to determine page grouping"""
        score = 0

        # Base score for unit existence
        score += 5

        # Add score for weapons
        if 'weapons' in unit:
            ranged_count = len(unit['weapons'].get('ranged', []))
            melee_count = len(unit['weapons'].get('melee', []))
            score += ranged_count * 2
            score += melee_count * 2

        # Add score for abilities (excluding faction abilities)
        if 'abilities_by_phase' in unit:
            for phase_abilities in unit['abilities_by_phase'].values():
                # Filter out faction abilities when counting
                unit_abilities = [a for a in phase_abilities if not a.get('is_shared_rule') or not self._is_faction_ability(a)]
                score += len(unit_abilities) * 3

        # Add score for passive abilities
        if 'passive_abilities' in unit:
            score += len(unit['passive_abilities']) * 1

        # Add score for multi-model units
        if 'selected_models' in unit and len(unit.get('selected_models', [])) > 1:
            score += len(unit['selected_models']) * 4

        return score

    def _assign_page_groups(self, units: List[Dict[str, Any]]) -> List[str]:
        """Assign page break classes to units for optimal printing on US Letter"""
        if not units:
            return []

        # Calculate complexity for each unit
        complexities = [self._calculate_unit_complexity(unit) for unit in units]

        # Classify units: Simple (<20), Medium (20-35), Complex (>35)
        # Simple units: 3-4 per page (~25% each)
        # Medium units: 2 per page (~50% each)
        # Complex units: 1 per page (100%)
        classes = []
        for score in complexities:
            if score < 20:
                classes.append('simple')
            elif score < 35:
                classes.append('medium')
            else:
                classes.append('complex')

        # Assign page breaks based on grouping rules
        page_breaks = [''] * len(units)
        page_capacity = 0  # Track how much "space" is left on current page

        for i, unit_class in enumerate(classes):
            # Determine unit size
            if unit_class == 'simple':
                unit_size = 25  # Simple units take ~25% of page
            elif unit_class == 'medium':
                unit_size = 50  # Medium units take ~50% of page
            else:
                unit_size = 100  # Complex units take full page

            # Check if we need a page break before this unit
            if page_capacity + unit_size > 100 and page_capacity > 0:
                # Current page is full, start new page
                page_breaks[i] = 'page-break-before'
                page_capacity = unit_size
            else:
                # Fits on current page
                page_capacity += unit_size

            # If unit fills the page, reset capacity
            if page_capacity >= 100:
                page_capacity = 0

        return page_breaks

    def format_html(self, cheat_sheet: Dict[str, Any]) -> str:
        """Format cheat sheet as HTML with print-friendly CSS"""
        html_parts = []

        # HTML header with CSS
        html_parts.append('''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>''' + cheat_sheet['army_name'] + ''' - Cheat Sheet</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.4;
            color: #333;
            background: #f5f5f5;
        }

        @media screen {
            .container {
                max-width: 1200px;
                margin: 0 auto;
                padding: 20px;
            }

            .no-print {
                display: block;
                text-align: center;
                margin: 20px 0;
            }

            .print-button {
                background: #2196F3;
                color: white;
                border: none;
                padding: 12px 24px;
                font-size: 16px;
                cursor: pointer;
                border-radius: 4px;
            }

            .print-button:hover {
                background: #1976D2;
            }
        }

        @media print {
            body {
                background: white;
            }

            .no-print {
                display: none;
            }

            .container {
                max-width: 100%;
                padding: 0;
            }
        }

        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            margin-bottom: 20px;
            border-radius: 8px;
        }

        @media print {
            .header {
                border-radius: 0;
                padding: 20px;
            }
        }

        .header h1 {
            font-size: 32px;
            margin-bottom: 10px;
        }

        .header .army-info {
            font-size: 18px;
            opacity: 0.95;
        }

        .section-title {
            font-size: 28px;
            color: #667eea;
            margin: 30px 0 20px 0;
            border-bottom: 3px solid #667eea;
            padding-bottom: 10px;
        }

        @media print {
            .section-title {
                margin-top: 20px;
            }
        }

        /* Unit cards */
        .unit-card {
            background: white;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            page-break-inside: avoid;
            break-inside: avoid;
        }

        @media print {
            .unit-card {
                box-shadow: none;
                border: 2px solid #ddd;
                border-radius: 4px;
                padding: 15px;
                margin-bottom: 15px;
            }

            /* Page break control for intelligent grouping */
            .unit-card.page-break-after {
                page-break-after: always;
            }

            .unit-card.page-break-before {
                page-break-before: always;
            }
        }

        .unit-header {
            display: flex;
            justify-content: space-between;
            align-items: baseline;
            margin-bottom: 15px;
            border-bottom: 2px solid #eee;
            padding-bottom: 10px;
        }

        .unit-name {
            font-size: 24px;
            font-weight: bold;
            color: #2c3e50;
        }

        .unit-points {
            font-size: 18px;
            color: #7f8c8d;
        }

        .warlord-badge {
            display: inline-block;
            background: #f39c12;
            color: white;
            padding: 4px 12px;
            border-radius: 4px;
            font-size: 14px;
            margin-left: 10px;
        }

        .model-section {
            margin: 15px 0;
        }

        .model-header {
            font-size: 18px;
            font-weight: bold;
            color: #34495e;
            margin-bottom: 10px;
            background: #ecf0f1;
            padding: 8px 12px;
            border-radius: 4px;
        }

        /* Tables */
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 10px 0;
            font-size: 13px;
        }

        @media print {
            table {
                font-size: 11px;
            }
        }

        th {
            background: #34495e;
            color: white;
            padding: 8px;
            text-align: left;
            font-weight: 600;
        }

        td {
            padding: 6px 8px;
            border-bottom: 1px solid #ddd;
        }

        tr:last-child td {
            border-bottom: none;
        }

        tr:hover {
            background: #f8f9fa;
        }

        .weapon-section {
            margin: 15px 0;
        }

        .weapon-title {
            font-weight: bold;
            font-size: 16px;
            color: #2c3e50;
            margin: 10px 0 8px 0;
        }

        .keywords-section {
            margin: 15px 0;
            padding: 10px;
            background: #f0f4ff;
            border-left: 4px solid #667eea;
            border-radius: 4px;
            font-size: 12px;
        }

        .passive-abilities-section {
            margin: 15px 0;
            padding: 10px;
            background: #fff4e6;
            border-left: 4px solid #ff9800;
            border-radius: 4px;
            font-size: 12px;
        }

        .enhancements-section {
            margin: 15px 0;
            padding: 10px;
            background: #f3e5f5;
            border-left: 4px solid #9c27b0;
            border-radius: 4px;
            font-size: 12px;
        }

        .abilities-section {
            margin: 15px 0;
        }

        .phase-group {
            margin: 10px 0;
        }

        .phase-title {
            font-weight: bold;
            color: #667eea;
            font-size: 15px;
            margin-bottom: 6px;
        }

        .ability {
            margin: 6px 0 6px 15px;
            line-height: 1.5;
        }

        .ability-name {
            font-weight: bold;
            color: #2c3e50;
        }

        .ability-description {
            color: #555;
            margin-left: 5px;
        }

        .compact-info {
            margin: 10px 0;
            padding: 8px;
            background: #f8f9fa;
            border-left: 3px solid #667eea;
            border-radius: 4px;
            font-size: 13px;
        }

        .ability-compact {
            margin: 5px 0;
            line-height: 1.4;
            font-size: 13px;
        }

        /* Faction abilities section */
        .faction-abilities-section {
            background: white;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            page-break-inside: avoid;
            break-inside: avoid;
        }

        @media print {
            .faction-abilities-section {
                page-break-after: always;
            }
        }

        .faction-ability {
            margin: 15px 0;
            padding: 12px;
            background: #f8f9fa;
            border-left: 4px solid #764ba2;
            border-radius: 4px;
        }

        .faction-ability-header {
            font-size: 18px;
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 8px;
        }

        .phase-tag {
            font-size: 14px;
            font-weight: normal;
            color: #667eea;
            font-style: italic;
        }

        .faction-ability-description {
            font-size: 13px;
            line-height: 1.5;
            color: #555;
        }

        @media print {
            .faction-abilities-section {
                box-shadow: none;
                border: 2px solid #ddd;
                border-radius: 4px;
                padding: 15px;
                margin-bottom: 15px;
            }

            .faction-ability {
                font-size: 11px;
                padding: 8px;
                margin: 10px 0;
            }

            .faction-ability-header {
                font-size: 14px;
            }

            .phase-tag {
                font-size: 11px;
            }

            .faction-ability-description {
                font-size: 10px;
                line-height: 1.4;
            }
        }

        @media print {
            @page {
                margin: 1.5cm;
            }

            .compact-info {
                font-size: 11px;
                padding: 6px;
                margin: 8px 0;
            }

            .ability-compact {
                font-size: 11px;
                margin: 3px 0;
            }

            .keywords-section {
                font-size: 10px;
                padding: 8px;
                margin: 10px 0;
            }

            .passive-abilities-section {
                font-size: 10px;
                padding: 8px;
                margin: 10px 0;
            }

            .enhancements-section {
                font-size: 10px;
                padding: 8px;
                margin: 10px 0;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="no-print">
            <button class="print-button" onclick="window.print()">🖨️ Print Cheat Sheet</button>
        </div>

        <div class="header">
            <h1>''' + cheat_sheet['army_name'] + '''</h1>
            <div class="army-info">''' + cheat_sheet['faction'] + ''' - ''' + cheat_sheet['detachment'] + ''' - ''' + str(cheat_sheet['points']) + ''' Points</div>
        </div>
''')

        # Faction abilities section
        faction_abilities = cheat_sheet.get('faction_abilities', [])
        if faction_abilities:
            html_parts.append('        <div class="faction-abilities-section">')
            html_parts.append('            <h2 class="section-title">Faction Abilities</h2>')
            for ability in faction_abilities:
                html_parts.append(self._format_faction_ability_html(ability))
            html_parts.append('        </div>')

        # Characters section with intelligent page grouping
        characters = cheat_sheet.get('characters', [])
        html_parts.append('        <h2 class="section-title">Characters</h2>')
        if characters:
            char_page_breaks = self._assign_page_groups(characters)
            for i, char in enumerate(characters):
                html_parts.append(self._format_unit_html(char, is_character=True, page_break_class=char_page_breaks[i]))

        # Units section with intelligent page grouping
        units = cheat_sheet.get('units', [])
        html_parts.append('        <h2 class="section-title">Units</h2>')
        if units:
            unit_page_breaks = self._assign_page_groups(units)
            for i, unit in enumerate(units):
                html_parts.append(self._format_unit_html(unit, is_character=False, page_break_class=unit_page_breaks[i]))

        # Close HTML
        html_parts.append('''    </div>
</body>
</html>''')

        return '\n'.join(html_parts)

    def _format_unit_markdown(self, unit: Dict[str, Any], lines: List[str]):
        """Format a single unit in markdown"""
        warlord_marker = " ⭐ **WARLORD**" if unit.get('warlord') else ""

        # Build header with faction keywords
        header = f"### {unit['name']}"
        if 'faction_keywords' in unit and unit['faction_keywords']:
            faction_str = ', '.join(unit['faction_keywords'])
            header += f" *(Faction: {faction_str})*"
        header += f" ({unit['points']} pts){warlord_marker}"

        lines.append(header)
        lines.append("")

        is_character = unit.get('is_character', False)
        has_models = unit.get('selected_models') and len(unit.get('selected_models', [])) > 0

        # If unit has multiple model types, show them separately
        if has_models and not is_character:
            self._format_multi_model_unit(unit, lines)
        else:
            # Single stat block (for characters or units without model breakdown)
            self._format_single_model_unit(unit, lines)

    def _format_single_model_unit(self, unit: Dict[str, Any], lines: List[str]):
        """Format a unit with a single stat block and weapon set"""
        # Stats
        if 'stats' in unit:
            stats = unit['stats']
            lines.append("| M | T | SV | W | LD | OC |")
            lines.append("|---|---|----|----|----|----|")
            lines.append(f"| {stats.get('M', '-')} | {stats.get('T', '-')} | {stats.get('SV', '-')} | {stats.get('W', '-')} | {stats.get('LD', '-')} | {stats.get('OC', '-')} |")
            lines.append("")

        # Keywords
        if 'categories' in unit and unit['categories']:
            lines.append("**Keywords:** " + " | ".join(unit['categories']))
            lines.append("")

        # Enhancements (if any)
        if 'enhancements' in unit and unit['enhancements']:
            lines.append("**Enhancements:** " + ", ".join(unit['enhancements']))
            lines.append("")

        # Passive Abilities (filter out faction abilities)
        if 'passive_abilities' in unit and unit['passive_abilities']:
            # Filter out faction abilities
            unit_passives = [a for a in unit['passive_abilities'] if not a.get('is_shared_rule') or not self._is_faction_ability(a)]
            if unit_passives:
                passive_list = [self._format_passive_ability(ability) for ability in unit_passives]
                # Remove duplicates while preserving order
                seen = set()
                unique_passive = []
                for p in passive_list:
                    if p not in seen:
                        seen.add(p)
                        unique_passive.append(p)
                lines.append("**Passive Abilities:** " + " | ".join(unique_passive))
                lines.append("")

        # Weapons - display side by side using HTML table for better layout
        if 'weapons' in unit:
            weapons = unit['weapons']
            is_character = unit.get('is_character', False)
            has_ranged = bool(weapons.get('ranged'))
            has_melee = bool(weapons.get('melee'))

            if has_ranged or has_melee:
                lines.append('<table><tr>')

                # Ranged weapons column
                if has_ranged:
                    lines.append('<td valign="top">')
                    lines.append('')
                    lines.append("**Ranged Weapons:**")
                    lines.append("")
                    if is_character:
                        lines.append("| Weapon | Range | A | BS | S | AP | D | Keywords |")
                        lines.append("|--------|-------|---|----|----|----|----|----------|")
                        for w in weapons['ranged']:
                            lines.append(f"| {w['name']} | {w['range']} | {w['attacks']} | {w['skill']} | {w['strength']} | {w['ap']} | {w['damage']} | {w['keywords']} |")
                    else:
                        lines.append("| Count | Weapon | Range | A | BS | S | AP | D | Keywords |")
                        lines.append("|-------|--------|-------|---|----|----|----|----|----------|")
                        for w in weapons['ranged']:
                            count = w.get('count', 1)
                            lines.append(f"| {count} | {w['name']} | {w['range']} | {w['attacks']} | {w['skill']} | {w['strength']} | {w['ap']} | {w['damage']} | {w['keywords']} |")
                    lines.append('')
                    lines.append('</td>')

                # Melee weapons column
                if has_melee:
                    lines.append('<td valign="top">')
                    lines.append('')
                    lines.append("**Melee Weapons:**")
                    lines.append("")
                    if is_character:
                        lines.append("| Weapon | Range | A | WS | S | AP | D | Keywords |")
                        lines.append("|--------|-------|---|----|----|----|----|----------|")
                        for w in weapons['melee']:
                            lines.append(f"| {w['name']} | {w['range']} | {w['attacks']} | {w['skill']} | {w['strength']} | {w['ap']} | {w['damage']} | {w['keywords']} |")
                    else:
                        lines.append("| Count | Weapon | Range | A | WS | S | AP | D | Keywords |")
                        lines.append("|-------|--------|-------|---|----|----|----|----|----------|")
                        for w in weapons['melee']:
                            count = w.get('count', 1)
                            lines.append(f"| {count} | {w['name']} | {w['range']} | {w['attacks']} | {w['skill']} | {w['strength']} | {w['ap']} | {w['damage']} | {w['keywords']} |")
                    lines.append('')
                    lines.append('</td>')

                lines.append('</tr></table>')
                lines.append("")

        # Abilities by phase
        # Skip faction abilities (they're shown at the top)
        if 'abilities_by_phase' in unit:
            for phase in ['Any', 'Command', 'Movement', 'Shooting', 'Charge', 'Fight']:
                abilities = unit['abilities_by_phase'].get(phase, [])
                # Filter out faction abilities
                unit_abilities = [a for a in abilities if not a.get('is_shared_rule') or not self._is_faction_ability(a)]
                if unit_abilities:
                    lines.append(f"**{phase} Phase:**")
                    for ability in unit_abilities:
                        lines.append(f"- **{ability['name']}:** {ability['description']}")
                    lines.append("")

        lines.append("---")
        lines.append("")

    def _format_multi_model_unit(self, unit: Dict[str, Any], lines: List[str]):
        """Format a unit with multiple model types (e.g., Pack Leader + regular models)"""
        # Get all catalogue weapons for this unit
        all_weapons = unit.get('weapons', {})
        selected_models = unit.get('selected_models', [])

        # Show stats once at the top (all models in a unit share the same stats)
        if 'stats' in unit:
            stats = unit['stats']
            lines.append("| M | T | SV | W | LD | OC |")
            lines.append("|---|---|----|----|----|----|")
            lines.append(f"| {stats.get('M', '-')} | {stats.get('T', '-')} | {stats.get('SV', '-')} | {stats.get('W', '-')} | {stats.get('LD', '-')} | {stats.get('OC', '-')} |")
            lines.append("")

        # Helper function to check if weapon matches
        def weapon_matches(catalogue_weapon_name: str, model_weapon_names: List[str]) -> bool:
            cat_normalized = self._normalize_weapon_name(catalogue_weapon_name)
            for model_name in model_weapon_names:
                model_normalized = self._normalize_weapon_name(model_name)
                if cat_normalized == model_normalized:
                    return True
                if model_normalized in cat_normalized or cat_normalized in model_normalized:
                    exact_match_exists = any(
                        self._normalize_weapon_name(w['name']) == model_normalized
                        for w in all_weapons.get('ranged', []) + all_weapons.get('melee', [])
                    )
                    if not exact_match_exists:
                        return True
            return False

        # Helper function to get weapons for a model
        def get_model_weapons(model):
            model_weapon_names = [w['name'] for w in model.get('weapons', [])]
            ranged = []
            melee = []

            for w in all_weapons.get('ranged', []):
                if weapon_matches(w['name'], model_weapon_names):
                    for model_weapon in model.get('weapons', []):
                        if weapon_matches(w['name'], [model_weapon['name'].lower()]):
                            weapon_copy = w.copy()
                            weapon_copy['count'] = model_weapon.get('count', 1)
                            ranged.append(weapon_copy)
                            break

            for w in all_weapons.get('melee', []):
                if weapon_matches(w['name'], model_weapon_names):
                    for model_weapon in model.get('weapons', []):
                        if weapon_matches(w['name'], [model_weapon['name'].lower()]):
                            weapon_copy = w.copy()
                            weapon_copy['count'] = model_weapon.get('count', 1)
                            melee.append(weapon_copy)
                            break

            return ranged, melee

        # Helper function to format model weapons separately (for stacked layout)
        def format_model_name(model):
            model_name = model['name']
            model_count = model.get('count', 1)
            return f"**{model_name} ({model_count} model{'s' if model_count > 1 else ''})**"

        def format_ranged_weapons(model):
            lines = []
            ranged, _ = get_model_weapons(model)
            if ranged:
                lines.append("*Ranged Weapons:*")
                lines.append("")
                lines.append("| Count | Weapon | Range | A | BS | S | AP | D | Keywords |")
                lines.append("|-------|--------|-------|---|----|----|----|----|----------|")
                for w in ranged:
                    lines.append(f"| {w.get('count', 1)} | {w['name']} | {w['range']} | {w['attacks']} | {w['skill']} | {w['strength']} | {w['ap']} | {w['damage']} | {w['keywords']} |")
                lines.append('')
            return lines

        def format_melee_weapons(model):
            lines = []
            _, melee = get_model_weapons(model)
            if melee:
                lines.append("*Melee Weapons:*")
                lines.append("")
                lines.append("| Count | Weapon | Range | A | WS | S | AP | D | Keywords |")
                lines.append("|-------|--------|-------|---|----|----|----|----|----------|")
                for w in melee:
                    lines.append(f"| {w.get('count', 1)} | {w['name']} | {w['range']} | {w['attacks']} | {w['skill']} | {w['strength']} | {w['ap']} | {w['damage']} | {w['keywords']} |")
                lines.append('')
            return lines

        # Group models: find main unit (largest count) vs leaders/special
        if selected_models:
            main_model = max(selected_models, key=lambda m: m.get('count', 1))
            leader_models = [m for m in selected_models if m != main_model]

            # If there are multiple model types, use aligned two-column layout
            if leader_models:
                # Use table with separate rows for model names, ranged, and melee
                # This ensures ranged and melee sections align horizontally
                lines.append('<table style="width: 100%;"><tr>')

                # Row 1: Model names
                lines.append('<tr>')
                lines.append('<td style="width: 50%; vertical-align: top;">')
                for model in leader_models:
                    lines.append('')
                    lines.append(format_model_name(model))
                    lines.append('')
                lines.append('</td>')
                lines.append('<td style="width: 50%; vertical-align: top;">')
                lines.append('')
                lines.append(format_model_name(main_model))
                lines.append('')
                lines.append('</td>')
                lines.append('</tr>')

                # Row 2: Ranged weapons
                lines.append('<tr>')
                lines.append('<td style="width: 50%; vertical-align: top;">')
                for model in leader_models:
                    for line in format_ranged_weapons(model):
                        lines.append(line)
                lines.append('</td>')
                lines.append('<td style="width: 50%; vertical-align: top;">')
                for line in format_ranged_weapons(main_model):
                    lines.append(line)
                lines.append('</td>')
                lines.append('</tr>')

                # Row 3: Melee weapons
                lines.append('<tr>')
                lines.append('<td style="width: 50%; vertical-align: top;">')
                for model in leader_models:
                    for line in format_melee_weapons(model):
                        lines.append(line)
                lines.append('</td>')
                lines.append('<td style="width: 50%; vertical-align: top;">')
                for line in format_melee_weapons(main_model):
                    lines.append(line)
                lines.append('</td>')
                lines.append('</tr>')

                lines.append('</table>')
                lines.append("")
            else:
                # Single model type - display ranged|melee side-by-side at full width
                ranged, melee = get_model_weapons(main_model)
                lines.append(format_model_name(main_model))
                lines.append("")

                if ranged or melee:
                    lines.append('<table style="width: 100%;"><tr>')

                    if ranged:
                        lines.append('<td style="width: 50%; vertical-align: top;">')
                        for line in format_ranged_weapons(main_model):
                            lines.append(line)
                        lines.append('</td>')

                    if melee:
                        lines.append('<td style="width: 50%; vertical-align: top;">')
                        for line in format_melee_weapons(main_model):
                            lines.append(line)
                        lines.append('</td>')

                    lines.append('</tr></table>')
                    lines.append("")

        # Passive Abilities and Keywords on separate lines (filter out faction abilities)
        if 'passive_abilities' in unit and unit['passive_abilities']:
            # Filter out faction abilities
            unit_passives = [a for a in unit['passive_abilities'] if not a.get('is_shared_rule') or not self._is_faction_ability(a)]
            if unit_passives:
                passive_list = [self._format_passive_ability(ability) for ability in unit_passives]
                seen = set()
                unique_passive = []
                for p in passive_list:
                    if p not in seen:
                        seen.add(p)
                        unique_passive.append(p)
                lines.append("**Passive Abilities:** " + " | ".join(unique_passive))
                lines.append("")

        if 'categories' in unit and unit['categories']:
            lines.append("**Keywords:** " + " | ".join(unit['categories']))
            lines.append("")

        # Enhancements (if any)
        if 'enhancements' in unit and unit['enhancements']:
            lines.append("**Enhancements:** " + ", ".join(unit['enhancements']))
            lines.append("")

        # Abilities (shown once for the whole unit, more compact)
        # Skip faction abilities (they're shown at the top)
        if 'abilities_by_phase' in unit:
            for phase in ['Any', 'Command', 'Movement', 'Shooting', 'Charge', 'Fight']:
                abilities = unit['abilities_by_phase'].get(phase, [])
                # Filter out faction abilities
                unit_abilities = [a for a in abilities if not a.get('is_shared_rule') or not self._is_faction_ability(a)]
                if unit_abilities:
                    # More compact format: inline instead of bullets
                    for ability in unit_abilities:
                        lines.append(f"**{phase} Phase:** *{ability['name']}* - {ability['description']}")
                    lines.append("")

        lines.append("---")

    def _format_model_name_html(self, model: Dict[str, Any]) -> str:
        """Format model name for HTML"""
        model_name = model['name']
        model_count = model.get('count', 1)
        return f'                <div class="model-header">{model_name} ({model_count} model{"s" if model_count > 1 else ""})</div>'

    def _format_model_ranged_html(self, model: Dict[str, Any], unit: Dict[str, Any]) -> str:
        """Format ranged weapons for a model in HTML"""
        html = []
        model_weapon_names = [w['name'] for w in model.get('weapons', [])]
        all_weapons = unit.get('weapons', {})

        # Helper function
        def weapon_matches(catalogue_weapon_name: str, model_weapon_names: List[str]) -> bool:
            cat_normalized = self._normalize_weapon_name(catalogue_weapon_name)
            for model_name in model_weapon_names:
                model_normalized = self._normalize_weapon_name(model_name)
                if cat_normalized == model_normalized:
                    return True
                if model_normalized in cat_normalized or cat_normalized in model_normalized:
                    exact_match_exists = any(
                        self._normalize_weapon_name(w['name']) == model_normalized
                        for w in all_weapons.get('ranged', []) + all_weapons.get('melee', [])
                    )
                    if not exact_match_exists:
                        return True
            return False

        # Ranged weapons
        ranged_for_model = []
        for w in all_weapons.get('ranged', []):
            if weapon_matches(w['name'], model_weapon_names):
                for model_weapon in model.get('weapons', []):
                    if weapon_matches(w['name'], [model_weapon['name'].lower()]):
                        weapon_copy = w.copy()
                        weapon_copy['count'] = model_weapon.get('count', 1)
                        ranged_for_model.append(weapon_copy)
                        break

        if ranged_for_model:
            html.append('                <div class="weapon-section">')
            html.append('                    <div class="weapon-title">Ranged Weapons</div>')
            html.append('                    <table>')
            html.append('                        <tr>')
            html.append('                            <th>Count</th><th>Weapon</th><th>Range</th><th>A</th><th>BS</th><th>S</th><th>AP</th><th>D</th><th>Keywords</th>')
            html.append('                        </tr>')
            for w in ranged_for_model:
                html.append('                        <tr>')
                html.append(f'                            <td>{w.get("count", 1)}</td>')
                html.append(f'                            <td>{w["name"]}</td>')
                html.append(f'                            <td>{w["range"]}</td>')
                html.append(f'                            <td>{w["attacks"]}</td>')
                html.append(f'                            <td>{w["skill"]}</td>')
                html.append(f'                            <td>{w["strength"]}</td>')
                html.append(f'                            <td>{w["ap"]}</td>')
                html.append(f'                            <td>{w["damage"]}</td>')
                html.append(f'                            <td>{w["keywords"]}</td>')
                html.append('                        </tr>')
            html.append('                    </table>')
            html.append('                </div>')

        return '\n'.join(html)

    def _format_model_melee_html(self, model: Dict[str, Any], unit: Dict[str, Any]) -> str:
        """Format melee weapons for a model in HTML"""
        html = []
        model_weapon_names = [w['name'] for w in model.get('weapons', [])]
        all_weapons = unit.get('weapons', {})

        # Helper function
        def weapon_matches(catalogue_weapon_name: str, model_weapon_names: List[str]) -> bool:
            cat_normalized = self._normalize_weapon_name(catalogue_weapon_name)
            for model_name in model_weapon_names:
                model_normalized = self._normalize_weapon_name(model_name)
                if cat_normalized == model_normalized:
                    return True
                if model_normalized in cat_normalized or cat_normalized in model_normalized:
                    exact_match_exists = any(
                        self._normalize_weapon_name(w['name']) == model_normalized
                        for w in all_weapons.get('ranged', []) + all_weapons.get('melee', [])
                    )
                    if not exact_match_exists:
                        return True
            return False

        # Melee weapons
        melee_for_model = []
        for w in all_weapons.get('melee', []):
            if weapon_matches(w['name'], model_weapon_names):
                for model_weapon in model.get('weapons', []):
                    if weapon_matches(w['name'], [model_weapon['name'].lower()]):
                        weapon_copy = w.copy()
                        weapon_copy['count'] = model_weapon.get('count', 1)
                        melee_for_model.append(weapon_copy)
                        break

        if melee_for_model:
            html.append('                <div class="weapon-section">')
            html.append('                    <div class="weapon-title">Melee Weapons</div>')
            html.append('                    <table>')
            html.append('                        <tr>')
            html.append('                            <th>Count</th><th>Weapon</th><th>Range</th><th>A</th><th>WS</th><th>S</th><th>AP</th><th>D</th><th>Keywords</th>')
            html.append('                        </tr>')
            for w in melee_for_model:
                html.append('                        <tr>')
                html.append(f'                            <td>{w.get("count", 1)}</td>')
                html.append(f'                            <td>{w["name"]}</td>')
                html.append(f'                            <td>{w["range"]}</td>')
                html.append(f'                            <td>{w["attacks"]}</td>')
                html.append(f'                            <td>{w["skill"]}</td>')
                html.append(f'                            <td>{w["strength"]}</td>')
                html.append(f'                            <td>{w["ap"]}</td>')
                html.append(f'                            <td>{w["damage"]}</td>')
                html.append(f'                            <td>{w["keywords"]}</td>')
                html.append('                        </tr>')
            html.append('                    </table>')
            html.append('                </div>')

        return '\n'.join(html)

    def _format_unit_html(self, unit: Dict[str, Any], is_character: bool, page_break_class: str = '') -> str:
        """Format a single unit as HTML"""
        html = []

        # Determine card class with page break control
        card_class = "unit-card"
        if page_break_class:
            card_class += f" {page_break_class}"

        html.append(f'        <div class="{card_class}">')

        # Unit header with faction keywords
        warlord_badge = '<span class="warlord-badge">⭐ WARLORD</span>' if unit.get('warlord') else ''
        faction_html = ''
        if 'faction_keywords' in unit and unit['faction_keywords']:
            faction_str = ', '.join(unit['faction_keywords'])
            faction_html = f' <em>(Faction: {faction_str})</em>'

        html.append(f'            <div class="unit-header">')
        html.append(f'                <div>')
        html.append(f'                    <span class="unit-name">{unit["name"]}</span>{faction_html}')
        html.append(f'                    {warlord_badge}')
        html.append(f'                </div>')
        html.append(f'                <span class="unit-points">{unit["points"]} pts</span>')
        html.append(f'            </div>')

        # Check if multi-model unit
        has_models = unit.get('selected_models') and len(unit.get('selected_models', [])) > 0

        if has_models and not is_character:
            # Multi-model unit - show stats once, then models side-by-side
            # Stats at top
            if 'stats' in unit:
                stats = unit['stats']
                html.append('            <table>')
                html.append('                <tr>')
                html.append('                    <th>M</th><th>T</th><th>SV</th><th>W</th><th>LD</th><th>OC</th>')
                html.append('                </tr>')
                html.append('                <tr>')
                html.append(f'                    <td>{stats.get("M", "-")}</td>')
                html.append(f'                    <td>{stats.get("T", "-")}</td>')
                html.append(f'                    <td>{stats.get("SV", "-")}</td>')
                html.append(f'                    <td>{stats.get("W", "-")}</td>')
                html.append(f'                    <td>{stats.get("LD", "-")}</td>')
                html.append(f'                    <td>{stats.get("OC", "-")}</td>')
                html.append('                </tr>')
                html.append('            </table>')

            # Group models: leaders on left, main unit on right
            selected_models = unit.get('selected_models', [])
            if selected_models:
                main_model = max(selected_models, key=lambda m: m.get('count', 1))
                leader_models = [m for m in selected_models if m != main_model]

                # If there are multiple model types, use aligned two-column layout
                if leader_models:
                    html.append('            <table style="width: 100%; border: none;">')

                    # Row 1: Model names
                    html.append('                <tr>')
                    html.append('                    <td style="width: 50%; vertical-align: top; border: none;">')
                    for model in leader_models:
                        html.append(self._format_model_name_html(model))
                    html.append('                    </td>')
                    html.append('                    <td style="width: 50%; vertical-align: top; border: none;">')
                    html.append(self._format_model_name_html(main_model))
                    html.append('                    </td>')
                    html.append('                </tr>')

                    # Row 2: Ranged weapons
                    html.append('                <tr>')
                    html.append('                    <td style="width: 50%; vertical-align: top; border: none;">')
                    for model in leader_models:
                        html.append(self._format_model_ranged_html(model, unit))
                    html.append('                    </td>')
                    html.append('                    <td style="width: 50%; vertical-align: top; border: none;">')
                    html.append(self._format_model_ranged_html(main_model, unit))
                    html.append('                    </td>')
                    html.append('                </tr>')

                    # Row 3: Melee weapons
                    html.append('                <tr>')
                    html.append('                    <td style="width: 50%; vertical-align: top; border: none;">')
                    for model in leader_models:
                        html.append(self._format_model_melee_html(model, unit))
                    html.append('                    </td>')
                    html.append('                    <td style="width: 50%; vertical-align: top; border: none;">')
                    html.append(self._format_model_melee_html(main_model, unit))
                    html.append('                    </td>')
                    html.append('                </tr>')

                    html.append('            </table>')
                else:
                    # Single model type - display ranged|melee side-by-side at full width
                    html.append(self._format_model_name_html(main_model))
                    html.append('            <table style="width: 100%; border: none;"><tr>')
                    html.append('                <td style="width: 50%; vertical-align: top; border: none;">')
                    html.append(self._format_model_ranged_html(main_model, unit))
                    html.append('                </td>')
                    html.append('                <td style="width: 50%; vertical-align: top; border: none;">')
                    html.append(self._format_model_melee_html(main_model, unit))
                    html.append('                </td>')
                    html.append('            </tr></table>')
        else:
            # Single model (character or simple unit)
            html.append(self._format_single_model_html(unit))

        # Passive Abilities and Keywords on separate lines (filter out faction abilities)
        if 'passive_abilities' in unit and unit['passive_abilities']:
            # Filter out faction abilities
            unit_passives = [a for a in unit['passive_abilities'] if not a.get('is_shared_rule') or not self._is_faction_ability(a)]
            if unit_passives:
                passive_list = [self._format_passive_ability(ability) for ability in unit_passives]
                seen = set()
                unique_passive = []
                for p in passive_list:
                    if p not in seen:
                        seen.add(p)
                        unique_passive.append(p)
                passive_text = "<strong>Passive Abilities:</strong> " + " | ".join(unique_passive)
                html.append(f'            <div class="passive-abilities-section">{passive_text}</div>')

        if 'categories' in unit and unit['categories']:
            keywords_text = "<strong>Keywords:</strong> " + " | ".join(unit['categories'])
            html.append(f'            <div class="keywords-section">{keywords_text}</div>')

        # Enhancements (if any)
        if 'enhancements' in unit and unit['enhancements']:
            enhancements_text = "<strong>Enhancements:</strong> " + ", ".join(unit['enhancements'])
            html.append(f'            <div class="enhancements-section">{enhancements_text}</div>')

        # Abilities (shown once for whole unit, more compact inline format)
        # Skip faction abilities (they're shown at the top)
        if 'abilities_by_phase' in unit:
            html.append('            <div class="abilities-section">')
            for phase in ['Any', 'Command', 'Movement', 'Shooting', 'Charge', 'Fight']:
                abilities = unit['abilities_by_phase'].get(phase, [])
                # Filter out faction abilities
                unit_abilities = [a for a in abilities if not a.get('is_shared_rule') or not self._is_faction_ability(a)]
                if unit_abilities:
                    for ability in unit_abilities:
                        # Convert markdown formatting to HTML
                        description_html = self._markdown_to_html(ability["description"])
                        html.append(f'                <div class="ability-compact">')
                        html.append(f'                    <strong>{phase} Phase:</strong> <em>{ability["name"]}</em> - {description_html}')
                        html.append(f'                </div>')
            html.append('            </div>')

        html.append('        </div>')
        return '\n'.join(html)

    def _format_single_model_html(self, unit: Dict[str, Any]) -> str:
        """Format single model HTML (for characters)"""
        html = []

        # Stats
        if 'stats' in unit:
            stats = unit['stats']
            html.append('            <table>')
            html.append('                <tr>')
            html.append('                    <th>M</th><th>T</th><th>SV</th><th>W</th><th>LD</th><th>OC</th>')
            html.append('                </tr>')
            html.append('                <tr>')
            html.append(f'                    <td>{stats.get("M", "-")}</td>')
            html.append(f'                    <td>{stats.get("T", "-")}</td>')
            html.append(f'                    <td>{stats.get("SV", "-")}</td>')
            html.append(f'                    <td>{stats.get("W", "-")}</td>')
            html.append(f'                    <td>{stats.get("LD", "-")}</td>')
            html.append(f'                    <td>{stats.get("OC", "-")}</td>')
            html.append('                </tr>')
            html.append('            </table>')

        # Weapons - display side by side
        if 'weapons' in unit:
            weapons = unit['weapons']
            has_ranged = bool(weapons.get('ranged'))
            has_melee = bool(weapons.get('melee'))

            if has_ranged or has_melee:
                html.append('            <div class="weapon-section">')
                html.append('                <table style="width: 100%; border: none;"><tr>')

                # Ranged weapons column
                if has_ranged:
                    html.append('                    <td style="width: 50%; vertical-align: top; border: none;">')
                    html.append('                        <div class="weapon-title">Ranged Weapons</div>')
                    html.append('                        <table>')
                    html.append('                            <tr>')
                    html.append('                                <th>Weapon</th><th>Range</th><th>A</th><th>BS</th><th>S</th><th>AP</th><th>D</th><th>Keywords</th>')
                    html.append('                            </tr>')
                    for w in weapons['ranged']:
                        html.append('                            <tr>')
                        html.append(f'                                <td>{w["name"]}</td>')
                        html.append(f'                                <td>{w["range"]}</td>')
                        html.append(f'                                <td>{w["attacks"]}</td>')
                        html.append(f'                                <td>{w["skill"]}</td>')
                        html.append(f'                                <td>{w["strength"]}</td>')
                        html.append(f'                                <td>{w["ap"]}</td>')
                        html.append(f'                                <td>{w["damage"]}</td>')
                        html.append(f'                                <td>{w["keywords"]}</td>')
                        html.append('                            </tr>')
                    html.append('                        </table>')
                    html.append('                    </td>')

                # Melee weapons column
                if has_melee:
                    html.append('                    <td style="width: 50%; vertical-align: top; border: none;">')
                    html.append('                        <div class="weapon-title">Melee Weapons</div>')
                    html.append('                        <table>')
                    html.append('                            <tr>')
                    html.append('                                <th>Weapon</th><th>Range</th><th>A</th><th>WS</th><th>S</th><th>AP</th><th>D</th><th>Keywords</th>')
                    html.append('                            </tr>')
                    for w in weapons['melee']:
                        html.append('                            <tr>')
                        html.append(f'                                <td>{w["name"]}</td>')
                        html.append(f'                                <td>{w["range"]}</td>')
                        html.append(f'                                <td>{w["attacks"]}</td>')
                        html.append(f'                                <td>{w["skill"]}</td>')
                        html.append(f'                                <td>{w["strength"]}</td>')
                        html.append(f'                                <td>{w["ap"]}</td>')
                        html.append(f'                                <td>{w["damage"]}</td>')
                        html.append(f'                                <td>{w["keywords"]}</td>')
                        html.append('                            </tr>')
                    html.append('                        </table>')
                    html.append('                    </td>')

                html.append('                </tr></table>')
                html.append('            </div>')

        return '\n'.join(html)



def main():
    """Test the generator"""
    sample_list = """Redneck Bar Fighters #2 (2000 Points)

Space Marines
Space Wolves
Stormlance Task Force
Strike Force (2,000 Points)

CHARACTERS

Arjac Rockfist (105 Points)
  • 1x Foehammer

Logan Grimnar (110 Points)
  • Warlord
  • 1x Axe Morkai
  • 1x Storm bolter
  • 1x Tyrnak and Fenrir

Bjorn the Fell-Handed (170 Points)
  • 1x Heavy flamer
  • 1x Helfrost cannon
  • 1x Trueclaw

BATTLELINE

Blood Claws (135 Points)
  • 1x Blood Claw Pack Leader
     ◦ 1x Plasma pistol
     ◦ 1x Power weapon
  • 9x Blood Claw
     ◦ 9x Astartes chainsword
     ◦ 9x Bolt pistol
"""

    generator = CheatSheetGenerator('space_wolves.yaml')
    cheat_sheet = generator.generate_cheat_sheet(sample_list)

    # Output as markdown
    print(generator.format_markdown(cheat_sheet))

    # Also save as YAML
    with open('cheat_sheet.yaml', 'w') as f:
        f.write(generator.format_yaml(cheat_sheet))
    print("\nYAML saved to cheat_sheet.yaml")


if __name__ == '__main__':
    main()
