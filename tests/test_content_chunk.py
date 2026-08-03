import tempfile
import unittest
from pathlib import Path

import _paths  # noqa: F401

from rushi import content


class ContentChunkTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_empty_source_raises(self):
        src = self.root / "empty.txt"
        src.write_text("   \n", encoding="utf-8")
        with self.assertRaises(ValueError):
            content.build_manifest(src, "t", "a", "2026", "doc")

    def test_chunk_by_paragraph(self):
        text = "甲" * 80 + "\n\n" + "乙" * 80 + "\n\n" + "丙" * 80
        chunks = content.chunk_text(text, max_chars=100)
        self.assertEqual(len(chunks), 3)
        self.assertEqual(chunks[0].text, "甲" * 80)
        self.assertEqual(chunks[1].text, "乙" * 80)

    def test_chunk_hard_cut_without_breaks(self):
        text = "x" * 45
        chunks = content.chunk_text(text, max_chars=10)
        self.assertEqual(len(chunks), 5)
        self.assertTrue(all(len(c.text) <= 10 for c in chunks))
        self.assertEqual("".join(c.text for c in chunks), text)

    def test_manifest_roundtrip(self):
        src = self.root / "src.txt"
        src.write_text("第一章\n\n正文内容", encoding="utf-8")
        manifest = content.build_manifest(src, "标题", "作者", "2026", "book", chunk_size=100)
        build = self.root / "build"
        content.write_manifest(build, manifest, src.read_text(encoding="utf-8"))
        loaded = content.load_manifest(build)
        self.assertEqual(loaded.title, "标题")
        self.assertEqual(loaded.author, "作者")
        self.assertEqual(loaded.sha256, manifest.sha256)
        self.assertEqual(loaded.kind, "book")


if __name__ == "__main__":
    unittest.main()
