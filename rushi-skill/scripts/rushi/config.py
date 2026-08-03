"""项目配置：rushi.json 的加载、默认值与落盘。"""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


CONFIG_NAME = "rushi.json"


@dataclass
class Config:
    """引擎配置。所有阈值都有默认值，可在 rushi.json 中覆盖。"""

    project_dir: Path
    provider: str = "openai"  # openai | mock
    json_mode: bool = True
    max_output_tokens: int = 8192
    model: str = ""
    api_key_env: str = "OPENAI_API_KEY"
    base_url: str = "https://api.openai.com/v1"
    chunk_size: int = 50000
    quote_max_chars: int = 150
    quote_max_words: int = 100
    min_critiques: int = 3
    min_glossary_terms: int = 5
    telemetry_enabled: bool = True
    target_trigger_precision: float = 0.95
    target_trigger_recall: float = 0.90
    bait_tolerance: int = 0
    min_pass_rate: float = 0.80
    mis_trigger_proposal_rate: float = 0.15
    negative_feedback_proposal_min: int = 3
    positive_feedback_promote_min: int = 10
    stale_days: int = 90
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["project_dir"] = str(self.project_dir)
        return data

    def save(self) -> None:
        data = self.to_dict()
        self.project_dir.mkdir(parents=True, exist_ok=True)
        (self.project_dir / CONFIG_NAME).write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    @classmethod
    def load(cls, project_dir: Path) -> "Config":
        cfg_path = Path(project_dir) / CONFIG_NAME
        data: dict[str, Any] = {}
        if not cfg_path.exists():
            data = {}
        else:
            data = json.loads(cfg_path.read_text(encoding="utf-8"))
        data.pop("project_dir", None)
        data.pop("extra", None)
        extra = {k: v for k, v in data.items() if k not in cls.__dataclass_fields__}
        for k in extra:
            data.pop(k)
        # 环境变量覆盖：允许不修改配置文件切换兼容端点（如 DeepSeek）
        if os.environ.get("RUSHI_BASE_URL"):
            data["base_url"] = os.environ["RUSHI_BASE_URL"]
        if os.environ.get("RUSHI_MODEL"):
            data["model"] = os.environ["RUSHI_MODEL"]
        if os.environ.get("RUSHI_API_KEY_ENV"):
            data["api_key_env"] = os.environ["RUSHI_API_KEY_ENV"]
        json_mode_env = os.environ.get("RUSHI_JSON_MODE")
        if json_mode_env in ("1", "true", "True"):
            data["json_mode"] = True
        elif json_mode_env in ("0", "false", "False"):
            data["json_mode"] = False
        return cls(project_dir=Path(project_dir).resolve(), **data, extra=extra)


def default_config(project_dir: Path) -> Config:
    return Config(project_dir=Path(project_dir).resolve())
