#!/usr/bin/env python3
"""
Parse Warhammer 40k army list exports
"""

import re
from typing import Dict, List, Optional, Any


class ArmyListParser:
    """Parse text-based army list exports"""

    def __init__(self, text: str):
        self.text = text
        self.lines = [line.rstrip() for line in text.split('\n')]

    def parse(self) -> Dict[str, Any]:
        """Parse the army list"""
        army = {
            'name': '',
            'points': 0,
            'faction': '',
            'detachment': '',
            'characters': [],
            'battleline': [],
            'other_units': []
        }

        current_section = None
        current_unit = None
        i = 0

        while i < len(self.lines):
            line = self.lines[i]

            # Army name and points (first line)
            if i == 0 or (not army['name'] and '(' in line and 'Points)' in line):
                match = re.match(r'^(.+?)\s*\((\d+)\s+Points\)', line)
                if match:
                    army['name'] = match.group(1).strip()
                    army['points'] = int(match.group(2))
                i += 1
                continue

            # Skip empty lines
            if not line.strip():
                i += 1
                continue

            # Faction/detachment lines
            if not line.startswith(' ') and not line.startswith('•'):
                # Check for section headers
                if line == 'CHARACTERS':
                    # Save current unit before changing sections
                    if current_unit and current_section:
                        self._add_unit_to_section(army, current_section, current_unit)
                        current_unit = None
                    current_section = 'characters'
                    i += 1
                    continue
                elif line == 'BATTLELINE':
                    # Save current unit before changing sections
                    if current_unit and current_section:
                        self._add_unit_to_section(army, current_section, current_unit)
                        current_unit = None
                    current_section = 'battleline'
                    i += 1
                    continue
                elif line == 'DEDICATED TRANSPORTS':
                    # Save current unit before changing sections
                    if current_unit and current_section:
                        self._add_unit_to_section(army, current_section, current_unit)
                        current_unit = None
                    current_section = 'other_units'
                    i += 1
                    continue
                elif line in ['OTHER DATASHEETS', 'OTHER UNITS']:
                    # Save current unit before changing sections
                    if current_unit and current_section:
                        self._add_unit_to_section(army, current_section, current_unit)
                        current_unit = None
                    current_section = 'other_units'
                    i += 1
                    continue
                elif 'Strike Force' in line or 'Combat Patrol' in line:
                    army['detachment'] = line.split('(')[0].strip()
                    i += 1
                    continue
                elif not army['faction'] and line.strip():
                    # Try to identify faction - if not a section header and not too long, it's likely the faction
                    if line not in ['CHARACTERS', 'BATTLELINE', 'DEDICATED TRANSPORTS', 'OTHER DATASHEETS', 'OTHER UNITS']:
                        army['faction'] = line.strip()
                    i += 1
                    continue

            # Unit entry (has points cost)
            if '(' in line and 'Points)' in line and not line.startswith(' '):
                # Save previous unit
                if current_unit and current_section:
                    self._add_unit_to_section(army, current_section, current_unit)

                # Parse new unit
                match = re.match(r'^(.+?)\s*\((\d+)\s+Points\)', line)
                if match:
                    current_unit = {
                        'name': match.group(1).strip(),
                        'points': int(match.group(2)),
                        'models': [],
                        'wargear': []
                    }
                i += 1
                continue

            # Warlord marker
            if '• Warlord' in line or 'Warlord' in line:
                if current_unit:
                    current_unit['warlord'] = True
                i += 1
                continue

            # Enhancements marker
            if '• Enhancements:' in line or 'Enhancements:' in line:
                if current_unit:
                    # Extract enhancement name
                    enhancement = line.split('Enhancements:')[1].strip()
                    if 'enhancements' not in current_unit:
                        current_unit['enhancements'] = []
                    current_unit['enhancements'].append(enhancement)
                i += 1
                continue

            # Model/weapon entries
            if line.startswith('  •'):
                # This is a model or weapon
                item = line.strip()[1:].strip()  # Remove bullet and whitespace

                # Skip 'Warlord' and 'Enhancements' as we handle them separately
                if item == 'Warlord' or item.startswith('Enhancements:'):
                    i += 1
                    continue

                if current_unit:
                    # Check if it's a model count (like "1x" or "9x")
                    # Models typically have "Pack Leader", "Pack Member" or are in multi-model entries
                    model_match = re.match(r'^(\d+)x\s+(.+)', item)

                    # For characters (single model units), treat everything as wargear
                    # Check by section or if it looks like a weapon name
                    is_character = current_section == 'characters'

                    if model_match:
                        count = int(model_match.group(1))
                        name = model_match.group(2).strip()

                        # Check if the next line is a nested weapon (indicates this is a model)
                        has_nested_weapons = False
                        if i + 1 < len(self.lines):
                            next_line = self.lines[i + 1]
                            if next_line.startswith('     ◦'):
                                has_nested_weapons = True

                        # If it's a character or looks like a weapon, treat as wargear
                        # UNLESS it has nested weapons (then it's definitely a model)
                        if has_nested_weapons:
                            # It's a model entry with weapons under it
                            current_unit['models'].append({
                                'name': name,
                                'count': count,
                                'weapons': []
                            })
                        elif is_character or self._looks_like_weapon(name):
                            current_unit['wargear'].append({
                                'name': name,
                                'count': count
                            })
                        else:
                            # It's a model entry
                            current_unit['models'].append({
                                'name': name,
                                'count': count,
                                'weapons': []
                            })
                    else:
                        # No count prefix, treat as wargear
                        current_unit['wargear'].append({
                            'name': item,
                            'count': 1
                        })

            # Sub-weapon entries (nested bullets)
            elif line.startswith('     ◦'):
                # This is a weapon for the current model
                item = line.strip()[1:].strip()  # Remove diamond and whitespace

                weapon_match = re.match(r'^(\d+)x\s+(.+)', item)
                if weapon_match and current_unit and current_unit['models']:
                    count = int(weapon_match.group(1))
                    weapon_name = weapon_match.group(2).strip()
                    current_unit['models'][-1]['weapons'].append({
                        'name': weapon_name,
                        'count': count
                    })
                elif current_unit and current_unit['models']:
                    current_unit['models'][-1]['weapons'].append({
                        'name': item,
                        'count': 1
                    })

            i += 1

        # Add last unit
        if current_unit:
            self._add_unit_to_section(army, current_section, current_unit)

        return army

    def _looks_like_weapon(self, name: str) -> bool:
        """Check if a name looks like a weapon rather than a model"""
        name_lower = name.lower()

        # Model name patterns (should NOT be treated as weapons)
        model_patterns = [
            'pack leader', 'pack member', 'sergeant', 'squad', 'trooper',
            'warrior', 'marine', 'guard', 'terminator', 'veteran', 'scout',
            'intercessor', 'assault', 'tactical', 'devastator', 'reiver',
            'bladeguard', 'hellblaster', 'primaris', 'blood claw', 'grey hunter',
            'long fang', 'wolf guard', 'sky claw', 'swift claw', 'thunderwolf',
            'cavalry', 'biker', 'jump pack'
        ]

        # Check if it matches a model pattern
        for pattern in model_patterns:
            if pattern in name_lower:
                return False

        # Weapon keywords
        weapon_keywords = [
            'pistol', 'bolter', 'gun', 'rifle', 'cannon', 'launcher', 'blade',
            'sword', 'axe', 'hammer', 'fist', 'staff', 'melta', 'plasma',
            'flamer', 'missile', 'grenade', 'chain', 'power', 'force', 'storm',
            'lightning', 'thunder', 'morkai', 'fenrir', 'foehammer', 'shield',
            'weapon', 'armour', 'hull', 'teeth', 'living lightning',
            # Vehicle weapons
            'laser', 'lascannon', 'destroyer', 'pod', 'stubber', 'multi-melta',
            'autocannon', 'heavy bolter', 'assault cannon', 'battle cannon'
        ]

        return any(kw in name_lower for kw in weapon_keywords)

    def _add_unit_to_section(self, army: Dict, section: Optional[str], unit: Dict):
        """Add unit to appropriate section"""
        if section == 'characters':
            army['characters'].append(unit)
        elif section == 'battleline':
            army['battleline'].append(unit)
        elif section == 'other_units':
            army['other_units'].append(unit)
        else:
            # Default to other_units if section unclear
            army['other_units'].append(unit)


def main():
    """Test the parser"""
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

BATTLELINE

Blood Claws (135 Points)
  • 1x Blood Claw Pack Leader
     ◦ 1x Plasma pistol
     ◦ 1x Power weapon
  • 9x Blood Claw
     ◦ 9x Astartes chainsword
     ◦ 9x Bolt pistol

OTHER DATASHEETS

Gladiator Lancer (160 Points)
  • 1x Armoured hull
  • 2x Fragstorm grenade launcher
"""

    parser = ArmyListParser(sample_list)
    army = parser.parse()

    import yaml
    print(yaml.dump(army, default_flow_style=False, sort_keys=False))


if __name__ == '__main__':
    main()
