# Implementation Guide: Warhammer 40k Cheat Sheet Generator

## Document Information
- **Version**: 1.0
- **Last Updated**: November 8, 2024
- **Purpose**: Step-by-step guide to rebuild this project from scratch

## Overview

This guide walks through the complete implementation process, from initial concept to final product. Follow these steps in order to recreate the cheat sheet generator.

## Phase 1: Project Setup

### Step 1.1: Create Project Structure

```bash
mkdir warhammer-cheatsheet
cd warhammer-cheatsheet
mkdir catalogues examples docs
```

### Step 1.2: Initialize Files

Create empty Python files:
```bash
touch cheat_sheet_generator.py
touch army_list_parser.py
touch wh40k_parser.py
touch generate_cheat_sheet.py
touch server.py
```

Create documentation:
```bash
touch README.md
touch .gitignore
```

### Step 1.3: Install Dependencies

```bash
pip install pyyaml
```

Only external dependency is PyYAML for reading/writing YAML files.

## Phase 2: Army List Parser (army_list_parser.py)

### Step 2.1: Basic Structure

Start with the class skeleton:

```python
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

        # Implementation will go here
        return army
```

### Step 2.2: Implement Army Header Parsing

Add to the `parse()` method:

```python
current_section = None
current_unit = None
i = 0

while i < len(self.lines):
    line = self.lines[i]

    # Skip empty lines
    if not line.strip():
        i += 1
        continue

    # Army name and points (first line or lines with points)
    if i == 0 or (not army['name'] and '(' in line and 'Points)' in line):
        match = re.match(r'^(.+?)\s*\((\d+)\s+Points\)', line)
        if match:
            army['name'] = match.group(1).strip()
            army['points'] = int(match.group(2))
        i += 1
        continue
```

### Step 2.3: Implement Section Detection

Add section header parsing:

```python
    # Check for section headers
    if line == 'CHARACTERS':
        if current_unit and current_section:
            self._add_unit_to_section(army, current_section, current_unit)
            current_unit = None
        current_section = 'characters'
        i += 1
        continue
    elif line == 'BATTLELINE':
        if current_unit and current_section:
            self._add_unit_to_section(army, current_section, current_unit)
            current_unit = None
        current_section = 'battleline'
        i += 1
        continue
    elif line in ['OTHER DATASHEETS', 'OTHER UNITS', 'DEDICATED TRANSPORTS']:
        if current_unit and current_section:
            self._add_unit_to_section(army, current_section, current_unit)
            current_unit = None
        current_section = 'other_units'
        i += 1
        continue
```

### Step 2.4: Implement Unit Parsing

Add unit entry parsing:

```python
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
```

### Step 2.5: Implement Warlord and Enhancement Parsing

```python
    # Warlord marker
    if '• Warlord' in line or 'Warlord' in line:
        if current_unit:
            current_unit['warlord'] = True
        i += 1
        continue

    # Enhancements marker
    if '• Enhancements:' in line or 'Enhancements:' in line:
        if current_unit:
            enhancement = line.split('Enhancements:')[1].strip()
            if 'enhancements' not in current_unit:
                current_unit['enhancements'] = []
            current_unit['enhancements'].append(enhancement)
        i += 1
        continue
```

### Step 2.6: Implement Wargear Parsing

This is the most complex part. Add wargear parsing with model detection:

```python
    # Model/weapon entries (  • bullet)
    if line.startswith('  •'):
        item = line.strip()[1:].strip()  # Remove bullet

        # Skip already-handled markers
        if item == 'Warlord' or item.startswith('Enhancements:'):
            i += 1
            continue

        if current_unit:
            # Check for count notation (e.g., "1x", "9x")
            model_match = re.match(r'^(\d+)x\s+(.+)', item)

            if model_match:
                count = int(model_match.group(1))
                name = model_match.group(2).strip()

                # Check if next line has nested weapons
                has_nested_weapons = False
                if i + 1 < len(self.lines):
                    next_line = self.lines[i + 1]
                    if next_line.startswith('     ◦'):
                        has_nested_weapons = True

                # Decide if it's a model or weapon
                if has_nested_weapons:
                    # It's a model with weapons
                    current_unit['models'].append({
                        'name': name,
                        'count': count,
                        'weapons': []
                    })
                elif self._looks_like_weapon(name):
                    # It's a weapon
                    current_unit['wargear'].append({
                        'name': name,
                        'count': count
                    })
                else:
                    # It's a model
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

    # Nested weapon entries (     ◦ diamond)
    elif line.startswith('     ◦'):
        item = line.strip()[1:].strip()

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
```

