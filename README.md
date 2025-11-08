# Warhammer 40k Cheat Sheet Generator

A Python tool that converts BattleScribe army list exports into clean, printable cheat sheets for tabletop gaming. Automatically extracts unit stats, weapons, abilities, and faction rules to create reference sheets optimized for quick gameplay.

## Features

- **Parse BattleScribe Army Lists**: Import text-based army list exports
- **Automatic Faction Ability Detection**: Identifies and displays army-wide faction abilities
- **Smart Page Grouping**: Optimizes printing on US Letter paper by intelligently grouping units
- **Multiple Output Formats**: Generate both Markdown (.md) and HTML (.html) cheat sheets
- **Comprehensive Unit Information**:
  - Stats (M, T, SV, W, LD, OC)
  - Weapons (Ranged and Melee)
  - Abilities organized by phase
  - Keywords and passive abilities
  - Character enhancements
  - Warlord markers
- **Print-Optimized HTML**: Built-in print styles with page breaks for clean printing
- **Multi-Model Unit Support**: Handles units with different model types and weapon loadouts

## Quick Start

### 1. Generate a Cheat Sheet

```bash
# Basic usage
python3 generate_cheat_sheet.py army_list.txt catalogues/space_wolves.yaml -o output.html

# Generate both HTML and Markdown
python3 generate_cheat_sheet.py army_list.txt catalogues/space_wolves.yaml -o output.html -f html
python3 generate_cheat_sheet.py army_list.txt catalogues/space_wolves.yaml -o output.md -f markdown
```

### 2. Preview HTML Output

```bash
python3 server.py
# Then open http://localhost:8000 in your browser
```

## Installation

### Prerequisites

- Python 3.7+
- PyYAML

```bash
pip install pyyaml
```

### Setup

```bash
# Clone or download this repository
cd warhammer-cheatsheet

# You're ready to go!
python3 generate_cheat_sheet.py --help
```

## Usage

### Command Line Arguments

```bash
python3 generate_cheat_sheet.py <army_list_file> <catalogue_file> [options]

Required:
  army_list_file    Path to BattleScribe army list text export
  catalogue_file    Path to faction catalogue YAML file

Options:
  -o, --output      Output file path (default: cheat_sheet.html)
  -f, --format      Output format: 'html' or 'markdown' (default: html)
```

### Creating Army Lists

1. **In BattleScribe**:
   - Build your army list
   - Go to File → Export → Text (or use Share → Copy as Text)
   - Save as a `.txt` file

2. **Required Format**:
   The army list should follow BattleScribe's text export format with sections like:
   ```
   Army Name (Points)

   Faction Name
   Detachment Name
   Strike Force (X,XXX Points)

   CHARACTERS

   Unit Name (Points)
     • Wargear items
     • Enhancements: Name

   BATTLELINE

   ...
   ```

### Example

```bash
# Generate Space Wolves cheat sheet
python3 generate_cheat_sheet.py examples/space_wolves_example.txt catalogues/space_wolves.yaml -o my_army.html

# Generate Death Guard cheat sheet in Markdown
python3 generate_cheat_sheet.py examples/death_guard_example.txt catalogues/death_guard.yaml -o my_army.md -f markdown
```

## Catalogue Files

Catalogue files contain the complete faction datasheet information (units, weapons, abilities, etc.). They are generated from BattleScribe's `.cat` XML files.

### Available Catalogues

- `catalogues/space_wolves.yaml` - Space Marines / Space Wolves
- `catalogues/death_guard.yaml` - Death Guard

### Generating New Catalogues

```bash
python3 wh40k_parser.py path/to/faction.cat output_catalogue.yaml
```

See `catalogues/README.md` for detailed instructions on creating catalogues.

## Features Explained

### Faction Ability Detection

The generator automatically identifies faction-wide abilities by:
- Looking for abilities with "If your Army Faction is [FACTION]" in their description
- Requiring abilities to appear on 50%+ of units in the army
- Filtering out detachment-specific abilities

This ensures only true army-wide rules appear in the Faction Abilities section.

### Page Grouping for Printing

When generating HTML, units are intelligently grouped to optimize printing on US Letter paper:
- **Simple units** (<20 complexity): 3-4 per page
- **Medium units** (20-35 complexity): 2 per page
- **Complex units** (>35 complexity): 1 per page

Complexity is calculated based on:
- Number of weapons
- Number of abilities
- Multi-model units
- Passive abilities

