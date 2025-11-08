# Technical Specification: Warhammer 40k Cheat Sheet Generator

## Document Information
- **Version**: 1.0
- **Last Updated**: November 8, 2024
- **Related**: PRODUCT_REQUIREMENTS.md

## System Architecture

### Overview

```
┌─────────────────────┐
│   User Input        │
│  (Army List .txt)   │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Army List Parser   │
│ (army_list_parser)  │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐      ┌──────────────────┐
│  Cheat Sheet        │◄─────│  Catalogue YAML  │
│  Generator          │      │  (faction data)  │
│ (cheat_sheet_gen)   │      └──────────────────┘
└──────────┬──────────┘
           │
           ▼
     ┌─────┴─────┐
     │           │
     ▼           ▼
┌─────────┐  ┌────────────┐
│  HTML   │  │  Markdown  │
│ Output  │  │   Output   │
└─────────┘  └────────────┘
```

### Component Breakdown

#### 1. CLI Entry Point (`generate_cheat_sheet.py`)
- **Purpose**: Command-line interface
- **Responsibilities**:
  - Parse command-line arguments
  - Validate input files exist
  - Instantiate parser and generator
  - Write output to disk
  - Display success/error messages

#### 2. Army List Parser (`army_list_parser.py`)
- **Purpose**: Parse BattleScribe text exports
- **Input**: Plain text army list
- **Output**: Python dictionary with structured army data
- **Responsibilities**:
  - Identify army metadata (name, points, faction, detachment)
  - Parse section headers (CHARACTERS, BATTLELINE, etc.)
  - Extract unit entries with points
  - Parse wargear items (• bullet format)
  - Parse nested weapons (◦ diamond format)
  - Detect warlord markers
  - Extract enhancements
  - Handle model count notation (e.g., "9x Blood Claw")

#### 3. Cheat Sheet Generator (`cheat_sheet_generator.py`)
- **Purpose**: Main processing and output generation
- **Input**: Parsed army data + catalogue YAML
- **Output**: Formatted HTML or Markdown
- **Responsibilities**:
  - Load and cache catalogue data
  - Enrich units with catalogue information
  - Detect faction abilities
  - Filter duplicate abilities
  - Organize abilities by phase
  - Calculate page complexity
  - Assign page breaks
  - Format output in HTML or Markdown

#### 4. Catalogue Parser (`wh40k_parser.py`)
- **Purpose**: Convert BattleScribe XML to YAML
- **Input**: BattleScribe `.cat` XML file
- **Output**: Structured YAML catalogue
- **Responsibilities**:
  - Parse XML tree structure
  - Extract unit datasheets
  - Extract weapon profiles
  - Extract abilities and rules
  - Resolve infoLinks to shared rules
  - Generate YAML output

#### 5. Web Server (`server.py`)
- **Purpose**: Preview HTML output
- **Responsibilities**:
  - Serve static files on localhost:8000
  - Enable quick HTML preview in browser

## Data Models

### Army List Data Structure

```python
{
    'name': str,              # Army name
    'points': int,            # Total points
    'faction': str,           # Main faction (e.g., "Space Marines")
    'detachment': str,        # Detachment name
    'characters': [           # List of character units
        {
            'name': str,      # Unit name
            'points': int,    # Points cost
            'warlord': bool,  # True if warlord
            'enhancements': [str],  # List of enhancement names
            'models': [       # Model entries (for multi-model units)
                {
                    'name': str,      # Model name
                    'count': int,     # Number of models
                    'weapons': [      # Nested weapons
                        {
                            'name': str,
                            'count': int
                        }
                    ]
                }
            ],
            'wargear': [      # Direct wargear items
                {
                    'name': str,
                    'count': int
                }
            ]
        }
    ],
    'battleline': [...],      # Same structure as characters
    'other_units': [...]      # Same structure as characters
}
```

### Enriched Unit Data Structure