### Step 2.7: Implement Helper Functions

Add the weapon detection heuristic:

```python
def _looks_like_weapon(self, name: str) -> bool:
    """Check if a name looks like a weapon rather than a model"""
    name_lower = name.lower()

    # Model name patterns
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
        'lightning', 'thunder', 'shield', 'weapon', 'armour', 'hull', 'teeth',
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
        army['other_units'].append(unit)
```

### Step 2.8: Test the Parser

Create a test script:

```python
if __name__ == '__main__':
    sample_list = """Redneck Bar Fighters (1620 Points)

Space Marines
Space Wolves
Strike Force (2,000 Points)

CHARACTERS

Logan Grimnar (110 Points)
  • Warlord
  • 1x Axe Morkai
  • 1x Storm bolter

BATTLELINE

Blood Claws (135 Points)
  • 1x Blood Claw Pack Leader
     ◦ 1x Bolt pistol
     ◦ 1x Power weapon
  • 9x Blood Claw
     ◦ 9x Bolt pistol
"""

    parser = ArmyListParser(sample_list)
    army = parser.parse()

    import yaml
    print(yaml.dump(army, default_flow_style=False, sort_keys=False))
```

Run: `python3 army_list_parser.py`

## Phase 3: Catalogue Parser (wh40k_parser.py)

### Step 3.1: XML Parsing Setup

```python
#!/usr/bin/env python3
"""
Parse BattleScribe XML catalogue files to YAML
"""

import xml.etree.ElementTree as ET
import yaml
from typing import Dict, List, Optional, Any


def parse_battlescribe_catalogue(cat_file: str, output_file: str):
    """Parse a BattleScribe .cat file and save as YAML"""
    tree = ET.parse(cat_file)
    root = tree.getroot()

    catalogue = {
        'units': [],
        'shared_rules': {}
    }

    # Parse units
    for entry in root.findall(".//selectionEntry[@type='unit']"):
        unit = parse_unit_entry(entry, root)
        if unit:
            catalogue['units'].append(unit)

    # Parse shared rules
    for rule in root.findall(".//rule"):
        rule_id = rule.get('id')
        if rule_id:
            catalogue['shared_rules'][rule_id] = parse_rule(rule)

    # Write to YAML
    with open(output_file, 'w') as f:
        yaml.dump(catalogue, f, default_flow_style=False, sort_keys=False)

    print(f"Catalogue saved to {output_file}")
    print(f"  Units: {len(catalogue['units'])}")
    print(f"  Shared Rules: {len(catalogue['shared_rules'])}")
```

### Step 3.2: Unit Parsing

```python
def parse_unit_entry(entry: ET.Element, root: ET.Element) -> Optional[Dict]:
    """Parse a unit entry"""
    unit = {
        'name': entry.get('name'),
        'stats': {},
        'keywords': [],
        'faction': '',
        'abilities': [],
        'weapons': {'ranged': [], 'melee': []}
    }

    # Parse profiles
    for profile in entry.findall(".//profile"):
        type_name = profile.get('typeName', '')

        if type_name == 'Unit':
            unit['stats'] = parse_stats_profile(profile)
        elif 'Weapon' in type_name:
            weapon = parse_weapon_profile(profile)
            if weapon:
                if 'Ranged' in type_name:
                    unit['weapons']['ranged'].append(weapon)
                else:
                    unit['weapons']['melee'].append(weapon)

    # Parse abilities/rules
    for rule in entry.findall(".//rule"):
        ability = parse_rule(rule)
        if ability:
            unit['abilities'].append(ability)

    # Parse infoLinks (references to shared rules)
    for link in entry.findall(".//infoLink"):
        link_id = link.get('targetId')
        if link_id:
            # Find the referenced rule
            shared_rule = root.find(f".//rule[@id='{link_id}']")
            if shared_rule is not None:
                ability = parse_rule(shared_rule)
                if ability:
                    ability['is_shared_rule'] = True
                    ability['rule_id'] = link_id
                    unit['abilities'].append(ability)

    return unit
```

### Step 3.3: Profile Parsing

