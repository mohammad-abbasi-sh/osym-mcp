"""Daily smoke probe (CI): latest announcements + calendar + health.

Run with:  python tests/smoke_live.py
Exit 0 = site reachable, exit 1 = blocked/error (visible in CI).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from osym_mcp.server import (  # noqa: E402
    osym_exam_calendar,
    osym_health,
    osym_latest_announcements,
)


def main() -> int:
    try:
        out = json.loads(osym_latest_announcements(limit=3))
        assert "error" not in out, out.get("error")
        assert out["count"] == 3
        first = out["announcements"][0]
        cal = json.loads(osym_exam_calendar(query="yks"))
        assert "error" not in cal, cal.get("error")
        assert cal["count"] >= 1
        health = json.loads(osym_health())
        assert health["status"] == "ok", health
        print(
            f"SMOKE OK: latest={first['date']} {first['title'][:60]} | "
            f"YKS rows={cal['count']}"
        )
        return 0
    except Exception as e:  # noqa: BLE001 — smoke must report, not crash
        print(f"SMOKE FAIL: {e}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
