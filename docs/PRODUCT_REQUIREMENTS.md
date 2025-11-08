# Product Requirements Document: Warhammer 40k Cheat Sheet Generator

## Document Information
- **Version**: 1.0
- **Last Updated**: November 8, 2024
- **Status**: Complete Implementation

## Executive Summary

A Python-based tool that automatically converts BattleScribe army list exports into clean, printable cheat sheets for Warhammer 40k tabletop gaming. The tool eliminates the need to reference codexes during gameplay by providing all necessary unit information in an optimized, easy-to-read format.

## Problem Statement

### Current Pain Points

1. **During Gameplay**: Players must constantly reference physical codexes or digital apps to check unit stats, weapons, and abilities
2. **Information Overload**: Codexes contain hundreds of units; players only need data for the 10-15 units in their army
3. **Slow Gameplay**: Looking up information interrupts game flow and increases game time
4. **Army Lists**: BattleScribe exports contain unit names and wargear but not the actual stats and ability descriptions
5. **Printing Issues**: No easy way to create print-optimized reference sheets from BattleScribe lists

### Target Users

- **Primary**: Warhammer 40k players who use BattleScribe for army building
- **Secondary**: Tournament organizers who need quick reference sheets
- **Tertiary**: New players learning the game and needing consolidated information

## Solution Overview

A command-line tool that:
1. Parses BattleScribe army list text exports
2. Enriches the data with complete unit information from pre-generated catalogues
3. Outputs formatted cheat sheets in HTML or Markdown
4. Optimizes layout for printing on standard paper sizes

## User Stories

### Critical (Must Have)

**US-001: Parse Army List**
```
As a player
I want to import my BattleScribe army list
So that I can generate a cheat sheet for my army
```

**US-002: View Unit Stats**
```
As a player
I want to see all unit stats (M, T, SV, W, LD, OC)
So that I can quickly reference them during gameplay
```

**US-003: View Weapon Profiles**
```
As a player
I want to see complete weapon profiles for all my units
So that I know the stats for attacks
```

**US-004: View Abilities**
```
As a player
I want to see all unit abilities with descriptions
So that I know what special rules my units have
```

**US-005: Print Cheat Sheet**
```
As a player
I want to print my cheat sheet
So that I can use it during physical games
```

### High Priority (Should Have)

**US-006: Faction Abilities**
```
As a player
I want to see army-wide faction abilities at the top
So that I remember what rules apply to my whole army
```

**US-007: Organize by Phase**
```
As a player
I want abilities organized by game phase
So that I can quickly find relevant abilities during each phase
```

**US-008: Optimized Page Breaks**
```
As a player
I want intelligent page breaks when printing
So that I minimize paper waste and maximize readability
```

**US-009: Character Enhancements**
```
As a player
I want to see which characters have enhancements
So that I remember their special upgrades
```

**US-010: Warlord Identification**
```
As a player
I want my Warlord clearly marked
So that I can easily identify them
```

### Medium Priority (Could Have)

**US-011: Multi-Model Units**
```
As a player with units containing different model types
I want to see each model's weapons separately
So that I know what each model can do
```

**US-012: Markdown Output**
```
As a player who wants to edit my cheat sheet
I want to export to Markdown format
So that I can customize it further
```

**US-013: Web Preview**
```
As a player
I want to preview my HTML cheat sheet in a browser
So that I can verify it before printing
```

### Low Priority (Won't Have - V1)

**US-014: Enhancement Descriptions**
```
As a player
I want to see what my character enhancements do
So that I don't forget their effects
```
*Note: Deferred - Enhancement descriptions are detachment-specific and not available in BattleScribe catalogues*

**US-015: Stratagem Reference**
```
As a player
I want my army's stratagems included
So that I have all rules in one place
```
*Note: Deferred - Future enhancement*

**US-016: PDF Export**
```
As a player
I want to export directly to PDF
So that I don't need to print from browser
```
*Note: Deferred - Browser print-to-PDF works for V1*

## Functional Requirements

### FR-001: Army List Parsing

**Input**: BattleScribe text export (`.txt` file)

**Must Parse**:
- Army name and total points
- Faction and detachment
- All unit entries with:
  - Unit name and points cost
  - Warlord markers
  - Enhancements
  - Selected wargear items
  - Model counts for multi-model units
  - Weapon assignments per model