```python
def parse_stats_profile(profile: ET.Element) -> Dict[str, str]:
    """Parse unit stats profile"""
    stats = {}
    for char in profile.findall(".//characteristic"):
        name = char.get('name')
        value = char.text or ''
        stats[name] = value
    return stats

def parse_weapon_profile(profile: ET.Element) -> Optional[Dict]:
    """Parse weapon profile"""
    weapon = {
        'name': profile.get('name'),
        'range': '',
        'attacks': '',
        'skill': '',
        'strength': '',
        'ap': '',
        'damage': '',
        'keywords': []
    }

    for char in profile.findall(".//characteristic"):
        name = char.get('name', '').lower()
        value = char.text or ''

        if 'range' in name:
            weapon['range'] = value
        elif 'attack' in name or name == 'a':
            weapon['attacks'] = value
        elif 'skill' in name or name == 'bs' or name == 'ws':
            weapon['skill'] = value
        elif 'strength' in name or name == 's':
            weapon['strength'] = value
        elif 'ap' in name or 'penetration' in name:
            weapon['ap'] = value
        elif 'damage' in name or name == 'd':
            weapon['damage'] = value
        elif 'keyword' in name or 'abilit' in name:
            if value:
                weapon['keywords'] = [k.strip() for k in value.split(',')]

    return weapon if weapon['name'] else None

def parse_rule(rule: ET.Element) -> Optional[Dict]:
    """Parse ability/rule"""
    ability = {
        'name': rule.get('name', ''),
        'description': '',
        'phase': 'Any Phase',
        'is_shared_rule': False,
        'rule_id': rule.get('id', '')
    }

    # Get description
    desc_elem = rule.find('./description')
    if desc_elem is not None and desc_elem.text:
        ability['description'] = desc_elem.text

    # Try to infer phase from description
    desc_lower = ability['description'].lower()
    if 'command phase' in desc_lower:
        ability['phase'] = 'Command Phase'
    elif 'movement phase' in desc_lower:
        ability['phase'] = 'Movement Phase'
    elif 'shooting phase' in desc_lower:
        ability['phase'] = 'Shooting Phase'
    elif 'charge phase' in desc_lower:
        ability['phase'] = 'Charge Phase'
    elif 'fight phase' in desc_lower:
        ability['phase'] = 'Fight Phase'

    return ability if ability['name'] else None
```

### Step 3.4: Add Main Function

```python
def main():
    import sys

    if len(sys.argv) != 3:
        print("Usage: python3 wh40k_parser.py <input.cat> <output.yaml>")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2]

    parse_battlescribe_catalogue(input_file, output_file)

if __name__ == '__main__':
    main()
```

## Phase 4: Cheat Sheet Generator (cheat_sheet_generator.py)

This is the largest and most complex file. Build it in stages.

### Step 4.1: Class Setup

```python
#!/usr/bin/env python3
"""
Generate cheat sheets from army lists and catalogues
"""

import yaml
from typing import Dict, List, Any, Optional


class CheatSheetGenerator:
    def __init__(self, catalogue_yaml: str):
        """Load the catalogue data"""
        with open(catalogue_yaml, 'r') as f:
            self.catalogue = yaml.safe_load(f)

        # Track faction abilities for filtering
        self.faction_ability_rule_ids = set()

    def generate(self, army: Dict[str, Any], format: str = 'html') -> str:
        """Generate cheat sheet in specified format"""
        # Create enriched cheat sheet
        cheat_sheet = {
            'army_name': army['name'],
            'points': army['points'],
            'faction': army['faction'],
            'detachment': army['detachment'],
            'characters': [],
            'units': []
        }

        # Enrich characters
        for char in army['characters']:
            try:
                enriched = self._enrich_unit(char)
                cheat_sheet['characters'].append(enriched)
            except ValueError as e:
                print(f"Warning: {e}")

        # Enrich units (battleline + other)
        for unit in army['battleline'] + army['other_units']:
            try:
                enriched = self._enrich_unit(unit)
                cheat_sheet['units'].append(enriched)
            except ValueError as e:
                print(f"Warning: {e}")

        # Extract faction abilities
        faction_abilities = self._extract_faction_abilities(cheat_sheet)
        cheat_sheet['faction_abilities'] = faction_abilities

        # Generate output
        if format == 'markdown':
            return self._format_markdown(cheat_sheet)
        else:
            return self._format_html(cheat_sheet)
```

### Step 4.2: Unit Enrichment

