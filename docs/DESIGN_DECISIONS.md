# Design Decisions Log

## Document Information
- **Version**: 1.0
- **Last Updated**: November 8, 2024
- **Purpose**: Record of key design decisions and rationale

## Overview

This document explains the "why" behind major design decisions made during development. Understanding these decisions helps maintain consistency and avoid regressing when making changes.

---

## Decision 1: Text-Based Army List Parsing (Not HTML)

### Decision
Parse BattleScribe text exports rather than HTML exports.

### Context
BattleScribe can export army lists in multiple formats:
- Plain text (structured with bullets and indentation)
- HTML (styled web page)
- Roster format (XML-like structure)

### Rationale

**Pros of Text Format:**
- Clean, consistent structure
- Easy to parse with regex and line-by-line processing
- Minimal noise (no HTML tags or styling)
- Human-readable
- Works with "Copy as Text" feature (no file needed)

**Cons of HTML:**
- Requires HTML parsing library (BeautifulSoup)
- More fragile (changes to BattleScribe's HTML structure break parser)
- More dependencies
- Harder to debug

**Cons of Roster (XML):**
- Very verbose with many nested tags
- Contains internal IDs that need resolving
- More complex to parse
- Not human-readable

### Outcome
Text format chosen for simplicity and robustness.

### Status
✅ Implemented and working well

---

## Decision 2: YAML Catalogues (Not JSON or Database)

### Decision
Store catalogue data as YAML files rather than JSON or database.

### Context
Catalogue data needs to be stored in a format that's:
- Easy to generate from BattleScribe XML
- Easy to read during cheat sheet generation
- Human-readable for debugging
- Version-controllable

### Rationale

**Why YAML over JSON:**
- More readable (no quotes on keys, better for multi-line strings)
- Supports comments (helpful for notes)
- PyYAML handles both reading and writing cleanly

**Why YAML over Database:**
- No setup required (no schema migrations, no server)
- Files are portable and self-contained
- Easy to version control
- Catalogue updates are just file replacements
- Simpler for end users (no database management)

**Trade-offs:**
- YAML files are large (500KB+ per faction)
- Slower to load than database queries
- No indexing or query optimization

### Outcome
YAML chosen for simplicity and portability. Performance is acceptable for typical use.

### Status
✅ Implemented. Performance is fine (<2s load time).

---

## Decision 3: Faction Ability Detection Algorithm

### Decision
Use two-tier algorithm: description pattern matching + frequency threshold.

### Context
Need to automatically identify which abilities are army-wide "faction abilities" vs unit-specific abilities. Original approach used only frequency (5+ units = faction ability) which incorrectly flagged "Invulnerable Save 4+".

### Problem
Some abilities appear on many units but aren't faction abilities (e.g., "Invulnerable Save" on multiple units).

### Iterations

**V1: Frequency Only**
```python
if count >= 5:
    faction_ability = True
```
❌ Failed - captured common unit abilities like "Invulnerable Save"

**V2: Description Pattern Only**
```python
if 'If your Army Faction is' in description:
    faction_ability = True
```
❌ Failed - captured detachment-specific abilities (e.g., "Templar Vows")

**V3: Combined Approach (Final)**
```python
if 'If your Army Faction is' in description and count >= 50% of units:
    faction_ability = True
```
✅ Success - accurately identifies true faction abilities

### Rationale

**Why 50% Threshold:**
- True faction abilities (like "Oath of Moment") appear on most units
- Detachment-specific abilities (like "Templar Vows") appear on few units
- 50% is a reasonable middle ground

**Why Both Checks:**
- Description pattern ensures it's faction-related
- Frequency threshold filters detachment abilities
- Together they accurately identify army-wide rules

**Why Filter All Faction-Like Abilities:**
- Even if not displayed, detachment abilities should be removed from individual units
- Prevents duplication and confusion
- Matches how players think about abilities

### Outcome
Algorithm correctly identifies faction abilities across different armies and detachments.

### Status
✅ Implemented and validated with Space Marines, Death Guard, Space Wolves.

---

## Decision 4: Page Break Complexity Algorithm

### Decision
Use complexity scoring (5 base + weapons + abilities + models) to classify units and assign page breaks.

### Context
Want to optimize printing on US Letter paper. Units vary greatly in complexity (single characters vs multi-model squads vs vehicles with many weapons).

### Approach

**Complexity Score:**
```
score = 5 (base)
      + (ranged weapons × 2)
      + (melee weapons × 2)
      + (abilities × 3)
      + (passive abilities × 1)
      + (additional models × 4)
```

**Classification:**
- Simple (<20): ~25% of page
- Medium (20-35): ~50% of page
- Complex (>35): 100% of page

### Rationale

**Why Scoring System:**
- Objective measurement
- Adapts to any army composition
- More accurate than fixed rules (e.g., "characters = simple")

**Why These Weights:**
- Abilities take more space (3 points) than weapons (2 points)
- Multi-model units need significant space (4 points per model type)
- Passive abilities are compact (1 point)

**Why Three Classes:**
- Balances granularity vs simplicity
- Maps to natural page divisions (quarter, half, full)
- Produces good results empirically

**Why 100% Capacity System:**
- Easy to reason about ("page is 80% full")
- Simple arithmetic (no complex bin-packing)
- Good-enough results for typical armies

### Tested Results

| Army | Total Units | Pages | Units/Page |
|------|-------------|-------|------------|
| Death Guard (2000pt) | 17 | 4 | 4.25 |
| Space Wolves (2000pt) | 14 | 3 | 4.67 |
| Redneck Bar Fighters | 14 | 3 | 4.67 |

### Trade-offs
- Not perfect bin-packing (optimal NP-hard problem)
- Sometimes leaves white space at bottom of pages
- Good enough for real-world use

### Outcome
Page breaks are logical and minimize paper waste.

### Status
✅ Implemented. Results are satisfactory.

---

## Decision 5: Enhancement Name Only (No Descriptions)

### Decision
Display enhancement names but not descriptions in V1.

### Context
Users requested enhancement support. Enhancements are character upgrades with names (e.g., "Feral Rage") and effects.

### Problem
Enhancement descriptions are detachment-specific and not included in BattleScribe catalogues. They would need to be:
- Manually compiled from codexes
- Organized by detachment
- Kept up-to-date with game updates

### Options Considered

**Option 1: Name + Description**
- PRO: Complete information
- CON: Requires separate enhancement database
- CON: Maintenance burden
- CON: Detachment-specific (complex mapping)

**Option 2: Name Only**
- PRO: Simple to implement (already in army list)
- PRO: No additional data needed
- CON: Players need to know what enhancements do

**Option 3: Link to External Resource**
- PRO: No maintenance
- CON: Requires internet connection
- CON: Breaks when URLs change

### Decision Rationale

Chose **Option 2: Name Only** for V1 because:
- Immediate value with minimal effort
- Users already know their enhancements (they picked them)
- Names serve as memory triggers
- Descriptions can be added in V2 as separate feature

### Future Enhancement
V2 could add enhancement database:
```yaml
# detachments/saga_of_the_hunter.yaml
enhancements:
  feral_rage:
    name: "Feral Rage"
    cost: 15
    description: "While this model is leading a unit..."
```

### Outcome
Enhancement names display correctly. User feedback will determine if descriptions are needed.

### Status
✅ Implemented as name-only. Feedback pending.

---

## Decision 6: Weapon Matching Heuristics

### Decision
Use heuristic-based classification to distinguish weapon items from model items.

### Context
Army lists have lines like:
```
  • 1x Pack Leader
  • 1x Power weapon
  • 1x Plasma pistol
```

Need to determine which are models and which are weapons without explicitly being told.

### Problem
BattleScribe doesn't mark which items are models vs weapons. Both use same bullet format. Context clues:
- Nested weapons under models
- Name patterns (e.g., "Leader" is a model, "pistol" is a weapon)
- Count notation (high counts often indicate models)

### Algorithm

```python
def classify_item(name, has_nested_weapons):
    # Step 1: If has nested weapons, it's definitely a model
    if has_nested_weapons:
        return 'model'

    # Step 2: Check name patterns
    model_keywords = ['leader', 'sergeant', 'marine', ...]
    weapon_keywords = ['pistol', 'bolter', 'sword', ...]

    if any(kw in name.lower() for kw in model_keywords):
        return 'model'
    if any(kw in name.lower() for kw in weapon_keywords):
        return 'weapon'

    # Step 3: Default to weapon if uncertain
    return 'weapon'
```

### Rationale

**Why Heuristic (Not ML or Catalogue Lookup):**
- Simple and fast
- No training data needed
- Works across all factions
- Easy to extend with new keywords

**Why Check Nested Weapons First:**
- 100% reliable signal
- Avoids false positives

**Why Default to Weapon:**
- Character units (common use case) have weapons, not models
- Less disruptive if wrong (shows as wargear list)

**Why Maintain Keyword Lists:**
- Covers 99% of cases
- Easy to add new patterns
- Explicit and debuggable

### Edge Cases

**Handled:**
- "Pack Leader with plasma pistol" → model (has "leader")
- "Power weapon" → weapon (has "weapon")
- "9x Blood Claw" with nested weapons → model (has nested)

**Not Handled:**
- Ambiguous names without keywords
- Non-English catalogues

### Outcome
Correctly classifies models and weapons in tested armies.

### Status
✅ Implemented. Works well in practice.

---

## Decision 7: Organize Abilities by Phase

### Decision
Group abilities by game phase rather than alphabetically or by type.

### Context
Warhammer 40k has structured game phases:
1. Command Phase
2. Movement Phase
3. Shooting Phase
4. Charge Phase
5. Fight Phase

Abilities trigger in specific phases or are always active.

### Rationale

**Why Phase Organization:**
- Matches game flow (players look up abilities when phase starts)
- Reduces cognitive load (only need to check relevant section)
- More usable than alphabetical (would scatter related abilities)

**Why Separate Passive Abilities:**
- Passive abilities (Leader, Deep Strike) are always active
- Different visual presentation (compact list vs detailed cards)
- Reduces clutter in phase sections

**Why Include "Any Phase":**
- Some abilities can trigger anytime
- Catch-all for abilities without clear phase

### Implementation

```python
phases = {
    'Command Phase': [],
    'Movement Phase': [],
    'Shooting Phase': [],
    'Charge Phase': [],
    'Fight Phase': [],
    'Any Phase': []
}
```

Phase detected from ability description keywords.

### Trade-offs
- Requires parsing ability descriptions
- May mis-categorize ambiguous abilities
- More complex than flat list

### Outcome
Abilities are organized logically. Players report this is more usable than codex format.

### Status
✅ Implemented. Positive user feedback.

---

## Decision 8: HTML + Markdown Output (Not Just One)

### Decision
Support both HTML and Markdown output formats.

### Context
Different users have different needs:
- Print users want styled HTML
- Digital users may prefer Markdown
- Some want to edit output

### Rationale

**Why HTML:**
- Rich styling and colors
- Print-optimized CSS
- Professional appearance
- Page breaks for printing

**Why Markdown:**
- Plain text (easy to edit)
- Version control friendly
- Works in text editors
- No browser needed
- GitHub-compatible

**Why Both:**
- Minimal extra effort (same data, different formatters)
- Covers more use cases
- Users can choose

### Implementation

```python
if format == 'markdown':
    return self._format_markdown(cheat_sheet)
else:
    return self._format_html(cheat_sheet)
```

Same enriched data structure, two formatters.

### Trade-offs
- More code to maintain (2 formatters)
- Need to keep both in sync
- More testing needed

### Outcome
Both formats work well. Users appreciate flexibility.

### Status
✅ Implemented. Both formats maintained equally.

---

## Decision 9: CSS Color Scheme

### Decision
Use distinct colors for different section types: blue (keywords), orange (passive abilities), purple (enhancements).

### Context
Need visual differentiation between section types to improve scannability.

### Color Choices

```css
.keywords-section {
    background: #f0f4ff;  /* Light blue */
    border-left: 4px solid #667eea;  /* Blue */
}

.passive-abilities-section {
    background: #fff4e6;  /* Light orange */
    border-left: 4px solid #ff9800;  /* Orange */
}

.enhancements-section {
    background: #f3e5f5;  /* Light purple */
    border-left: 4px solid #9c27b0;  /* Purple */
}
```

### Rationale

**Why Different Colors:**
- Quick visual scanning
- Sections stand out
- Reduces time to find information

**Why These Specific Colors:**
- Blue: Traditional for metadata/info (like keywords)
- Orange: Warm, attention-grabbing (passive = always relevant)
- Purple: Distinct, special (enhancements are unique upgrades)

**Why Light Backgrounds:**
- Printable (uses minimal ink)
- High contrast with black text
- Not distracting

**Why Left Border (Not Full Border):**
- Clean, modern look
- Less visual noise
- Still provides clear separation

### Accessibility
All color combinations pass WCAG AA contrast requirements.

### Outcome
Sections are visually distinct and easy to navigate.

### Status
✅ Implemented. No accessibility issues reported.

---

## Decision 10: CLI Over GUI

### Decision
Build command-line tool rather than graphical interface.

### Context
Need interface for users to generate cheat sheets.

### Options Considered

**Option 1: CLI**
- PRO: Fast to build
- PRO: Scriptable/automatable
- PRO: No framework dependencies
- CON: Less accessible to non-technical users

**Option 2: GUI (Electron, PyQt, tkinter)**
- PRO: More user-friendly
- PRO: Drag-and-drop files
- CON: Complex to build
- CON: Large dependencies
- CON: Platform-specific issues

**Option 3: Web App**
- PRO: Universal (works everywhere)
- PRO: Modern UX
- CON: Requires server
- CON: More complex architecture
- CON: Deployment overhead

### Decision Rationale

Chose **CLI** for V1 because:
- Target users (Warhammer players) are comfortable with tech
- Many already use BattleScribe (not beginner-friendly)
- CLI enables automation (batch processing, scripts)
- Can add GUI later if needed
- Faster time to MVP

### Outcome
CLI is sufficient for current user base. Web preview via simple HTTP server provides visual feedback.

### Status
✅ Implemented. No requests for GUI yet.

---

## Decision 11: Page Break After Faction Abilities

### Decision
Always insert page break after faction abilities section.

### Context
Faction abilities are army-wide rules that apply to all units. They should be:
- Highly visible
- Easy to reference
- Separated from unit-specific data

### Rationale

**Why Separate Page:**
- Faction abilities are conceptually different (army-wide vs unit-specific)
- Players reference them throughout the game
- Visual separation reinforces importance
- Allows printing only faction page as quick reference

**Why Not Group With First Unit:**
- Would push first unit to bottom of page (poor UX)
- Faction abilities often lengthy (multiple abilities)
- Clear separation is worth the paper cost

### Trade-offs
- Uses extra paper (faction abilities may not fill whole page)
- But: Better organization and usability

### Outcome
Clear separation between faction and unit information. Users find it helpful.

### Status
✅ Implemented. Positive feedback on organization.

---

## Decision 12: No Database, No Cloud

### Decision
Keep everything local: files only, no database, no cloud services.

### Context
Need to store and retrieve catalogue data and generated cheat sheets.

### Rationale

**Why Local Files:**
- Zero setup (download and run)
- No internet required after catalogue generation
- Complete privacy (no data sent anywhere)
- Works offline at game events
- No service costs or maintenance

**Why No Database:**
- Overkill for size of data
- Adds complexity for end users
- File loading is fast enough (<2s)
- YAML files are version-controllable

**Why No Cloud:**
- Players don't want to upload army lists (privacy)
- Internet unreliable at tournaments
- Adds dependency and failure point
- Increases complexity

### Trade-offs
- Can't share catalogues easily (each user generates own)
- No central updates (users must regenerate catalogues)
- But: Independence and privacy are more important

### Outcome
Tool works completely offline. No dependencies on external services.

### Status
✅ Implemented. Users appreciate offline capability.

---

## Decision 13: Support Multi-Model Units

### Decision
Handle units with different model types (e.g., Sergeant + Troopers) with separate weapon loadouts.

### Context
Many units have:
- Leader model with special wargear
- Multiple identical troops with standard wargear

Example:
```
Blood Claws (135 Points)
  • 1x Blood Claw Pack Leader
     ◦ 1x Power weapon
  • 9x Blood Claw
     ◦ 9x Bolt pistol
```

### Approach

**Data Structure:**
```python
{
    'models': [
        {
            'name': 'Blood Claw Pack Leader',
            'count': 1,
            'weapons': ['Power weapon']
        },
        {
            'name': 'Blood Claw',
            'count': 9,
            'weapons': ['Bolt pistol']
        }
    ]
}
```

**Display Format:**
- Two-column table
- Left: Pack Leader with weapons
- Right: Blood Claws with weapons

### Rationale

**Why Support This:**
- Common in 40k (almost all units have variants)
- Critical for gameplay (different models have different weapons)
- Army list exports show this structure

**Why Not Flatten:**
- Loses important information
- Players need to know which model has which weapon
- Matches how players think about units

**Why Two-Column Layout:**
- Compact (fits on page)
- Clear separation
- Easy to scan

### Outcome
Multi-model units display correctly with proper weapon assignments.

### Status
✅ Implemented. Handles complex units well.

---

## Lessons Learned

### What Worked Well

1. **Iterative Development**: Started simple, added features incrementally
2. **Test-Driven**: Used real army lists to drive implementation
3. **User Feedback**: Tested with actual players to validate approach
4. **Flexible Architecture**: Easy to add new formatters, features

### What Could Be Improved

1. **Testing**: Should have unit tests from start
2. **Edge Cases**: Encountered unexpected BattleScribe formats
3. **Documentation**: Should have documented as we built
4. **Error Messages**: Could be more helpful for debugging

### Future Considerations

1. **Enhancement Database**: Most requested feature
2. **More Catalogues**: Community wants all factions
3. **Customization**: Users want to tweak styling
4. **Performance**: Large catalogues are slow to load

---

## References

- BattleScribe Format: Observed from exports
- Warhammer 40k Rules: Games Workshop official rules
- User Feedback: Playtesting sessions
- CSS Best Practices: Web typography standards

---

**End of Design Decisions Log**