**Format Support**:
```
Army Name (Points)

Faction Name
Detachment Name
Strike Force (X,XXX Points)

CHARACTERS

Unit Name (Points)
  • Warlord
  • Wargear Item
  • Enhancements: Enhancement Name

BATTLELINE

Unit Name (Points)
  • 1x Model Name
     ◦ 1x Weapon Name
  • 9x Model Name
     ◦ 9x Weapon Name
```

**Output**: Python dictionary with structured army data

### FR-002: Catalogue Data Integration

**Input**: YAML catalogue file containing faction data

**Must Provide**:
- Complete unit datasheets
- Weapon profiles (ranged and melee)
- Ability descriptions
- Stat blocks
- Keywords
- Shared rules database

**Matching Logic**:
- Exact unit name match
- Case-insensitive weapon matching
- Handle weapon variations (e.g., "Power weapon" vs "Master-crafted power weapon")

### FR-003: Faction Ability Detection

**Algorithm**:
1. Scan all units for shared rules
2. Check if rule description contains "If your Army Faction is [FACTION]"
3. Count how many units have the rule
4. Include rule as faction ability if:
   - Has faction description pattern AND
   - Appears on ≥50% of units in army

**Purpose**:
- Include true army-wide faction abilities (e.g., "Oath of Moment")
- Exclude detachment-specific abilities (e.g., "Templar Vows")

**Output**: Faction abilities section at top of cheat sheet

### FR-004: Ability Organization

**Requirements**:
- Group abilities by game phase:
  - Command Phase
  - Movement Phase
  - Shooting Phase
  - Charge Phase
  - Fight Phase
  - Any Phase (always active)
- List passive abilities separately (e.g., "Leader", "Deep Strike")
- Filter out faction abilities from individual units (show only once at top)
- Include ability names and full descriptions

### FR-005: Page Optimization

**Algorithm**:
1. Calculate complexity score for each unit:
   - Base: 5 points
   - Per ranged weapon: +2 points
   - Per melee weapon: +2 points
   - Per ability: +3 points
   - Per passive ability: +1 point
   - Per additional model type: +4 points

2. Classify units:
   - Simple: <20 complexity (3-4 per page)
   - Medium: 20-35 complexity (2 per page)
   - Complex: >35 complexity (1 per page)

3. Group units on pages:
   - Track page capacity (0-100%)
   - Simple units = 25% capacity
   - Medium units = 50% capacity
   - Complex units = 100% capacity
   - Add page break when capacity would exceed 100%

**Target**: Optimize for US Letter (8.5" x 11") paper

### FR-006: HTML Output

**Requirements**:
- Clean, professional styling
- Color-coded sections:
  - Blue: Keywords
  - Orange: Passive abilities
  - Purple: Enhancements
  - White: Standard abilities
- Print button for easy printing
- Print-specific CSS:
  - Hide print button
  - Optimize font sizes
  - Apply page breaks
  - Remove backgrounds (optional)
- Responsive layout for screen viewing

### FR-007: Markdown Output

**Requirements**:
- GitHub-flavored Markdown
- Tables for stats and weapons
- Bold/italic formatting for emphasis
- Clear section headers
- Readable plain text format
- Easy to edit manually if needed

### FR-008: Multi-Model Unit Support

**Requirements**:
- Detect units with multiple model types (e.g., Sergeant + Troopers)
- Parse nested weapon assignments:
  ```
  • 1x Pack Leader
     ◦ 1x Plasma pistol
     ◦ 1x Power weapon
  • 9x Pack Member
     ◦ 9x Bolter
  ```
- Display each model type's weapons separately
- Show model counts
- Handle different weapon loadouts per model type

### FR-009: Enhancement Display

**Requirements**:
- Parse "Enhancements: [Name]" from army list
- Display below Keywords section
- Format consistently with other sections
- Only show for characters that have enhancements
- Support multiple enhancements per character (comma-separated)

**Limitation**:
- V1 shows enhancement name only
- Descriptions require separate database (future enhancement)

### FR-010: Catalogue Generation

**Tool**: `wh40k_parser.py`

**Input**: BattleScribe XML catalogue file (`.cat`)

**Must Extract**:
- All unit entries (`<selectionEntry>` with type="unit")
- Unit stats (profiles with typeName="Unit")
- Weapons (profiles with typeName="Weapon" or "Ranged Weapons" or "Melee Weapons")
- Abilities (rules and infoLinks)
- Keywords
- Shared rules (catalogueLinks)

