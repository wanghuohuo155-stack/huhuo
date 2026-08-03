"""生成 examples/demo-pack 演示构建目录（内容来自 tests/fixtures）。"""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))

import fixtures  # noqa: E402


def main() -> None:
    demo = ROOT / "examples" / "demo-pack"
    if demo.exists():
        shutil.rmtree(demo)
    (demo / "candidates").mkdir(parents=True)
    (demo / "skills" / "slow-gardener" / "tests").mkdir(parents=True)
    (demo / "source.txt").write_text(fixtures.SOURCE_TEXT, encoding="utf-8")
    (demo / "claims.jsonl").write_text(
        "\n".join(json.dumps(c, ensure_ascii=False) for c in fixtures.CLAIMS) + "\n",
        encoding="utf-8",
    )
    (demo / "skills" / "slow-gardener" / "SKILL.md").write_text(
        fixtures.SKILL_MD, encoding="utf-8"
    )
    (demo / "skills" / "slow-gardener" / "tests" / "trigger.json").write_text(
        json.dumps(fixtures.TRIGGER_TESTS, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (demo / "candidates" / "glossary.md").write_text(
        "# 术语\n\n| 术语 | 作者的用法 | 与常识的差异 |\n"
        "|---|---|---|\n| 墒情 | 土壤含水量状态 | 判断而非感觉 |\n",
        encoding="utf-8",
    )
    print(f"[demo] 已生成: {demo}")


if __name__ == "__main__":
    main()
