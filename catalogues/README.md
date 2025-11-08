# Faction Catalogues

This directory contains YAML catalogue files generated from BattleScribe's XML catalogue files. Each catalogue contains complete datasheet information for a faction.

## Available Catalogues

- **space_wolves.yaml** - Space Marines / Space Wolves faction
- **death_guard.yaml** - Death Guard faction

## What's in a Catalogue File?

Each catalogue YAML contains:
- **Units**: All datasheets with stats (M, T, SV, W, LD, OC)
- **Weapons**: Ranged and melee weapon profiles
- **Abilities**: Unit abilities with descriptions and phases
- **Keywords**: Unit keywords
- **Shared Rules**: Common abilities referenced by multiple units

## Generating New Catalogues

### Step 1: Locate BattleScribe Catalogue Files

BattleScribe catalogue files (`.cat` extension) are typically located at:

**Windows:**
```
C:\Users\<YourName>\AppData\Roaming\BattleScribe\data\<Game System>\
```

**Mac:**
```
~/Library/Application Support/BattleScribe/data/<Game System>/
```

**Linux:**
```
~/.local/share/BattleScribe/data/<Game System>/
```

For Warhammer 40k 10th Edition:
```
.../data/Warhammer 40,000 10th Edition/
```

### Step 2: Generate YAML Catalogue

From the repository root directory:

```bash
python3 wh40k_parser.py /path/to/faction.cat catalogues/faction_name.yaml
```

**Examples:**

```bash
# Generate Space Marines catalogue
python3 wh40k_parser.py ~/.local/share/BattleScribe/data/Warhammer\ 40,000\ 10th\ Edition/Imperium\ -\ Space\ Marines.cat catalogues/space_marines.yaml

# Generate Tyranids catalogue
python3 wh40k_parser.py ~/.local/share/BattleScribe/data/Warhammer\ 40,000\ 10th\ Edition/Tyranids.cat catalogues/tyranids.yaml

# Generate Orks catalogue
python3 wh40k_parser.py ~/.local/share/BattleScribe/data/Warhammer\ 40,000\ 10th\ Edition/Orks.cat catalogues/orks.yaml
```

### Step 3: Verify the Catalogue

After generation, test the catalogue with an army list:

```bash
python3 generate_cheat_sheet.py examples/test_army.txt catalogues/faction_name.yaml -o test_output.html
```

Open the HTML file and verify:
- All units are found
- Stats are correct
- Weapons have complete profiles
- Abilities have descriptions

## Common Issues

### Issue: "Unit not found in catalogue"

**Cause**: Unit name in the army list doesn't match the catalogue

**Solutions**:
1. Check for extra spaces or characters in the unit name
2. Verify you're using the correct faction catalogue
3. Ensure the catalogue was generated from the same BattleScribe version as your army list
4. Some units may be in parent catalogues (e.g., Space Wolves units may need the Space Marines catalogue)

### Issue: Missing weapon profiles

**Cause**: Weapons not included in the BattleScribe catalogue or referenced from a different file

**Solutions**:
1. Regenerate the catalogue from the latest BattleScribe data
2. Check if weapons are defined in a parent catalogue file
3. Some weapons may be in the "Imperium - Space Marines" catalogue even for subfactions

### Issue: Abilities missing descriptions

**Cause**: Abilities defined as shared rules in separate files

**Solutions**:
- BattleScribe uses multiple linked files. The main faction catalogue may reference shared rules from:
  - `Imperium.cat` (for Imperial factions)
  - `Chaos.cat` (for Chaos factions)
  - Game system catalogues

Currently, the parser only reads the single `.cat` file provided. Future enhancement: support for parsing linked catalogues.

## Catalogue File Format

The YAML format structure:

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
    abilities:
      - name: "Ability Name"
        description: "Full description"
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

## Updating Catalogues

When BattleScribe releases new updates:

1. Update BattleScribe data through the app
2. Regenerate the catalogue using the parser
3. Test with army lists to verify changes
4. Replace the old catalogue file

## Tips

- **Naming**: Use lowercase with underscores for catalogue filenames (e.g., `space_wolves.yaml`, `tau_empire.yaml`)
- **Size**: Catalogue files can be large (500KB+) - this is normal as they contain complete faction data
- **Versions**: Keep catalogue files updated with your BattleScribe version
- **Subfactions**: Some subfactions (like Space Wolves) may require the parent faction catalogue (Space Marines)

## Contributing Catalogues

If you generate catalogues for additional factions, consider sharing them! Just ensure they're generated from official BattleScribe data files.

### Needed Catalogues

Common factions that would benefit from catalogue generation:
- Aeldari (Craftworlds)
- Drukhari
- Necrons
- Orks
- Tau Empire
- Tyranids
- Imperial Guard (Astra Militarum)
- Adeptus Custodes
- Grey Knights
- Thousand Sons
- World Eaters

---

**Note**: BattleScribe catalogue files are maintained by the BattleScribe community and contain all the official datasheet information from Games Workshop's codexes.
