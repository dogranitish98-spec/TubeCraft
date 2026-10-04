#!/usr/bin/env python3
"""Run TubeCraft's deterministic local media smoke test.

Use --live only after configuring AGNES_API_KEY and a reachable provider.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys

from core.self_test import self_test_workspace


def main() -> int:
    parser = argparse.ArgumentParser(description="TubeCraft Studio self-test")
    parser.add_argument("--live", action="store_true", help="Report whether live Agnes testing is configured")
    args = parser.parse_args()
    result = self_test_workspace(os.getcwd())
    result["live_configured"] = bool(os.environ.get("AGNES_API_KEY", "").strip())
    if args.live and not result["live_configured"]:
        result["live_error"] = "AGNES_API_KEY is not configured; local smoke test passed, live AI generation was not attempted."
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
