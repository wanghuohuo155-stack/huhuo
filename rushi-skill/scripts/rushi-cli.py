"""入世 CLI 自举入口：python rushi-cli.py <subcommand>"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from rushi.cli import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
