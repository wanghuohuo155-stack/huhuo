import json
import tempfile
import unittest
from pathlib import Path

import _paths  # noqa: F401

from rushi import schema


class SchemaTest(unittest.TestCase):
    def test_required(self):
        errors = schema.validate({"a": 1}, {"type": "object", "required": ["a", "b"]})
        self.assertTrue(any("缺少必填字段 'b'" in e for e in errors))

    def test_type(self):
        errors = schema.validate("x", {"type": "integer"})
        self.assertTrue(any("期望类型 integer" in e for e in errors))

    def test_enum(self):
        errors = schema.validate(
            {"c": "bad"},
            {"type": "object", "properties": {"c": {"enum": ["a", "b"]}}},
        )
        self.assertTrue(any("不在枚举" in e for e in errors))

    def test_pack_file_valid(self):
        pack = {
            "schema_version": "1.0",
            "name": "demo-pack",
            "version": "0.1.0",
            "source": {"title": "t", "sha256": "a" * 64},
            "confidence": "unverified",
            "freshness": {"packaged_at": "x", "expires_at": "y", "policy": "z"},
            "skills": ["slow-gardener"],
            "artifacts": ["PROVENANCE.md", "TEST_REPORT.md", "GLOSSARY.md", "INDEX.md"],
            "engine": "rushi",
        }
        spec = json.loads(
            (Path(__file__).resolve().parents[1] / "rushi-skill" / "references" / "specs" / "pack.schema.json")
            .read_text(encoding="utf-8")
        )
        self.assertEqual(schema.validate(pack, spec), [])


if __name__ == "__main__":
    unittest.main()

