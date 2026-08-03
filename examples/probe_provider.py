"""最小 provider 探针：验证配置的端点/密钥/配额可用。用法：python examples/probe_provider.py"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "rushi-skill" / "scripts"))

from rushi.config import Config
from rushi.providers import ProviderError, get_provider


def main() -> int:
    cfg = Config.load(ROOT)
    provider = get_provider(cfg)
    try:
        text = provider.complete(
            "请只回复两个字：正常",
            system="你是连通性测试助手。",
        )
    except ProviderError as exc:
        print(f"probe FAILED: {exc}")
        return 1
    print(f"probe OK: model={getattr(provider, 'model', '?')} base={cfg.base_url} reply={text.strip()[:40]!r}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