```python
def find_unit(self, name: str) -> Optional[Dict]:
    """Find unit in catalogue by name"""
    for unit in self.catalogue['units']:
        if unit['name'].lower() == name.lower():
            return unit
    return None

def _enrich_unit(self, unit: Dict[str, Any]) -> Dict[str, Any]:
    """Enrich unit with catalogue data"""
    catalogue_unit = self.find_unit(unit['name'])

    if not catalogue_unit:
        raise ValueError(f"Unit '{unit['name']}' not found in catalogue")

    enriched = {
        'name': unit['name'],
        'points': unit['points'],
        'warlord': unit.get('warlord', False),
        'enhancements': unit.get('enhancements', []),
        'selected_wargear': unit.get('wargear', []),
        'selected_models': unit.get('models', []),
        'stats': catalogue_unit['stats'],
        'keywords': catalogue_unit.get('keywords', []),
        'faction': catalogue_unit.get('faction', ''),
        'weapons': catalogue_unit['weapons'],
        'abilities_by_phase': {},
        'passive_abilities': []
    }

    # Organize abilities by phase
    phases, passives = self._organize_abilities_by_phase(
        catalogue_unit.get('abilities', [])
    )
    enriched['abilities_by_phase'] = phases
    enriched['passive_abilities'] = passives

    return enriched
```

### Step 4.3: Faction Ability Detection

```python
def _is_faction_ability_by_description(self, ability: Dict[str, Any]) -> bool:
    """Check if ability is a faction ability based on its description"""
    description = ability.get('description', '')
    return 'if your army faction is' in description.lower()

def _extract_faction_abilities(self, cheat_sheet: Dict[str, Any]) -> List[Dict]:
    """Extract faction abilities"""
    all_units = cheat_sheet['characters'] + cheat_sheet['units']
    total_units = len(all_units)
    ability_counts = {}  # rule_id -> (ability, count)

    # Count abilities
    for unit in all_units:
        # Check regular abilities
        for phase_abilities in unit.get('abilities_by_phase', {}).values():
            for ability in phase_abilities:
                if ability.get('is_shared_rule'):
                    rule_id = ability.get('rule_id')
                    if rule_id and self._is_faction_ability_by_description(ability):
                        if rule_id not in ability_counts:
                            ability_counts[rule_id] = (ability, 0)
                        ability_counts[rule_id] = (
                            ability_counts[rule_id][0],
                            ability_counts[rule_id][1] + 1
                        )

        # Check passive abilities
        for ability in unit.get('passive_abilities', []):
            if ability.get('is_shared_rule'):
                rule_id = ability.get('rule_id')
                if rule_id and self._is_faction_ability_by_description(ability):
                    if rule_id not in ability_counts:
                        ability_counts[rule_id] = (ability, 0)
                    ability_counts[rule_id] = (
                        ability_counts[rule_id][0],
                        ability_counts[rule_id][1] + 1
                    )

    # Store all faction-like abilities for filtering
    for rule_id in ability_counts.keys():
        self.faction_ability_rule_ids.add(rule_id)

    # Apply 50% threshold for display
    threshold = max(1, total_units * 0.5)
    faction_abilities = []

    for rule_id, (ability, count) in ability_counts.items():
        if count >= threshold:
            faction_abilities.append(ability)

    return faction_abilities
```

### Step 4.4: Page Complexity (continue in next section due to length)

```python
def _calculate_unit_complexity(self, unit: Dict[str, Any]) -> int:
    """Calculate complexity score for page grouping"""
    score = 5  # Base

    # Weapons
    score += len(unit['weapons'].get('ranged', [])) * 2
    score += len(unit['weapons'].get('melee', [])) * 2

    # Abilities (excluding faction)
    for phase_abilities in unit.get('abilities_by_phase', {}).values():
        unit_abilities = [
            a for a in phase_abilities
            if not self._is_faction_ability(a)
        ]
        score += len(unit_abilities) * 3

    # Passive abilities
    score += len(unit.get('passive_abilities', [])) * 1

    # Multi-model units
    if len(unit.get('selected_models', [])) > 1:
        score += len(unit['selected_models']) * 4

    return score

def _assign_page_groups(self, units: List[Dict]) -> List[str]:
    """Assign page break classes"""
    if not units:
        return []

    complexities = [self._calculate_unit_complexity(u) for u in units]
    page_breaks = [''] * len(units)
    page_capacity = 0

    for i, score in enumerate(complexities):
        # Classify
        if score < 20:
            unit_size = 25
        elif score < 35:
            unit_size = 50
        else:
            unit_size = 100

        # Check if fits
        if page_capacity + unit_size > 100 and page_capacity > 0:
            page_breaks[i] = 'page-break-before'
            page_capacity = unit_size
        else:
            page_capacity += unit_size

        if page_capacity >= 100:
            page_capacity = 0

    return page_breaks
```

