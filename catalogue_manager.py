#!/usr/bin/env python3
"""
Automatic catalogue detection and download from BSData GitHub
"""

import os
import re
import yaml
import requests
import tempfile
import shutil
from pathlib import Path
from typing import Optional, Dict, List
from wh40k_parser import CatalogueParser

# Map faction names from BattleScribe exports to BSData catalogue files
FACTION_CATALOGUE_MAP = {
    # Chaos
    'Death Guard': 'Chaos - Death Guard.cat',
    'Thousand Sons': 'Chaos - Thousand Sons.cat',
    'World Eaters': 'Chaos - World Eaters.cat',
    'Chaos Space Marines': 'Chaos - Chaos Space Marines.cat',
    'Chaos Daemons': 'Chaos - Chaos Daemons.cat',
    'Chaos Knights': 'Chaos - Chaos Knights.cat',
    "Emperor's Children": "Chaos - Emperor's Children.cat",

    # Imperium
    'Space Marines': 'Imperium - Space Marines.cat',
    'Space Wolves': 'Imperium - Space Wolves.cat',
    'Blood Angels': 'Imperium - Blood Angels.cat',
    'Dark Angels': 'Imperium - Dark Angels.cat',
    'Adeptus Mechanicus': 'Imperium - Adeptus Mechanicus.cat',
    'Astra Militarum': 'Imperium - Astra Militarum.cat',
    'Adepta Sororitas': 'Imperium - Adepta Sororitas.cat',
    'Adeptus Custodes': 'Imperium - Adeptus Custodes.cat',
    'Grey Knights': 'Imperium - Grey Knights.cat',
    'Imperial Knights': 'Imperium - Imperial Knights.cat',
    'Deathwatch': 'Imperium - Deathwatch.cat',
    'Black Templars': 'Imperium - Black Templars.cat',
    'Ultramarines': 'Imperium - Ultramarines.cat',
    'Imperial Fists': 'Imperium - Imperial Fists.cat',
    'Salamanders': 'Imperium - Salamanders.cat',
    'Raven Guard': 'Imperium - Raven Guard.cat',
    'Iron Hands': 'Imperium - Iron Hands.cat',
    'White Scars': 'Imperium - White Scars.cat',

    # Xenos
    'Necrons': 'Necrons.cat',
    'Orks': 'Orks.cat',
    'Tyranids': 'Tyranids.cat',
    "T'au Empire": "T'au Empire.cat",
    'Tau Empire': "T'au Empire.cat",  # Alternative spelling
    'Aeldari': 'Aeldari - Craftworlds.cat',
    'Craftworlds': 'Aeldari - Craftworlds.cat',
    'Drukhari': 'Aeldari - Drukhari.cat',
    'Leagues of Votann': 'Leagues of Votann.cat',
    'Genestealer Cults': 'Genestealer Cults.cat',
}

GITHUB_RAW_BASE = 'https://raw.githubusercontent.com/BSData/wh40k-10e/main/'

# Map factions to their primary linked catalogues (for common weapons/units)
FACTION_LINKED_CATALOGUES = {
    'Space Wolves': ['Imperium - Space Marines.cat'],
    'Blood Angels': ['Imperium - Space Marines.cat'],
    'Dark Angels': ['Imperium - Space Marines.cat'],
    'Black Templars': ['Imperium - Space Marines.cat'],
    'Deathwatch': ['Imperium - Space Marines.cat'],
    'Ultramarines': ['Imperium - Space Marines.cat'],
    'Imperial Fists': ['Imperium - Space Marines.cat'],
    'Salamanders': ['Imperium - Space Marines.cat'],
    'Raven Guard': ['Imperium - Space Marines.cat'],
    'Iron Hands': ['Imperium - Space Marines.cat'],
    'White Scars': ['Imperium - Space Marines.cat'],
    'Grey Knights': ['Imperium - Space Marines.cat'],
}