```python
{
    'name': str,
    'points': int,
    'warlord': bool,
    'enhancements': [str],
    'stats': {
        'M': str,   # Movement (e.g., "6\"")
        'T': str,   # Toughness
        'SV': str,  # Save
        'W': str,   # Wounds
        'LD': str,  # Leadership
        'OC': str   # Objective Control
    },
    'keywords': [str],
    'faction': str,
    'weapons': {
        'ranged': [
            {
                'name': str,
                'range': str,
                'attacks': str,
                'skill': str,     # BS (Ballistic Skill)
                'strength': str,
                'ap': str,        # Armor Penetration
                'damage': str,
                'keywords': [str] # Weapon abilities
            }
        ],
        'melee': [
            {
                'name': str,
                'range': str,     # "Melee"
                'attacks': str,
                'skill': str,     # WS (Weapon Skill)
                'strength': str,
                'ap': str,
                'damage': str,
                'keywords': [str]
            }
        ]
    },
    'abilities_by_phase': {
        'Command Phase': [
            {
                'name': str,
                'description': str,
                'phase': str,
                'is_shared_rule': bool,
                'rule_id': str    # For deduplication
            }
        ],
        'Movement Phase': [...],
        'Shooting Phase': [...],
        'Charge Phase': [...],
        'Fight Phase': [...],
        'Any Phase': [...]
    },
    'passive_abilities': [
        {
            'name': str,
            'description': str,
            'is_shared_rule': bool,
            'rule_id': str
        }
    ],
    'selected_models': [      # For multi-model units
        {
            'name': str,
            'count': int,
            'weapons': [
                {
                    'name': str,
                    'count': int,
                    'profile': {...}  # Full weapon profile
                }
            ]
        }
    ]
}
```

### Catalogue YAML Structure

```yaml
units:
  - name: "Unit Name"
    stats:
      M: "6\""
      T: "4"
      SV: "3+"
      W: "2"
      LD: "6+"
      OC: "1"
    keywords: ["Keyword1", "Keyword2"]
    faction: "Faction Name"
    abilities:
      - name: "Ability Name"
        description: "Full description text"
        phase: "Command Phase"
        is_shared_rule: true
        rule_id: "unique_id"
    weapons:
      ranged:
        - name: "Bolter"
          range: "24\""
          attacks: "2"
          skill: "3+"
          strength: "4"
          ap: "0"
          damage: "1"
          keywords: ["Rapid Fire 2"]
      melee:
        - name: "Close Combat Weapon"
          range: "Melee"
          attacks: "1"
          skill: "3+"
          strength: "4"
          ap: "0"
          damage: "1"
          keywords: []

shared_rules:
  unique_id:
    name: "Leader"
    description: "This model can lead units..."
    phase: "Any Phase"
```

## Algorithm Specifications

### Algorithm 1: Army List Parsing

**File**: `army_list_parser.py`
**Function**: `ArmyListParser.parse()`

```python
# High-level pseudocode
def parse():
    army = initialize_army_structure()
    current_section = None
    current_unit = None

    for each line in army_list:
        # Skip empty lines
        if line.is_empty():
            continue

        # Parse army header (first line)
        if is_army_header(line):
            extract_army_name_and_points(line)
            continue

        # Parse section headers
        if is_section_header(line):
            save_current_unit()
            current_section = identify_section(line)
            continue

        # Parse unit entry (has points cost)
        if has_points_notation(line):
            save_current_unit()
            current_unit = parse_unit_header(line)
            continue

        # Parse warlord marker
        if is_warlord_marker(line):
            current_unit.warlord = True
            continue

        # Parse enhancements
        if is_enhancement_line(line):
            extract_enhancement(line, current_unit)
            continue

        # Parse wargear (• bullet)
        if is_wargear_bullet(line):
            parse_wargear_item(line, current_unit)
            continue

        # Parse nested weapon (◦ diamond)
        if is_nested_weapon(line):
            add_weapon_to_last_model(line, current_unit)
            continue

    save_current_unit()
    return army
```