**Output**: YAML file with structured faction data

**Processing**:
- Parse XML tree
- Extract nested profiles
- Resolve infoLinks to shared rules
- Organize weapons by type (ranged/melee)
- Preserve all stat values and descriptions

## Non-Functional Requirements

### NFR-001: Performance
- Parse army list: <1 second
- Generate cheat sheet: <3 seconds for typical 2000pt army
- Catalogue loading: <2 seconds

### NFR-002: Usability
- Command-line interface with clear help text
- Descriptive error messages
- Progress indicators during generation
- Example files provided

### NFR-003: Maintainability
- Modular code structure (separate parser, generator, CLI)
- Clear function names and docstrings
- Configuration through YAML files
- No hardcoded faction-specific logic

### NFR-004: Compatibility
- Python 3.7+
- Standard library + PyYAML only
- Works on Windows, Mac, Linux
- No GUI dependencies

### NFR-005: Data Quality
- Preserve exact stat values from BattleScribe
- Maintain weapon characteristic accuracy
- Include complete ability descriptions
- No data loss during conversion

### NFR-006: Print Quality
- Readable at standard print sizes
- High contrast for black & white printing
- Appropriate margins
- Clear section separation
- Page breaks at logical points

## Technical Constraints

### TC-001: BattleScribe Dependency
- Tool requires BattleScribe-formatted army lists
- Catalogue files must be generated from official BattleScribe `.cat` files
- Updates to BattleScribe data require catalogue regeneration

### TC-002: Enhancement Limitations
- Enhancement descriptions not available in BattleScribe catalogues
- Enhancements are detachment-specific (not in unit catalogues)
- V1 shows enhancement names only

### TC-003: Shared Rules
- Some shared rules may be in separate catalogue files
- Parser only reads single `.cat` file
- Complex rule references may need manual verification

### TC-004: Weapon Matching
- Weapon names must match between army list and catalogue
- Case variations handled (e.g., "power weapon" = "Power Weapon")
- Some weapons may have unit-specific variations

### TC-005: Paper Size
- Page optimization targets US Letter
- Other paper sizes (A4) may need adjustment
- Print margins vary by browser/printer

## Success Metrics

### Primary Metrics

1. **Successful Generation Rate**: >95% of valid BattleScribe army lists generate without errors
2. **Data Accuracy**: 100% accuracy for stats, weapons, and abilities vs. codex
3. **Print Quality**: Users can read cheat sheet at arm's length during gameplay
4. **Time Savings**: Generate cheat sheet in <5 minutes vs 30+ minutes manual creation

### Secondary Metrics

1. **Page Efficiency**: Average 3-5 units per page for typical armies
2. **Paper Usage**: 2000pt army fits on 3-5 pages
3. **User Satisfaction**: Players report faster gameplay and fewer codex lookups

## Out of Scope (V1)

The following features are explicitly out of scope for the initial version:

1. **GUI Interface**: Command-line only for V1
2. **Web Application**: Local tool only, no server component
3. **Database Storage**: Catalogue files only, no database
4. **Real-time Updates**: Manual catalogue regeneration required
5. **Enhancement Descriptions**: Names only, descriptions require separate database
6. **Stratagem Reference**: Unit datasheets only
7. **Secondary Objectives**: Game mission rules not included
8. **Army List Editor**: Import only, no editing functionality
9. **Points Calculator**: Uses points from BattleScribe list
10. **Roster Validation**: Assumes BattleScribe list is legal

## Future Enhancements (V2+)

Potential features for future versions:

1. **Enhancement Database**: YAML files with enhancement descriptions per detachment
2. **Stratagem Sheets**: Separate reference sheets for army stratagems
3. **Quick Reference Cards**: Smaller format for common abilities
4. **Interactive HTML**: Collapsible sections, search functionality
5. **PDF Export**: Direct PDF generation (not browser-based)
6. **A4 Paper Support**: Optimization for international paper sizes
7. **Custom Styling**: User-configurable colors and layouts
8. **Multi-Catalogue Parsing**: Support for linked catalogue files
9. **Digital-First Mode**: Tablet-optimized HTML with larger touch targets
10. **Army Comparison**: Side-by-side sheets for multiple armies

## Risk Assessment

### High Risk

