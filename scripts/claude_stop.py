#!/usr/bin/env python3
"""Optional local structure check only; not an application test or compliance proof."""
import json
import sys
from harness import doctor
from _core import ConfigError

def main():
    try:
        event = json.load(sys.stdin)
        if event.get("stop_hook_active"):
            return 0
        doctor()
        return 0
    except (ValueError, OSError, ConfigError, AttributeError) as exc:
        print(f"Starter structure check failed: {exc}. Fix or report the blocker; do not claim product verification.", file=sys.stderr)
        return 2

if __name__ == "__main__":
    raise SystemExit(main())
