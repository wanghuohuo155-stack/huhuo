"""证据与遥测存储：SQLite（stdlib 实现，无外部依赖）。"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


SCHEMA = """
CREATE TABLE IF NOT EXISTS claims (
    claim_id      TEXT PRIMARY KEY,
    skill_slug    TEXT NOT NULL,
    kind          TEXT,
    title         TEXT,
    source_chapter TEXT,
    source_quote  TEXT,
    source_span   TEXT,
    status        TEXT NOT NULL DEFAULT 'pending',
    confidence    TEXT,
    checker       TEXT,
    checked_at    TEXT
);
CREATE TABLE IF NOT EXISTS telemetry (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    ts         TEXT NOT NULL,
    skill_slug TEXT NOT NULL,
    event      TEXT NOT NULL,
    detail     TEXT
);
CREATE INDEX IF NOT EXISTS idx_claims_slug ON claims(skill_slug);
CREATE INDEX IF NOT EXISTS idx_telemetry_slug ON telemetry(skill_slug);
"""


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class Store:
    def __init__(self, db_path: Path | str):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.executescript(SCHEMA)

    def close(self) -> None:
        self.conn.close()

    # ---------- claims ----------
    def upsert_claim(self, claim: dict[str, Any]) -> None:
        row = (
            claim["claim_id"],
            claim.get("skill_slug", ""),
            claim.get("kind", ""),
            claim.get("title", ""),
            claim.get("source_chapter", ""),
            claim.get("source_quote", ""),
            claim.get("source_span") or "",
            claim.get("status", "pending"),
            claim.get("confidence") or "",
            claim.get("checker") or "",
            claim.get("checked_at") or "",
        )
        self.conn.execute(
            """INSERT INTO claims
               (claim_id, skill_slug, kind, title, source_chapter, source_quote,
                source_span, status, confidence, checker, checked_at)
               VALUES (?,?,?,?,?,?,?,?,?,?,?)
               ON CONFLICT(claim_id) DO UPDATE SET
                 skill_slug=excluded.skill_slug, kind=excluded.kind,
                 title=excluded.title, source_chapter=excluded.source_chapter,
                 source_quote=excluded.source_quote, source_span=excluded.source_span,
                 status=excluded.status, confidence=excluded.confidence,
                 checker=excluded.checker, checked_at=excluded.checked_at""",
            row,
        )
        self.conn.commit()

    def claims(self, skill_slug: str | None = None) -> list[dict[str, Any]]:
        if skill_slug:
            rows = self.conn.execute(
                "SELECT * FROM claims WHERE skill_slug=? ORDER BY claim_id", (skill_slug,)
            ).fetchall()
        else:
            rows = self.conn.execute("SELECT * FROM claims ORDER BY claim_id").fetchall()
        cols = [d[0] for d in self.conn.execute("SELECT * FROM claims LIMIT 1").description]
        return [dict(zip(cols, r)) for r in rows]

    def claim_stats(self) -> dict[str, int]:
        out: dict[str, int] = {}
        for status, n in self.conn.execute(
            "SELECT status, COUNT(*) FROM claims GROUP BY status"
        ):
            out[status] = n
        return out

    def import_claims_jsonl(self, path: Path) -> int:
        n = 0
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            self.upsert_claim(json.loads(line))
            n += 1
        return n

    def export_claims_jsonl(self, path: Path) -> None:
        lines = [json.dumps(c, ensure_ascii=False) for c in self.claims()]
        path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")

    # ---------- telemetry ----------
    def add_telemetry(self, skill_slug: str, event: str, detail: str = "") -> None:
        if not detail:
            detail = ""
        self.conn.execute(
            "INSERT INTO telemetry (ts, skill_slug, event, detail) VALUES (?,?,?,?)",
            (utcnow(), skill_slug, event, detail),
        )
        self.conn.commit()

    def telemetry(self, skill_slug: str | None = None) -> list[dict[str, Any]]:
        if skill_slug:
            rows = self.conn.execute(
                "SELECT * FROM telemetry WHERE skill_slug=? ORDER BY id", (skill_slug,)
            ).fetchall()
        else:
            rows = self.conn.execute("SELECT * FROM telemetry ORDER BY id").fetchall()
        cols = [d[0] for d in self.conn.execute("SELECT * FROM telemetry LIMIT 1").description]
        return [dict(zip(cols, r)) for r in rows]

    def telemetry_events(self, events: Iterable[str]) -> list[dict[str, Any]]:
        marks = ",".join("?" for _ in events)
        rows = self.conn.execute(
            f"SELECT * FROM telemetry WHERE event IN ({marks}) ORDER BY id", tuple(events)
        ).fetchall()
        cols = [d[0] for d in self.conn.execute("SELECT * FROM telemetry LIMIT 1").description]
        return [dict(zip(cols, r)) for r in rows]

