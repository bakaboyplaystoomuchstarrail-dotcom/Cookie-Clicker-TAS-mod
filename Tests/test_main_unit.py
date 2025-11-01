import json
import os
import tempfile
import unittest
from pathlib import Path

# Import the functions under test
from main import _build_js_building_name, _generate_verification_html


class TestMainHelpers(unittest.TestCase):
    def test_build_js_building_name_maps_known_names(self):
        # Known mappings from Python names to JS names
        mappings = {
            'cursor': 'Cursor',
            'grandma': 'Grandma',
            'farm': 'Farm',
            'mine': 'Mine',
            'factory': 'Factory',
            'bank': 'Bank',
            'temple': 'Temple',
            'wizard_tower': 'Wizard tower',
            'shipment': 'Shipment',
            'alchemy_lab': 'Alchemy lab',
        }
        for py_name, expected_js in mappings.items():
            self.assertEqual(_build_js_building_name(py_name), expected_js)

    def test_build_js_building_name_returns_input_for_unknown(self):
        unknown = 'space_port'
        self.assertEqual(_build_js_building_name(unknown), unknown)

    def test_generate_verification_html_creates_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output_file = Path(tmpdir) / 'verification' / 'test_verification.html'
            goal = 123.0
            total_time_ms = 4567
            path_json = [["click", 1, 0], ["buy", "cursor", 10], ["wait", 1, 11]]
            predicted_buildings = {"Cursor": 1}

            _generate_verification_html(str(output_file), goal, total_time_ms, path_json, predicted_buildings)

            self.assertTrue(output_file.exists())
            content = output_file.read_text(encoding='utf-8')
            self.assertTrue(len(content) > 0)

    def test_generate_verification_html_embeds_bfs_path(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output_file = Path(tmpdir) / 'verification' / 'embed_bfs.html'
            goal = 50.0
            total_time_ms = 200
            path_json = [["click", 1, 0], ["wait", 1, 1], ["buy", "grandma", 2]]

            _generate_verification_html(str(output_file), goal, total_time_ms, path_json, {})

            content = output_file.read_text(encoding='utf-8')
            expected_snippet = f"const BFS_PATH = {json.dumps(path_json)};"
            self.assertIn(expected_snippet, content)

    def test_generate_verification_html_embeds_predicted_buildings(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output_file = Path(tmpdir) / 'verification' / 'embed_buildings.html'
            goal = 75.0
            total_time_ms = 350
            predicted_buildings = {"Cursor": 3, "Grandma": 2}

            _generate_verification_html(str(output_file), goal, total_time_ms, [], predicted_buildings)

            content = output_file.read_text(encoding='utf-8')
            expected_snippet = f"const PREDICTED_BUILDINGS = {json.dumps(predicted_buildings)};"
            self.assertIn(expected_snippet, content)


if __name__ == '__main__':
    unittest.main()
