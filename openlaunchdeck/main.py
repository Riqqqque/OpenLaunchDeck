from __future__ import annotations

import sys


def main() -> int:
    try:
        from .app import run
    except ImportError:
        try:
            from openlaunchdeck.app import run
        except ImportError as fallback_exc:
            print(f"OpenLaunchDeck could not start: {fallback_exc}", file=sys.stderr)
            print("Install dependencies with: pip install -r requirements.txt", file=sys.stderr)
            return 1
    return run()


if __name__ == "__main__":
    raise SystemExit(main())
