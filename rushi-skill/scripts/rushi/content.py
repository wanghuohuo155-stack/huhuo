"""内容摄入：源文件规范化、哈希、分块与内容清单。"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass
class Chunk:
    chunk_id: str
    text: str
    start: int
    end: int


@dataclass
class ContentManifest:
    source_file: str
    title: str
    author: str
    year: str
    kind: str  # book | video | podcast | course | interview | doc
    sha256: str
    chunk_size: int
    chunks: list[Chunk]
    created_at: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_file": self.source_file,
            "title": self.title,
            "author": self.author,
            "year": self.year,
            "kind": self.kind,
            "sha256": self.sha256,
            "chunk_size": self.chunk_size,
            "created_at": self.created_at,
            "chunks": [
                {"chunk_id": c.chunk_id, "start": c.start, "end": c.end}
                for c in self.chunks
            ],
        }


def read_source(path: Path | str) -> str:
    text = Path(path).read_text(encoding="utf-8-sig")
    return text.replace("\r\n", "\n").replace("\r", "\n")


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def chunk_text(text: str, max_chars: int, prefer_break_at: str = "\n\n") -> list[Chunk]:
    """按自然边界分块：优先双换行，其次单换行，最后硬切。"""
    chunks: list[Chunk] = []
    start = 0
    idx = 0
    n = 0
    while start < len(text):
        if start + max_chars >= len(text):
            chunks.append(Chunk(f"c{idx + 1:03d}", text[start:], start, len(text)))
            break
        window = text[start : start + max_chars]
        cut = window.rfind(prefer_break_at)
        consumed = 0
        if cut < max_chars // 10:
            cut = window.rfind("\n")
            consumed = 1 if cut >= max_chars // 10 else 0
        else:
            consumed = len(prefer_break_at)
        if cut < max_chars // 10:
            cut = max_chars
            consumed = 0
        end = start + cut
        chunks.append(Chunk(f"c{idx + 1:03d}", text[start:end], start, end))
        start = max(end + consumed, start + 1)
        idx += 1
        n += 1
        if n > 10_000:
            raise ValueError("分块数量异常，请检查 max_chars 配置")
    return chunks


def build_manifest(
    source_path: Path | str,
    title: str,
    author: str,
    year: str,
    kind: str,
    chunk_size: int = 50000,
) -> ContentManifest:
    text = read_source(source_path)
    if not text.strip():
        raise ValueError(f"源文件为空: {source_path}")
    return ContentManifest(
        source_file=str(Path(source_path).resolve()),
        title=title,
        author=author,
        year=year,
        kind=kind,
        sha256=sha256_text(text),
        chunk_size=chunk_size,
        chunks=chunk_text(text, chunk_size),
        created_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
    )


def book_dir(project: Path, slug: str) -> Path:
    return Path(project) / "books" / slug


def write_manifest(book_dir: Path, manifest: ContentManifest, source_text: str) -> None:
    book_dir.mkdir(parents=True, exist_ok=True)
    (book_dir / "source.txt").write_text(source_text, encoding="utf-8")
    (book_dir / "source.manifest.json").write_text(
        json.dumps(manifest.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8"
    )


def load_manifest(book_dir: Path) -> ContentManifest:
    data = json.loads((book_dir / "source.manifest.json").read_text(encoding="utf-8"))
    chunks = [
        Chunk(c["chunk_id"], data["chunks_text"].get(c["chunk_id"], ""), c["start"], c["end"])
        if "chunks_text" in data
        else Chunk(c["chunk_id"], "", c["start"], c["end"])
        for c in data["chunks"]
    ]
    return ContentManifest(
        source_file=data["source_file"],
        title=data["title"],
        author=data["author"],
        year=data["year"],
        kind=data["kind"],
        sha256=data["sha256"],
        chunk_size=data["chunk_size"],
        chunks=chunks,
        created_at=data["created_at"],
    )
