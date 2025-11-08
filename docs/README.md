# Project Documentation

This directory contains comprehensive documentation for the Warhammer 40k Cheat Sheet Generator project.

## Documentation Index

### 1. [Product Requirements Document](PRODUCT_REQUIREMENTS.md)
**Purpose**: Defines what the product should do and why

**Contains**:
- Problem statement and target users
- User stories (must-have, should-have, could-have)
- Functional requirements (FR-001 through FR-010)
- Non-functional requirements (performance, usability)
- Success metrics and acceptance criteria
- Feature scope and limitations

**Read this if you want to**:
- Understand the product vision
- Know what features are included (and excluded)
- See the complete list of requirements
- Understand user needs and pain points

---

### 2. [Technical Specification](TECHNICAL_SPECIFICATION.md)
**Purpose**: Explains how the product is built

**Contains**:
- System architecture diagram
- Component breakdown (parsers, generators, CLI)
- Data models and structures
- Algorithm specifications (parsing, faction detection, page grouping)
- Implementation details for each module
- CSS styling and color scheme
- Error handling strategies
- Performance considerations

**Read this if you want to**:
- Understand the codebase architecture
- See algorithm pseudocode
- Know how specific features work
- Debug issues or add features
- Understand data flow

---

### 3. [Implementation Guide](IMPLEMENTATION_GUIDE.md)
**Purpose**: Step-by-step guide to rebuild the project from scratch

**Contains**:
- Phase-by-phase implementation plan
- Complete code examples for each component
- Testing and validation steps
- Common pitfalls to avoid
- Debugging strategies
- Completion checklist

**Read this if you want to**:
- Build this project from zero
- Teach someone how to implement it
- Understand the build process
- See working code examples
- Know the implementation order

---

### 4. [Design Decisions Log](DESIGN_DECISIONS.md)
**Purpose**: Records why specific design choices were made

**Contains**:
- 13 major design decisions with rationale
- Options considered for each decision
- Trade-offs and outcomes
- Lessons learned
- Future considerations

**Decisions Covered**:
1. Text-based army list parsing
2. YAML catalogues (not JSON/database)
3. Faction ability detection algorithm
4. Page break complexity algorithm
5. Enhancement name only (no descriptions)
6. Weapon matching heuristics
7. Organize abilities by phase
8. HTML + Markdown output
9. CSS color scheme
10. CLI over GUI
11. Page break after faction abilities
12. No database, no cloud
13. Support multi-model units

**Read this if you want to**:
- Understand the "why" behind choices
- Avoid repeating past mistakes
- Make consistent future decisions
- See what alternatives were considered

---

## How to Use This Documentation

### For New Developers

**Quick Start Path**:
1. Read the **Product Requirements** (to understand what it does)
2. Skim the **Technical Specification** (to see the architecture)
3. Follow the **Implementation Guide** (to build it)
4. Refer to **Design Decisions** (when you have questions about "why")

### For AI Agents

**Rebuilding the Project**:
1. Start with **Product Requirements** for context
2. Use **Implementation Guide** as step-by-step instructions
3. Reference **Technical Specification** for algorithms and data structures
4. Check **Design Decisions** when making trade-offs

### For Project Maintainers

**Making Changes**:
1. Check **Product Requirements** (is this in scope?)
2. Review **Design Decisions** (what constraints exist?)
3. Update **Technical Specification** (document your changes)
4. Add new decisions to **Design Decisions** (document rationale)

### For Contributors

**Adding Features**:
1. Propose feature against **Product Requirements** (does it fit?)
2. Study **Technical Specification** (where does it go?)
3. Follow patterns in **Implementation Guide** (consistent style)
4. Document decision in **Design Decisions** (explain choices)

---

## Document Status

| Document | Status | Last Updated | Completeness |
|----------|--------|--------------|--------------|
| Product Requirements | ✅ Complete | 2024-11-08 | 100% |
| Technical Specification | ✅ Complete | 2024-11-08 | 100% |
| Implementation Guide | ✅ Complete | 2024-11-08 | 100% |
| Design Decisions | ✅ Complete | 2024-11-08 | 100% |

---

## Keeping Documentation Updated

### When to Update Documentation

**Product Requirements**:
- New feature requests
- Changed requirements
- New user stories
- Updated success metrics

**Technical Specification**:
- Architecture changes
- New algorithms
- API changes
- Performance optimizations

**Implementation Guide**:
- Build process changes
- New setup steps
- Updated dependencies
- New best practices

**Design Decisions**:
- Every significant design choice
- When alternatives are considered
- When existing decisions are changed
- When lessons are learned

### Documentation Best Practices

1. **Be Specific**: Include code examples, not just descriptions
2. **Explain Why**: Don't just document what, explain why
3. **Show Alternatives**: Document what didn't work and why
4. **Keep Current**: Update docs when code changes
5. **Use Examples**: Real-world examples are more valuable than theory

---

## Additional Resources

### External Documentation

- **BattleScribe**: https://battlescribe.net/
- **Warhammer 40k**: https://warhammer40000.com/
- **PyYAML**: https://pyyaml.org/
- **Python**: https://docs.python.org/3/

### Related Files

- **Main README**: `../README.md` - User-facing documentation
- **Catalogue README**: `../catalogues/README.md` - Catalogue generation guide
- **Examples**: `../examples/` - Sample army lists and outputs

---

## Questions and Feedback

### Common Questions

**Q: Where do I start?**
A: Read the Product Requirements document first to understand the project vision.

**Q: I want to add a feature. Where should I look?**
A: Check Product Requirements (scope), Technical Specification (architecture), and Design Decisions (constraints).

**Q: How was X implemented?**
A: See Technical Specification for algorithms, Implementation Guide for code examples.

**Q: Why was Y done this way?**
A: Check Design Decisions document for the rationale.

**Q: I want to rebuild this project. What's the process?**
A: Follow the Implementation Guide step-by-step.

### Getting Help

1. Check this documentation first
2. Look at example files in `../examples/`
3. Review the main README for usage instructions
4. Examine the source code (it's well-commented)

---

## Version History

### Version 1.0 (2024-11-08)
- Initial documentation suite
- Product Requirements Document
- Technical Specification
- Implementation Guide
- Design Decisions Log

### Future Plans

Planned documentation additions:
- API Reference (if we add programmatic API)
- Testing Guide (when we add unit tests)
- Deployment Guide (for packaging and distribution)
- Contribution Guide (for open source contributions)
- Troubleshooting FAQ (based on user issues)

---

## Document Maintenance

**Owner**: Project maintainers

**Review Cycle**: Update documentation when:
- Major features are added
- Architecture changes
- Design decisions are made
- User feedback indicates confusion

**Format**: Markdown (for readability and version control)

**Location**: `/docs/` directory in project root

---

**Last Updated**: November 8, 2024
**Maintained By**: Project team
**Status**: Active and current
