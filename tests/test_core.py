"""Synthetic unit tests of the harness, not application/model quality measurements."""
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"scripts"))
from _core import ConfigError, command, parse_json, safe_path, source_fingerprint


class CoreTests(unittest.TestCase):
    def test_duplicate_json_keys_rejected(self):
        with self.assertRaises(ConfigError):
            parse_json('{"a":1,"a":2}')

    def test_nonfinite_json_rejected(self):
        for literal in ("NaN", "Infinity", "-Infinity"):
            with self.subTest(literal=literal), self.assertRaises(ConfigError):
                parse_json('{"a":'+literal+'}')

    def test_path_escape_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaises(ConfigError):
                safe_path("../outside", Path(temp))

    def test_absolute_path_rejected(self):
        with self.assertRaises(ConfigError):
            safe_path("/tmp/outside")

    def test_symlink_escape_rejected(self):
        with tempfile.TemporaryDirectory() as temp, tempfile.TemporaryDirectory() as outside:
            root=Path(temp)
            try:
                (root/"escape").symlink_to(Path(outside), target_is_directory=True)
            except OSError:
                self.skipTest("symlinks unavailable")
            with self.assertRaises(ConfigError):
                safe_path("escape/data.json", root)

    def test_argv_is_not_shell_evaluated(self):
        result=command(["{python}", "-c", "import sys; print(sys.argv[1])", "x; echo dangerous"], Path.cwd(), 5, capture=True)
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["stdout"].strip(), "x; echo dangerous")

    def test_timeout_recorded(self):
        result=command(["{python}", "-c", "import time; time.sleep(5)"], Path.cwd(), 0.03, capture=True)
        self.assertEqual(result["status"], "TIMEOUT")

    def test_missing_executable_is_not_pass(self):
        result=command(["this-executable-does-not-exist-271828"], Path.cwd(), 2, capture=True)
        self.assertEqual(result["status"], "ERROR")

    def test_source_change_detected_and_cache_ignored(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp); (root/"src").mkdir(); source=root/"src/a.py"
            source.write_text("old")
            first=source_fingerprint(["src"],root)
            cache=root/"src/__pycache__"; cache.mkdir(); (cache/"x.pyc").write_text("cache")
            self.assertEqual(first,source_fingerprint(["src"],root))
            source.write_text("new")
            self.assertNotEqual(first,source_fingerprint(["src"],root))

    def test_empty_source_selection_rejected(self):
        with self.assertRaises(ConfigError):
            source_fingerprint([])