**Key Functions**:

1. **parse_unit_header(line)**
   ```python
   # Regex: ^(.+?)\s*\((\d+)\s+Points\)
   # Example: "Logan Grimnar (110 Points)"
   match = regex_match(line)
   return {
       'name': match.group(1).strip(),
       'points': int(match.group(2)),
       'models': [],
       'wargear': []
   }
   ```

2. **parse_wargear_item(line, unit)**
   ```python
   # Line: "  • 1x Axe Morkai"
   item = line.strip_bullet()

   # Check for count notation (e.g., "1x", "9x")
   model_match = regex_match(r'^(\d+)x\s+(.+)', item)

   if model_match:
       count = int(model_match.group(1))
       name = model_match.group(2))

       # Determine if it's a model or weapon
       if has_nested_weapons_below() or looks_like_model(name):
           add_to_models(unit, name, count)
       else:
           add_to_wargear(unit, name, count)
   else:
       # No count, treat as single wargear item
       add_to_wargear(unit, item, 1)
   ```

3. **looks_like_weapon(name)**
   ```python
   # Model name patterns (return False)
   model_patterns = [
       'pack leader', 'sergeant', 'marine', 'terminator',
       'warrior', 'trooper', ...
   ]

   # Weapon keywords (return True)
   weapon_keywords = [
       'pistol', 'bolter', 'gun', 'rifle', 'sword', 'axe',
       'hammer', 'launcher', 'cannon', ...
   ]

   name_lower = name.lower()

   # Check model patterns first
   for pattern in model_patterns:
       if pattern in name_lower:
           return False

   # Check weapon keywords
   for keyword in weapon_keywords:
       if keyword in name_lower:
           return True

   return False  # Default to not a weapon
   ```

### Algorithm 2: Faction Ability Detection

**File**: `cheat_sheet_generator.py`
**Function**: `_extract_faction_abilities()`

```python
def extract_faction_abilities(cheat_sheet):
    all_units = cheat_sheet.characters + cheat_sheet.units
    total_units = len(all_units)
    ability_counts = {}  # rule_id -> (ability_data, count)

    # Step 1: Scan all units and count abilities
    for unit in all_units:
        # Check regular abilities
        for phase, abilities in unit.abilities_by_phase.items():
            for ability in abilities:
                if ability.is_shared_rule:
                    if is_faction_ability_by_description(ability):
                        rule_id = ability.rule_id
                        if rule_id not in ability_counts:
                            ability_counts[rule_id] = (ability, 0)
                        ability_counts[rule_id][1] += 1

        # Check passive abilities
        for ability in unit.passive_abilities:
            if ability.is_shared_rule:
                if is_faction_ability_by_description(ability):
                    rule_id = ability.rule_id
                    if rule_id not in ability_counts:
                        ability_counts[rule_id] = (ability, 0)
                    ability_counts[rule_id][1] += 1

    # Step 2: Store ALL faction-like abilities for filtering
    # (Even if they don't meet threshold, filter from units)
    for rule_id in ability_counts.keys():
        self.faction_ability_rule_ids.add(rule_id)

    # Step 3: Apply frequency threshold for display
    threshold = max(1, total_units * 0.5)  # 50% of units
    faction_abilities = []

    for rule_id, (ability, count) in ability_counts.items():
        if count >= threshold:
            faction_abilities.append(ability)

    return faction_abilities

def is_faction_ability_by_description(ability):
    description = ability.description.lower()
    return 'if your army faction is' in description
```

**Why This Works**:
- **Pattern Matching**: True faction abilities always say "If your Army Faction is [FACTION]"
- **Frequency Threshold**: True faction abilities appear on most units (50%+)
- **Filtering**: All faction-like abilities are removed from individual units
- **Example Results**:
  - "Oath of Moment" appears on 12/14 units (86%) → SHOW as faction ability
  - "Templar Vows" appears on 1/14 units (7%) → HIDE (detachment-specific)

