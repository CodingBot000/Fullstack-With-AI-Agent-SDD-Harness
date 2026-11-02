#!/usr/bin/env python3
"""Replace with a project-owned adapter. Deliberately returns NOT_CONFIGURED."""
import sys

if __name__ == "__main__":
    print("NOT_CONFIGURED: implement the real project adapter; see evals/adapters/README.md", file=sys.stderr)
    raise SystemExit(2)