**R-001: BattleScribe Format Changes**
- **Impact**: Tool breaks if BattleScribe changes export format
- **Mitigation**: Maintain parser for current format, version documentation
- **Likelihood**: Low (format stable for years)

**R-002: Catalogue Data Quality**
- **Impact**: Missing or incorrect unit data produces bad cheat sheets
- **Mitigation**: Example files for testing, verification against codexes
- **Likelihood**: Medium (depends on BattleScribe data quality)

### Medium Risk

**R-003: Edge Case Units**
- **Impact**: Complex units may not format correctly
- **Mitigation**: Extensive testing with diverse army lists
- **Likelihood**: Medium (40k has many special cases)

**R-004: Print Compatibility**
- **Impact**: Output may look different across browsers/printers
- **Mitigation**: Test with major browsers, use standard CSS
- **Likelihood**: Low (modern browsers consistent)

### Low Risk

**R-005: Python Version Compatibility**
- **Impact**: Tool may not work on older Python versions
- **Mitigation**: Specify Python 3.7+ requirement, test on multiple versions
- **Likelihood**: Low (syntax used is compatible)

## Acceptance Criteria

### For Product Release

The tool is considered complete when:

1. ✅ Parses valid BattleScribe army list text exports
2. ✅ Generates HTML and Markdown output
3. ✅ Includes all unit stats, weapons, and abilities
4. ✅ Identifies and displays faction abilities
5. ✅ Organizes abilities by phase
6. ✅ Supports character enhancements
7. ✅ Marks warlord characters
8. ✅ Handles multi-model units with different weapons
9. ✅ Optimizes page breaks for printing
10. ✅ Provides example army lists and output
11. ✅ Includes documentation for usage and catalogue generation
12. ✅ Works with at least 2 factions (Space Marines/Wolves, Death Guard)
13. ✅ CLI provides clear error messages
14. ✅ Generated output is accurate vs. codex

### Test Cases

**TC-001**: Generate cheat sheet for 2000pt Space Wolves army
- Expected: 3-4 page HTML output with all units, stats, weapons, abilities

**TC-002**: Generate cheat sheet for Death Guard army
- Expected: Correct faction ability ("Nurgle's Gift"), not "Oath of Moment"

**TC-003**: Character with enhancement
- Expected: Enhancement name displayed below Keywords

**TC-004**: Multi-model unit (e.g., Intercessor Squad)
- Expected: Separate weapon lists for Sergeant and Intercessors

**TC-005**: Complex vehicle unit
- Expected: All weapons and abilities formatted correctly, full page if needed

**TC-006**: Markdown export
- Expected: Readable plain text with tables and formatting

**TC-007**: Army with detachment-specific ability
- Expected: Only true faction abilities shown, detachment abilities filtered

**TC-008**: Print preview
- Expected: Page breaks at appropriate locations, readable font sizes

## Appendix A: Example Army List Format

```
Redneck Bar Fighters (1620 Points)

Space Marines
Space Wolves
Saga of the Hunter
Strike Force (2,000 Points)

CHARACTERS

Logan Grimnar (110 Points)
  • Warlord
  • 1x Axe Morkai
  • 1x Storm bolter

Techmarine (65 Points)
  • 1x Forge bolter
  • 1x Servo-arm
  • Enhancements: Feral Rage

BATTLELINE

Blood Claws (135 Points)
  • 1x Blood Claw Pack Leader
     ◦ 1x Bolt pistol
     ◦ 1x Power weapon
  • 9x Blood Claw
     ◦ 9x Astartes chainsword
     ◦ 9x Bolt pistol

OTHER DATASHEETS

Rhino (75 Points)
  • 1x Armoured tracks
  • 1x Storm bolter
```

## Appendix B: Technical Stack

- **Language**: Python 3.7+
- **Dependencies**: PyYAML
- **Input Formats**: Text (army lists), XML (catalogues)
- **Output Formats**: HTML, Markdown
- **Architecture**: CLI tool with modular parsers

## Appendix C: Glossary

- **BattleScribe**: Popular army list building software for tabletop wargames
- **Datasheet**: Official unit stat card from Games Workshop
- **Faction Ability**: Army-wide rule that applies to all units
- **Enhancement**: Upgrade applied to character models
- **Warlord**: Commander of the army (one per army)
- **Detachment**: Army organization structure with specific rules
- **Shared Rule**: Common ability used by multiple units
- **Catalogue**: BattleScribe's XML file containing all faction data