### Algorithm 3: Page Complexity Calculation

**File**: `cheat_sheet_generator.py`
**Function**: `_calculate_unit_complexity()`

```python
def calculate_unit_complexity(unit):
    score = 0

    # Base cost for any unit
    score += 5

    # Weapons complexity
    ranged_weapons = len(unit.weapons.ranged)
    melee_weapons = len(unit.weapons.melee)
    score += ranged_weapons * 2
    score += melee_weapons * 2

    # Abilities complexity (exclude faction abilities)
    for phase_abilities in unit.abilities_by_phase.values():
        unit_only_abilities = [
            a for a in phase_abilities
            if not is_faction_ability(a)
        ]
        score += len(unit_only_abilities) * 3

    # Passive abilities
    score += len(unit.passive_abilities) * 1

    # Multi-model units are more complex
    if len(unit.selected_models) > 1:
        score += len(unit.selected_models) * 4

    return score
```

**Classification**:
```python
if score < 20:
    return 'simple'    # ~25% page capacity
elif score < 35:
    return 'medium'    # ~50% page capacity
else:
    return 'complex'   # 100% page capacity
```

**Example Calculations**:

| Unit Type | Base | Weapons | Abilities | Models | Total | Class |
|-----------|------|---------|-----------|--------|-------|-------|
| Character | 5 | 4 (2 weapons) | 9 (3 abilities) | 0 | 18 | Simple |
| Tactical Squad | 5 | 8 (4 weapons) | 6 (2 abilities) | 8 (2 models) | 27 | Medium |
| Tank | 5 | 16 (8 weapons) | 18 (6 abilities) | 0 | 39 | Complex |

### Algorithm 4: Page Break Assignment

**File**: `cheat_sheet_generator.py`
**Function**: `_assign_page_groups()`

```python
def assign_page_groups(units):
    page_breaks = [''] * len(units)
    page_capacity = 0  # Track current page usage (0-100%)

    for i, unit in enumerate(units):
        # Calculate unit size
        complexity = calculate_unit_complexity(unit)

        if complexity == 'simple':
            unit_size = 25
        elif complexity == 'medium':
            unit_size = 50
        else:  # complex
            unit_size = 100

        # Check if unit fits on current page
        if page_capacity + unit_size > 100 and page_capacity > 0:
            # Page full, start new page
            page_breaks[i] = 'page-break-before'
            page_capacity = unit_size
        else:
            # Fits on current page
            page_capacity += unit_size

        # Reset capacity if page is full
        if page_capacity >= 100:
            page_capacity = 0

    return page_breaks
```

**Example**:
```
Page 1:
- Character A (simple, 25%)
- Character B (simple, 25%)
- Character C (simple, 25%)
Total: 75%

Page 2:
- Unit A (medium, 50%)
- Unit B (simple, 25%)
Total: 75%

Page 3:
- Unit C (medium, 50%)
← Page break before next unit
- Vehicle A (complex, 100%)

Page 4:
- Vehicle A continues
```

### Algorithm 5: Weapon Matching

**File**: `cheat_sheet_generator.py`
**Function**: `_find_weapon_profile()`

```python
def find_weapon_profile(weapon_name, unit_weapons):
    # Normalize weapon name for matching
    search_name = weapon_name.lower().strip()

    # Try exact match first
    for weapon in unit_weapons:
        if weapon.name.lower() == search_name:
            return weapon

    # Try partial match (handle variations)
    # E.g., "Power weapon" matches "Master-crafted power weapon"
    for weapon in unit_weapons:
        weapon_lower = weapon.name.lower()

        # Check if search_name is contained in weapon name
        if search_name in weapon_lower:
            return weapon

        # Check if weapon name is contained in search_name
        if weapon_lower in search_name:
            return weapon

    # No match found
    return None
```

**Edge Cases Handled**:
- "power weapon" → "Master-crafted power weapon"
- "bolt pistol" → "Bolt Pistol" (case insensitive)
- "Storm bolter" → "Storm Bolter" (spacing variations)

