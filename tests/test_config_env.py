import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import _paths  # noqa: F401

from rushi.config import Config, default_config


class ConfigEnvTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_env_overrides(self):
        with mock.patch.dict(
            os.environ,
            {
                "RUSHI_BASE_URL": "https://override.test",
                "RUSHI_MODEL": "override-model",
                "RUSHI_API_KEY_ENV": "OVERRIDE_KEY",
                "RUSHI_JSON_MODE": "0",
            },
            clear=False,
        ):
            cfg = Config.load(self.root)
        self.assertEqual(cfg.base_url, "https://override.test")
        self.assertEqual(cfg.model, "override-model")
        self.assertEqual(cfg.api_key_env, "OVERRIDE_KEY")
        self.assertFalse(cfg.json_mode)

    def test_env_json_mode_true(self):
        with mock.patch.dict(os.environ, {"RUSHI_JSON_MODE": "1"}, clear=False):
            cfg = Config.load(self.root)
        self.assertTrue(cfg.json_mode)

    def test_default_json_mode_true(self):
        cfg = Config.load(self.root)
        self.assertTrue(cfg.json_mode)

    def test_save_load_roundtrip(self):
        cfg = default_config(self.root)
        cfg.model = "m1"
        cfg.json_mode = False
        cfg.save()
        cfg2 = Config.load(self.root)
        self.assertEqual(cfg2.model, "m1")
        self.assertFalse(cfg2.json_mode)
        self.assertEqual(cfg2.project_dir, self.root.resolve())

    def test_broken_json_raises(self):
        (self.root / "rushi.json").write_text("{broken", encoding="utf-8")
        with self.assertRaises(json.JSONDecodeError):
            Config.load(self.root)

    def test_extra_fields_captured(self):
        (self.root / "rushi.json").write_text(
            json.dumps({"unknown_field": 42}, ensure_ascii=False), encoding="utf-8"
        )
        cfg = Config.load(self.root)
        self.assertEqual(cfg.extra, {"unknown_field": 42})


if __name__ == "__main__":
    unittest.main()

