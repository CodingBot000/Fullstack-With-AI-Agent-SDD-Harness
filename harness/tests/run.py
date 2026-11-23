"""Run the required kit tests in isolation from application tests."""
from pathlib import Path
import sys
import unittest


REQUIRED_SUITES = ("test_core.py", "test_harness.py", "test_collect.py", "test_evaluate.py")


def main() -> int:
    directory = Path(__file__).resolve().parent
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    for filename in REQUIRED_SUITES:
        if not (directory / filename).is_file():
            print(f"Missing required kit test suite: {filename}", file=sys.stderr)
            return 1
        tests = loader.discover(str(directory), pattern=filename)
        if not tests.countTestCases():
            print(f"No tests discovered in required kit test suite: {filename}", file=sys.stderr)
            return 1
        suite.addTests(tests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if result.testsRun == len(result.skipped):
        print("No kit tests were executed", file=sys.stderr)
        return 1
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