### Step 4.5: HTML Output

Create comprehensive HTML generation with CSS styling. See TECHNICAL_SPECIFICATION.md for full CSS details.

```python
def _format_html(self, cheat_sheet: Dict) -> str:
    """Generate HTML output"""
    html_parts = []

    # Add HTML header with CSS
    html_parts.append(self._get_html_header())

    # Army header
    html_parts.append(f'<h1>{cheat_sheet["army_name"]} - {cheat_sheet["points"]} Points</h1>')

    # Faction abilities
    if cheat_sheet.get('faction_abilities'):
        html_parts.append('<div class="faction-abilities-section">')
        html_parts.append('<h2>Faction Abilities</h2>')
        for ability in cheat_sheet['faction_abilities']:
            html_parts.append(self._format_ability_html(ability))
        html_parts.append('</div>')

    # Characters
    html_parts.append('<h2>Characters</h2>')
    char_breaks = self._assign_page_groups(cheat_sheet['characters'])
    for i, char in enumerate(cheat_sheet['characters']):
        html_parts.append(self._format_unit_html(char, char_breaks[i]))

    # Units
    html_parts.append('<h2>Units</h2>')
    unit_breaks = self._assign_page_groups(cheat_sheet['units'])
    for i, unit in enumerate(cheat_sheet['units']):
        html_parts.append(self._format_unit_html(unit, unit_breaks[i]))

    html_parts.append(self._get_html_footer())

    return '\n'.join(html_parts)
```

### Step 4.6: Markdown Output

```python
def _format_markdown(self, cheat_sheet: Dict) -> str:
    """Generate Markdown output"""
    lines = []

    # Title
    lines.append(f'# {cheat_sheet["army_name"]} - {cheat_sheet["points"]} Points')
    lines.append(f'**{cheat_sheet["faction"]}** - {cheat_sheet["detachment"]}')
    lines.append('')

    # Faction abilities
    if cheat_sheet.get('faction_abilities'):
        lines.append('## Faction Abilities')
        lines.append('')
        for ability in cheat_sheet['faction_abilities']:
            lines.append(f'### {ability["name"]}')
            lines.append(f'**Phase:** {ability["phase"]}')
            lines.append('')
            lines.append(ability['description'])
            lines.append('')
            lines.append('---')
            lines.append('')

    # Characters
    lines.append('## Characters')
    lines.append('')
    for char in cheat_sheet['characters']:
        lines.extend(self._format_unit_markdown(char))

    # Units
    lines.append('## Units')
    lines.append('')
    for unit in cheat_sheet['units']:
        lines.extend(self._format_unit_markdown(unit))

    return '\n'.join(lines)
```

## Phase 5: CLI Entry Point

### Step 5.1: generate_cheat_sheet.py

```python
#!/usr/bin/env python3
"""
CLI tool to generate Warhammer 40k cheat sheets
"""

import sys
import argparse
from army_list_parser import ArmyListParser
from cheat_sheet_generator import CheatSheetGenerator


def main():
    parser = argparse.ArgumentParser(
        description='Generate Warhammer 40k cheat sheets from BattleScribe army lists'
    )
    parser.add_argument('army_list', help='Path to army list text file')
    parser.add_argument('catalogue', help='Path to faction catalogue YAML file')
    parser.add_argument('-o', '--output', default='cheat_sheet.html',
                       help='Output file path')
    parser.add_argument('-f', '--format', choices=['html', 'markdown'],
                       default='html', help='Output format')

    args = parser.parse_args()

    try:
        # Read army list
        print(f'Reading army list from {args.army_list}...')
        with open(args.army_list, 'r') as f:
            army_text = f.read()

        # Parse army list
        parser = ArmyListParser(army_text)
        army = parser.parse()

        # Load catalogue and generate
        print(f'Loading catalogue from {args.catalogue}...')
        generator = CheatSheetGenerator(args.catalogue)

        print('Generating cheat sheet...')
        output = generator.generate(army, format=args.format)

        # Write output
        print(f'Writing output to {args.output}...')
        with open(args.output, 'w') as f:
            f.write(output)

        print('✓ Cheat sheet generated successfully!')
        print(f'  Army: {army["name"]}')
        print(f'  Points: {army["points"]}')
        print(f'  Characters: {len(army["characters"])}')
        print(f'  Units: {len(army["battleline"]) + len(army["other_units"])}')

    except FileNotFoundError as e:
        print(f'Error: {e}')
        sys.exit(1)
    except Exception as e:
        print(f'Error generating cheat sheet: {e}')
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
```

