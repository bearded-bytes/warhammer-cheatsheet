#!/usr/bin/env python3
"""
Warhammer 40k Cheat Sheet Generator - Web Application
Allows users to paste army lists and generate cheat sheets online
"""

from flask import Flask, render_template, request, jsonify, send_file
import os
import tempfile
from pathlib import Path
from cheat_sheet_generator import CheatSheetGenerator
from catalogue_manager import CatalogueManager

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max

# Initialize catalogue manager
CATALOGUES_DIR = Path(__file__).parent / 'catalogues'
catalogue_manager = CatalogueManager(CATALOGUES_DIR)


@app.route('/')
def index():
    """Main page with army list input form"""
    return render_template('index.html')


@app.route('/generate', methods=['POST'])
def generate_cheat_sheet():
    """Generate cheat sheet from posted army list"""
    try:
        # Get form data
        army_list_text = request.form.get('army_list', '')
        output_format = request.form.get('format', 'html')

        # Validate inputs
        if not army_list_text or not army_list_text.strip():
            return jsonify({'error': 'Please provide an army list'}), 400

        # Auto-detect faction and get/download catalogue
        faction_name = catalogue_manager.get_faction_name(army_list_text)
        if not faction_name:
            return jsonify({
                'error': 'Could not detect faction from army list. Please ensure you copied the complete BattleScribe export including the faction name.'
            }), 400

        catalogue_data = catalogue_manager.get_catalogue_for_army(army_list_text)
        if not catalogue_data:
            return jsonify({
                'error': f'Could not load catalogue for {faction_name}. This faction may not be supported yet.'
            }), 404

        # Generate cheat sheet
        generator = CheatSheetGenerator(catalogue_data)
        cheat_sheet = generator.generate_cheat_sheet(army_list_text)

        # Format output
        if output_format == 'markdown':
            output_content = generator.format_markdown(cheat_sheet)
        else:
            output_content = generator.format_html(cheat_sheet)

        # Return the generated content
        return jsonify({
            'success': True,
            'content': output_content,
            'army_name': cheat_sheet.get('army_name', 'Unknown Army'),
            'faction': faction_name,
            'points': cheat_sheet.get('points', 0),
            'format': output_format
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Error generating cheat sheet: {str(e)}'}), 500


@app.route('/about')
def about():
    """About page"""
    return render_template('about.html')


if __name__ == '__main__':
    # For development
    app.run(host='0.0.0.0', port=5000, debug=True)
