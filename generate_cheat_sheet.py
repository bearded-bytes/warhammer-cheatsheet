#!/usr/bin/env python3
"""
Main script to generate Warhammer 40k cheat sheets
"""

import sys
import argparse
from cheat_sheet_generator import CheatSheetGenerator


def main():
    parser = argparse.ArgumentParser(
        description='Generate Warhammer 40k game cheat sheets from army list exports'
    )
    parser.add_argument(
        'army_list',
        help='Path to army list export file (text format)'
    )
    parser.add_argument(
        'catalogue',
        help='Path to catalogue YAML file (e.g., space_wolves.yaml)'
    )
    parser.add_argument(
        '-o', '--output',
        default='cheat_sheet.md',
        help='Output file path (default: cheat_sheet.md)'
    )
    parser.add_argument(
        '-f', '--format',
        choices=['markdown', 'yaml', 'html'],
        default='markdown',
        help='Output format (default: markdown)'
    )

    args = parser.parse_args()

    # Read army list
    print(f"Reading army list from {args.army_list}...")
    with open(args.army_list, 'r') as f:
        army_list_text = f.read()

    # Generate cheat sheet
    print(f"Loading catalogue from {args.catalogue}...")
    generator = CheatSheetGenerator(args.catalogue)

    print("Generating cheat sheet...")
    cheat_sheet = generator.generate_cheat_sheet(army_list_text)

    # Format and save
    if args.format == 'markdown':
        output = generator.format_markdown(cheat_sheet)
    elif args.format == 'html':
        output = generator.format_html(cheat_sheet)
    else:
        output = generator.format_yaml(cheat_sheet)

    print(f"Writing output to {args.output}...")
    with open(args.output, 'w') as f:
        f.write(output)

    print(f"✓ Cheat sheet generated successfully!")
    print(f"  Army: {cheat_sheet['army_name']}")
    print(f"  Points: {cheat_sheet['points']}")
    print(f"  Characters: {len(cheat_sheet['characters'])}")
    print(f"  Units: {len(cheat_sheet['units'])}")


if __name__ == '__main__':
    main()