### Algorithm 6: Ability Organization

**File**: `cheat_sheet_generator.py`
**Function**: `_organize_abilities_by_phase()`

```python
def organize_abilities_by_phase(abilities):
    phases = {
        'Command Phase': [],
        'Movement Phase': [],
        'Shooting Phase': [],
        'Charge Phase': [],
        'Fight Phase': [],
        'Any Phase': []
    }

    passive_abilities = []

    for ability in abilities:
        # Skip faction abilities (shown separately)
        if is_faction_ability(ability):
            continue

        # Passive abilities (no phase, or always-on)
        if is_passive_ability(ability):
            passive_abilities.append(ability)
            continue

        # Categorize by phase
        phase = ability.phase or 'Any Phase'
        if phase in phases:
            phases[phase].append(ability)
        else:
            phases['Any Phase'].append(ability)

    return phases, passive_abilities

def is_passive_ability(ability):
    # Check ability name patterns
    passive_names = [
        'Leader', 'Deep Strike', 'Scouts', 'Infiltrators',
        'Invulnerable Save', 'Feel No Pain', 'Stealth',
        'Lone Operative', ...
    ]

    for name in passive_names:
        if name.lower() in ability.name.lower():
            return True

    # Check if description has no phase-specific trigger
    description = ability.description.lower()
    phase_triggers = [
        'command phase', 'movement phase', 'shooting phase',
        'charge phase', 'fight phase', 'at the start of',
        'at the end of', 'each time'
    ]

    for trigger in phase_triggers:
        if trigger in description:
            return False  # Has phase-specific trigger

    return True  # No phase triggers = passive
```

## Implementation Details

### File: `army_list_parser.py`

**Class**: `ArmyListParser`

```python
class ArmyListParser:
    def __init__(self, text: str):
        self.text = text
        self.lines = [line.rstrip() for line in text.split('\n')]

    def parse(self) -> Dict[str, Any]:
        """Main parsing function"""
        # Returns army dictionary structure

    def _looks_like_weapon(self, name: str) -> bool:
        """Heuristic to distinguish weapons from models"""

    def _add_unit_to_section(self, army: Dict, section: str, unit: Dict):
        """Add parsed unit to appropriate section"""
```

**Key Patterns**:
- Army header: `^(.+?)\s*\((\d+)\s+Points\)`
- Unit entry: `^(.+?)\s*\((\d+)\s+Points\)`
- Model count: `^(\d+)x\s+(.+)`
- Wargear bullet: `^\s\s•`
- Nested weapon: `^\s\s\s\s\s◦`

### File: `cheat_sheet_generator.py`

**Class**: `CheatSheetGenerator`

```python
class CheatSheetGenerator:
    def __init__(self, catalogue_yaml: str):
        """Load catalogue data"""
        self.catalogue = yaml.safe_load(open(catalogue_yaml))
        self.faction_ability_rule_ids = set()

    def generate(self, army: Dict, format: str = 'html') -> str:
        """Main generation function"""
        # 1. Enrich units with catalogue data
        # 2. Extract faction abilities
        # 3. Format output

    def _enrich_unit(self, unit: Dict) -> Dict:
        """Look up unit in catalogue and enrich with full data"""

    def _extract_faction_abilities(self, cheat_sheet: Dict) -> List:
        """Identify army-wide faction abilities"""

    def _calculate_unit_complexity(self, unit: Dict) -> int:
        """Calculate complexity score for page grouping"""

    def _assign_page_groups(self, units: List) -> List[str]:
        """Assign page break classes"""

    def _format_html(self, cheat_sheet: Dict) -> str:
        """Generate HTML output"""

    def _format_markdown(self, cheat_sheet: Dict) -> str:
        """Generate Markdown output"""
```

**Important Methods**:

1. **find_unit(name)**
   ```python
   def find_unit(self, name: str) -> Optional[Dict]:
       for unit in self.catalogue['units']:
           if unit['name'].lower() == name.lower():
               return unit
       return None
   ```

2. **_enrich_unit(unit)**
   ```python
   def _enrich_unit(self, unit: Dict) -> Dict:
       catalogue_unit = self.find_unit(unit['name'])
       if not catalogue_unit:
           raise ValueError(f"Unit not found: {unit['name']}")

       enriched = {
           'name': unit['name'],
           'points': unit['points'],
           'warlord': unit.get('warlord', False),
           'enhancements': unit.get('enhancements', []),
           'stats': catalogue_unit['stats'],
           'keywords': catalogue_unit['keywords'],
           'faction': catalogue_unit.get('faction', ''),
           'weapons': catalogue_unit['weapons'],
           'abilities_by_phase': {},
           'passive_abilities': []
       }

       # Organize abilities by phase
       phases, passives = self._organize_abilities_by_phase(
           catalogue_unit['abilities']
       )
       enriched['abilities_by_phase'] = phases
       enriched['passive_abilities'] = passives

       # Handle multi-model units
       if unit.get('models'):
           enriched['selected_models'] = self._enrich_models(
               unit['models'], catalogue_unit['weapons']
           )

       return enriched
   ```

### File: `wh40k_parser.py`

**Main Function**: `parse_battlescribe_catalogue()`

```python
def parse_battlescribe_catalogue(cat_file: str) -> Dict:
    tree = ET.parse(cat_file)
    root = tree.getroot()

    catalogue = {
        'units': [],
        'shared_rules': {}
    }

    # Find all unit entries
    for entry in root.findall(".//selectionEntry[@type='unit']"):
        unit = parse_unit_entry(entry)
        if unit:
            catalogue['units'].append(unit)

    # Extract shared rules
    for rule in root.findall(".//rule"):
        rule_id = rule.get('id')
        catalogue['shared_rules'][rule_id] = parse_rule(rule)

    return catalogue

def parse_unit_entry(entry: ET.Element) -> Optional[Dict]:
    unit = {
        'name': entry.get('name'),
        'stats': {},
        'keywords': [],
        'abilities': [],
        'weapons': {'ranged': [], 'melee': []}
    }

    # Extract profiles
    for profile in entry.findall(".//profile"):
        type_name = profile.get('typeName')

        if type_name == 'Unit':
            unit['stats'] = parse_stats_profile(profile)
        elif 'Weapon' in type_name:
            weapon = parse_weapon_profile(profile)
            if weapon:
                category = 'ranged' if 'Ranged' in type_name else 'melee'
                unit['weapons'][category].append(weapon)

    # Extract abilities
    for rule in entry.findall(".//rule"):
        ability = parse_rule(rule)
        if ability:
            unit['abilities'].append(ability)

    return unit
```

## CSS Styling

### Color Scheme

```css
/* Section Colors */
.keywords-section {
    background: #f0f4ff;        /* Light blue */
    border-left: 4px solid #667eea;  /* Blue */
}

.passive-abilities-section {
    background: #fff4e6;        /* Light orange */
    border-left: 4px solid #ff9800;  /* Orange */
}

.enhancements-section {
    background: #f3e5f5;        /* Light purple */
    border-left: 4px solid #9c27b0;  /* Purple */
}

/* Weapon Tables */
.weapon-table {
    border: 1px solid #ddd;
    background: #f9f9f9;
}

/* Phase Headers */
.phase-header {
    color: #2c3e50;
    font-size: 16px;
    font-weight: bold;
}
```

### Print Styles

```css
@media print {
    /* Hide UI elements */
    .no-print { display: none; }

    /* Optimize fonts */
    body { font-size: 11px; }
    .ability-compact { font-size: 10px; }

    /* Page breaks */
    .page-break-before { page-break-before: always; }
    .faction-abilities-section { page-break-after: always; }

    /* Ensure tables don't break */
    table { page-break-inside: avoid; }
}
```