## Phase 6: Testing and Refinement

### Step 6.1: Create Test Army List

Save as `examples/test_army.txt`:

```
Test Army (1000 Points)

Space Marines
Space Wolves
Strike Force (2,000 Points)

CHARACTERS

Logan Grimnar (110 Points)
  • Warlord
  • 1x Axe Morkai

BATTLELINE

Blood Claws (135 Points)
  • 1x Blood Claw Pack Leader
     ◦ 1x Power weapon
  • 9x Blood Claw
     ◦ 9x Bolt pistol
```

### Step 6.2: Generate Catalogue

```bash
# Find BattleScribe catalogue
python3 wh40k_parser.py ~/.local/share/BattleScribe/data/Warhammer\ 40,000\ 10th\ Edition/Imperium\ -\ Space\ Marines.cat catalogues/space_wolves.yaml
```

### Step 6.3: Generate Cheat Sheet

```bash
python3 generate_cheat_sheet.py examples/test_army.txt catalogues/space_wolves.yaml -o test_output.html
```

### Step 6.4: Debug and Refine

Common issues to fix:
1. Unit names not matching
2. Weapon profiles missing
3. Abilities not organizing correctly
4. Page breaks in wrong places
5. CSS styling issues

## Phase 7: Documentation

### Step 7.1: Create README.md

Write comprehensive README covering:
- Features
- Installation
- Usage examples
- Troubleshooting

### Step 7.2: Create .gitignore

```
# Generated output
output/
*.pyc
__pycache__/
.DS_Store

# Generated cheat sheets (except examples)
*.html
*.md
!examples/**/*.html
!examples/**/*.md
!README.md
```

## Phase 8: Polish and Release

### Step 8.1: Add Examples

Generate example outputs for documentation:

```bash
python3 generate_cheat_sheet.py examples/space_wolves_example.txt catalogues/space_wolves.yaml -o examples/space_wolves_example.html
python3 generate_cheat_sheet.py examples/space_wolves_example.txt catalogues/space_wolves.yaml -o examples/space_wolves_example.md -f markdown
```

### Step 8.2: Create Web Server (Optional)

```python
#!/usr/bin/env python3
"""
Simple web server to preview HTML cheat sheets
"""

import http.server
import socketserver

PORT = 8000

Handler = http.server.SimpleHTTPRequestHandler

with socketserver.TCPServer(("", PORT), Handler) as httpd:
    print(f"Server running at http://localhost:{PORT}/")
    print("Press Ctrl+C to stop")
    httpd.serve_forever()
```

### Step 8.3: Final Testing

Test with multiple armies:
- Space Marines variants
- Death Guard
- Other factions

Verify:
- All stats accurate vs codex
- Faction abilities correct
- Page breaks logical
- Print quality good

## Completion Checklist

- [ ] Army list parser handles all BattleScribe formats
- [ ] Catalogue parser extracts all unit data
- [ ] Faction ability detection works correctly
- [ ] Page grouping optimizes printing
- [ ] HTML output is styled and printable
- [ ] Markdown output is readable
- [ ] Enhancements display correctly
- [ ] Multi-model units format properly
- [ ] CLI provides clear feedback
- [ ] Examples are included
- [ ] Documentation is complete
- [ ] Code is tested with multiple armies

## Common Pitfalls to Avoid

1. **Don't hardcode faction logic** - Use pattern matching and thresholds
2. **Handle missing data gracefully** - Print warnings, don't crash
3. **Test with edge cases** - Complex vehicles, multi-model units, epic heroes
4. **Preserve exact stat values** - Don't transform or interpret game rules
5. **Keep CSS print-friendly** - Test actual printing, not just browser preview
6. **Document assumptions** - Explain why certain design decisions were made

## Next Steps After V1

Once basic implementation is complete:

1. **Add more catalogues** - Generate for all major factions
2. **Enhancement database** - Create YAML files for enhancement descriptions
3. **Improve formatting** - Refine CSS, add themes
4. **Add tests** - Unit tests for parsers
5. **Optimize performance** - Cache catalogue data, parallel processing
6. **Community feedback** - Get input from players, iterate

---

**End of Implementation Guide**
