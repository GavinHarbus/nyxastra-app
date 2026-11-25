import contextlib
import copy
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import build_community as builder
from lib.schema import validate_nyxtemplate


def document(version=2, **preset):
    return {
        "schema": "nyxtemplate", "version": version, "name": "Landscape",
        "body": "A landscape", "variables": [], "tags": [],
        "parameterPreset": preset,
        "community": {"author": {"name": "Creator"}, "license": "CC0-1.0", "category": "illustration"},
    }


class Image26ValidationTests(unittest.TestCase):
    def test_supported_presets_keep_legacy_and_new_formats(self):
        cases = [
            document(), document(2, format="png", quality="xhigh", complexity="low"),
            document(2, format="webp", quality="max", complexity="medium", background="transparent"),
            document(3, format="svg", n=1, quality="max", complexity="high"),
            document(4, format="gif"),
            document(4, format="gif", frameCount=2, frameDurationMS=20, size={"width": 0, "height": 0}),
            document(4, format="gif", frameCount=16, frameDurationMS=2000, size={"width": 512, "height": 256}),
            document(4, format="gif", frameCount=None, frameDurationMS=None, quality=None),
        ]
        for doc in cases:
            with self.subTest(preset=doc["parameterPreset"]):
                self.assertEqual([], validate_nyxtemplate(doc).errors)

    def test_invalid_parameters_report_errors_without_crashing(self):
        cases = [
            {"complexity": "max"}, {"complexity": []}, {"quality": {}}, {"format": []},
            {"format": "svg", "n": 2}, {"format": "gif", "frameCount": 1},
            {"format": "gif", "frameCount": 17}, {"format": "gif", "frameCount": True},
            {"format": "gif", "frameCount": 2.5}, {"format": "gif", "frameDurationMS": 19},
            {"format": "gif", "frameDurationMS": 2001}, {"format": "gif", "frameDurationMS": "200"},
            {"format": "png", "frameCount": 9}, {"frameDurationMS": 200},
            {"format": "svg", "background": "transparent"}, {"format": "gif", "background": "transparent"},
            {"format": "jpeg", "background": "transparent"}, {"n": True}, {"n": 0}, {"n": 11},
            {"size": []}, {"size": {"width": 0, "height": 512}},
            {"format": "gif", "size": {"width": 513, "height": 256}},
            {"format": "gif", "size": {"width": 16385, "height": 256}},
            {"size": {"width": True, "height": 256}},
        ]
        for preset in cases:
            with self.subTest(preset=preset):
                self.assertTrue(validate_nyxtemplate(document(4, **preset)).errors)

    def test_schema_version_must_cover_the_recipe(self):
        for version, preset in [(2, {"format": "svg"}), (3, {"format": "gif"}),
                                (2, {"format": "gif", "frameCount": 9}), (5, {}), (True, {})]:
            with self.subTest(version=version, preset=preset):
                self.assertTrue(validate_nyxtemplate(document(version, **preset)).errors)

    def test_new_recipe_formats_do_not_enable_vector_or_animated_covers(self):
        for cover_format in ["svg", "gif", []]:
            doc = document(4, format="gif")
            doc["cover"] = {"format": cover_format, "dataBase64": "AA=="}
            self.assertIn("cover-bad-format", [issue.code for issue in validate_nyxtemplate(doc).errors])
        for cover_format in ["png", "jpeg", "webp"]:
            doc["cover"]["format"] = cover_format
            self.assertEqual([], validate_nyxtemplate(doc).errors)


class Image26BuildTests(unittest.TestCase):
    def test_downloads_keep_per_template_versions_and_settings(self):
        cases = [("raster", document(2, format="png", complexity="low")),
                 ("vector", document(3, format="svg", n=1)),
                 ("animation", document(4, format="gif", frameCount=12, frameDurationMS=150))]
        original = copy.deepcopy(cases)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with patch.multiple(builder, REPO_ROOT=root, DIST_DIR=root / "dist",
                                DIST_TEMPLATES=root / "dist/templates", DIST_COVERS=root / "dist/covers",
                                DIST_INDEX=root / "dist/index.json", DIST_MANIFEST=root / "dist/manifest.json"), \
                    patch.object(builder, "load_featured_slugs", return_value=[]), \
                    patch.object(builder, "blob_base", return_value=None), contextlib.redirect_stdout(io.StringIO()):
                builder.build_dist([{"slug": slug, "doc": doc, "cover_bytes": None} for slug, doc in cases])
            index = json.loads((root / "dist/index.json").read_text())
            self.assertEqual(4, index["templateSchemaVersion"])
            for (slug, source), entry in zip(cases, index["templates"]):
                published = json.loads((root / f"dist/templates/{slug}.nyxtemplate").read_text())
                self.assertEqual(source["version"], published["version"])
                self.assertEqual(source["version"], entry["templateSchemaVersion"])
                self.assertEqual(source["parameterPreset"], published["parameterPreset"])
                self.assertEqual(source["parameterPreset"], entry["parameterPreset"])
                self.assertEqual([], validate_nyxtemplate(published).errors)
            self.assertEqual(original, cases)


if __name__ == "__main__":
    unittest.main()