### Enhancement Support

Character enhancements are displayed below the Keywords section:
```
**Keywords:** Character | Infantry | Imperium | Tacticus

**Enhancements:** Feral Rage

**Passive Abilities:** Leader
```

## Output Examples

### HTML Output
- Clean, professional styling
- Color-coded sections (blue for keywords, orange for passive abilities, purple for enhancements)
- Print button for easy printing
- Optimized page breaks
- Responsive design

### Markdown Output
- GitHub-flavored markdown
- Tables for stats and weapons
- Organized by phase
- Easy to read and edit

## File Structure

```
warhammer-cheatsheet/
├── cheat_sheet_generator.py    # Main generator logic
├── army_list_parser.py         # Parses army list text
├── wh40k_parser.py              # BattleScribe XML to YAML converter
├── generate_cheat_sheet.py     # CLI entry point
├── server.py                    # Simple web server
├── catalogues/                  # Faction data files
│   ├── space_wolves.yaml
│   ├── death_guard.yaml
│   └── README.md
├── examples/                    # Example army lists and outputs
│   ├── space_wolves_example.txt
│   ├── space_wolves_example.html
│   ├── death_guard_example.txt
│   └── death_guard_example.html
├── README.md
└── .gitignore
```

## How It Works

1. **Parse Army List**: `army_list_parser.py` reads the BattleScribe text export and extracts:
   - Army name, points, faction, detachment
   - All units with their wargear and models
   - Warlord and enhancement markers

2. **Enrich with Catalogue Data**: `cheat_sheet_generator.py` looks up each unit in the catalogue file to get:
   - Full stats
   - Weapon profiles (ranged and melee)
   - All abilities with descriptions
   - Keywords and special rules

3. **Process Abilities**: The generator:
   - Organizes abilities by phase
   - Identifies faction-wide abilities
   - Filters duplicates and redundant rules
   - Matches wargear to weapon profiles

4. **Generate Output**: Creates formatted output with:
   - Faction abilities section
   - Character and unit sections
   - Intelligent page breaks (HTML)
   - Print-optimized styling

## Tips & Best Practices

### For Best Results

- Use the latest BattleScribe catalogues when building army lists
- Export army lists as text, not HTML
- Generate HTML for printing, Markdown for viewing/editing
- Keep catalogue files updated with new datasheet releases

### Printing

1. Generate HTML output
2. Open in web browser
3. Click "Print Cheat Sheet" button
4. Recommended settings:
   - Paper: US Letter
   - Margins: Default or Minimal
   - Scale: 100%
   - Print backgrounds: Yes

## Troubleshooting

### "Unit not found in catalogue"

- Ensure you're using the correct catalogue for your faction
- Check if the unit name in the army list matches the catalogue exactly
- Regenerate the catalogue from the latest BattleScribe `.cat` file

### Abilities not showing correctly

- Verify the BattleScribe export includes ability descriptions
- Check that shared rules are properly defined in the catalogue
- Some abilities may be in the unit's stat block rather than the shared rules section

### Wrong faction abilities detected

The generator uses two criteria to identify faction abilities:
1. Description contains "If your Army Faction is [FACTION]"
2. Ability appears on 50%+ of units in the army

If an ability is incorrectly flagged, it's likely a detachment-specific ability that's in the catalogue but shouldn't apply to your army.

## Known Limitations

- Enhancements show name only (no descriptions) - descriptions are detachment-specific and not in BattleScribe catalogues
- Some special rules may not format perfectly if they use unusual BattleScribe markup
- Page breaks are optimized for US Letter paper; other sizes may need adjustment

## Future Enhancements

Potential features for future development:
- Enhancement description database
- Support for other paper sizes (A4, etc.)
- Interactive HTML with collapsible sections
- Quick reference cards (smaller format)
- PDF export
- Stratagem reference sheets

## Contributing

This is a personal project, but suggestions and improvements are welcome! Common areas for contribution:
- Additional faction catalogues
- Bug fixes for parsing edge cases
- Improved styling and layouts
- Support for other game systems

## License

This tool is for personal use. Warhammer 40,000 is a trademark of Games Workshop Ltd. This project is not affiliated with or endorsed by Games Workshop.

## Credits

Built to make tabletop gaming easier and reduce the need to constantly reference codexes during gameplay!

---

**Questions or Issues?** Check the examples directory for reference implementations, or examine the existing catalogue files for format guidance.