class CatalogueManager:
    """Manages automatic catalogue detection and downloading"""

    def __init__(self, catalogues_dir: Path):
        self.catalogues_dir = Path(catalogues_dir)
        self.catalogues_dir.mkdir(exist_ok=True)

    def detect_faction(self, army_list_text: str) -> Optional[str]:
        """
        Detect faction from army list text
        Returns the faction name as it appears in BattleScribe
        """
        lines = army_list_text.strip().split('\n')

        # Collect all potential faction matches from first 10 lines
        potential_factions = []

        # The faction is typically on the second or third non-empty line
        # after the army name line
        for i, line in enumerate(lines[:10]):  # Check first 10 lines
            line = line.strip()

            # Skip empty lines and the army name line (contains "Points)")
            if not line or 'Points)' in line:
                continue

            # Skip detachment names and keywords
            if 'Strike Force' in line or 'Detachment' in line or 'Saga of' in line:
                continue

            # Check if this line matches a known faction
            for faction_name in FACTION_CATALOGUE_MAP.keys():
                if faction_name.lower() in line.lower():
                    potential_factions.append(faction_name)

        # If we found multiple matches, prefer the more specific one
        # (e.g., "Space Wolves" over "Space Marines")
        if potential_factions:
            # Remove duplicates while preserving order
            potential_factions = list(dict.fromkeys(potential_factions))

            # If "Space Marines" is in the list along with a specific chapter, prefer the chapter
            if "Space Marines" in potential_factions and len(potential_factions) > 1:
                potential_factions.remove("Space Marines")

            # Return the first remaining (most specific) faction
            # If multiple remain, sort by length descending
            if len(potential_factions) > 1:
                potential_factions.sort(key=len, reverse=True)

            return potential_factions[0]

        return None

    def get_catalogue_filename(self, faction_name: str) -> Optional[str]:
        """Get the BSData catalogue filename for a faction"""
        return FACTION_CATALOGUE_MAP.get(faction_name)

    def get_yaml_path(self, faction_name: str) -> Path:
        """Get the path to the YAML catalogue file"""
        # Convert faction name to safe filename
        safe_name = faction_name.lower().replace(' ', '_').replace("'", '')
        return self.catalogues_dir / f'{safe_name}.yaml'

    def has_catalogue(self, faction_name: str) -> bool:
        """Check if we have the catalogue locally"""
        yaml_path = self.get_yaml_path(faction_name)
        return yaml_path.exists()

    def download_and_parse_catalogue(self, faction_name: str) -> Optional[Dict]:
        """
        Download catalogue from GitHub and parse with linked catalogues
        Returns catalogue data dict or None if failed
        """
        cat_filename = self.get_catalogue_filename(faction_name)
        if not cat_filename:
            print(f"Unknown faction: {faction_name}")
            return None

        print(f"Downloading catalogue for {faction_name}...")

        # Create temporary directory for catalogues
        temp_dir = tempfile.mkdtemp()

        try:
            # Download the main catalogue
            cat_url = GITHUB_RAW_BASE + cat_filename
            response = requests.get(cat_url, timeout=30)
            response.raise_for_status()

            # Save main catalogue to temp directory
            main_cat_path = os.path.join(temp_dir, cat_filename)
            with open(main_cat_path, 'w') as f:
                f.write(response.text)

            # Download linked catalogues if needed
            linked_catalogues = FACTION_LINKED_CATALOGUES.get(faction_name, [])
            for linked_cat in linked_catalogues:
                try:
                    print(f"  Downloading linked catalogue: {linked_cat}...")
                    linked_url = GITHUB_RAW_BASE + linked_cat
                    linked_response = requests.get(linked_url, timeout=30)
                    linked_response.raise_for_status()

                    linked_path = os.path.join(temp_dir, linked_cat)
                    with open(linked_path, 'w') as f:
                        f.write(linked_response.text)
                except Exception as e:
                    print(f"  Warning: Could not download {linked_cat}: {e}")
                    # Continue without this linked catalogue

            # Parse with linked catalogues enabled
            print(f"Parsing catalogue for {faction_name}...")
            parser = CatalogueParser(main_cat_path, load_linked_catalogues=True)
            catalogue_data = parser.parse_catalogue(include_linked=True)

            print(f"✓ Catalogue parsed successfully")

            # Cache the result to YAML for faster future loading
            try:
                yaml_path = self.get_yaml_path(faction_name)
                with open(yaml_path, 'w') as f:
                    yaml.dump(catalogue_data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
                print(f"✓ Catalogue cached to {yaml_path.name}")
            except Exception as e:
                print(f"  Warning: Could not cache catalogue: {e}")

            return catalogue_data

        except requests.RequestException as e:
            print(f"Error downloading catalogue: {e}")
            return None
        except Exception as e:
            print(f"Error parsing catalogue: {e}")
            import traceback
            traceback.print_exc()
            return None
        finally:
            # Clean up temp directory
            shutil.rmtree(temp_dir, ignore_errors=True)

    def get_catalogue_for_army(self, army_list_text: str) -> Optional[Dict]:
        """
        Detect faction and get catalogue data
        Returns the catalogue dict or None if not found
        """
        # Detect faction
        faction_name = self.detect_faction(army_list_text)
        if not faction_name:
            return None

        # Check if we have it cached locally
        if self.has_catalogue(faction_name):
            yaml_path = self.get_yaml_path(faction_name)
            try:
                with open(yaml_path, 'r') as f:
                    return yaml.safe_load(f)
            except Exception as e:
                print(f"Error loading cached catalogue: {e}")
                # Fall through to download

        # Download and parse in-memory
        return self.download_and_parse_catalogue(faction_name)

    def get_faction_name(self, army_list_text: str) -> Optional[str]:
        """Just return the detected faction name"""
        return self.detect_faction(army_list_text)