## Error Handling

### Common Errors

1. **Unit Not Found**
   ```python
   raise ValueError(f"Unit '{unit_name}' not found in catalogue. "
                   f"Check spelling or regenerate catalogue.")
   ```

2. **Weapon Not Found**
   ```python
   # Log warning but continue
   print(f"Warning: Weapon '{weapon_name}' not found for {unit_name}")
   # Show weapon name without profile
   ```

3. **Invalid Army List Format**
   ```python
   raise ValueError(f"Could not parse army list. "
                   f"Ensure it's a valid BattleScribe text export.")
   ```

4. **Catalogue Load Error**
   ```python
   raise FileNotFoundError(f"Catalogue file '{path}' not found. "
                          f"Generate with: python3 wh40k_parser.py ...")
   ```

## Performance Considerations

### Optimization Strategies

1. **Catalogue Caching**: Load catalogue once, reuse for multiple generations
2. **Lazy Evaluation**: Only enrich units that are in the army list
3. **Efficient Lookups**: Use dictionaries for O(1) lookups where possible
4. **Minimal Regex**: Cache compiled regex patterns

### Expected Performance

- Parse army list: 0.1-0.5 seconds
- Load catalogue: 1-2 seconds (large YAML files)
- Generate output: 0.5-1 second
- **Total**: <3 seconds for typical 2000pt army

## Testing Strategy

### Unit Tests

```python
# Test army list parser
def test_parse_unit_header():
    line = "Logan Grimnar (110 Points)"
    result = parser.parse_unit_header(line)
    assert result['name'] == "Logan Grimnar"
    assert result['points'] == 110

def test_parse_wargear():
    line = "  • 1x Axe Morkai"
    result = parser.parse_wargear(line)
    assert result['name'] == "Axe Morkai"
    assert result['count'] == 1

# Test faction ability detection
def test_faction_ability_detection():
    abilities = [
        {'name': 'Oath of Moment', 'description': 'If your Army Faction is...'},
        {'name': 'Invulnerable Save', 'description': 'This model has...'}
    ]
    result = generator.is_faction_ability(abilities[0])
    assert result == True
    result = generator.is_faction_ability(abilities[1])
    assert result == False
```

### Integration Tests

1. Generate cheat sheet for Space Wolves example
2. Generate cheat sheet for Death Guard example
3. Verify output contains all expected sections
4. Verify faction abilities are correct
5. Verify page breaks are assigned

### Validation

- Compare generated stats to official codex
- Verify weapon profiles match codex
- Check ability descriptions are complete
- Ensure page breaks make sense visually

## Deployment

### Package Structure

```
warhammer-cheatsheet/
├── cheat_sheet_generator.py
├── army_list_parser.py
├── wh40k_parser.py
├── generate_cheat_sheet.py
├── server.py
├── catalogues/
├── examples/
├── docs/
├── README.md
└── .gitignore
```

### Installation

```bash
# Clone repository
git clone <repo-url>
cd warhammer-cheatsheet

# Install dependencies
pip install pyyaml

# Run
python3 generate_cheat_sheet.py examples/space_wolves_example.txt catalogues/space_wolves.yaml
```

### Distribution

- GitHub repository (public or private)
- No build process required (pure Python)
- Cross-platform (Windows, Mac, Linux)
- No external services or API keys needed

## Future Technical Improvements

1. **Multi-Catalogue Support**: Parse linked catalogue files automatically
2. **Parallel Processing**: Generate multiple armies concurrently
3. **Template System**: User-customizable HTML templates
4. **Database Backend**: SQLite for faster lookups on large catalogues
5. **API Mode**: Run as web service for online generation
6. **PDF Generation**: Direct PDF export using reportlab
7. **Incremental Updates**: Update catalogues without full regeneration
8. **Unit Tests**: Comprehensive test suite with pytest
9. **CI/CD**: Automated testing and releases
10. **Logging**: Structured logging for debugging

---

**End of Technical Specification**
