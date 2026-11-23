"""Small, dependency-free utilities. Configuration is trusted code, not a sandbox."""
from __future__ import annotations
import hashlib
import json
import math
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
from collections.abc import Iterable
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SOURCE_FINGERPRINT_EXCLUSIONS = {
    ".git", ".harness", "__pycache__", "node_modules", ".venv", "venv",
    ".pytest_cache", ".next", "dist", "build", "coverage",
}

class ConfigError(ValueError):
    """Invalid or incomplete configuration; never silently interpreted as success."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ConfigError(message)


def _pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in items:
        require(key not in result, f"Duplicate JSON key: {key}")
        result[key] = value
    return result


def parse_json(text: str) -> Any:
    def reject(value: str) -> None:
        raise ConfigError(f"Non-finite JSON number: {value}")
    try:
        return json.loads(text, object_pairs_hook=_pairs, parse_constant=reject)
    except json.JSONDecodeError as exc:
        raise ConfigError(f"Invalid JSON at line {exc.lineno}, column {exc.colno}") from exc


def load_json(path: Path) -> Any:
    try:
        return parse_json(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ConfigError(f"Cannot read file: {path}") from exc


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise ConfigError(f"Cannot read dataset/results: {path}") from exc
    result = []
    for number, line in enumerate(lines, 1):
        if not line.strip():
            continue
        row = parse_json(line)
        require(isinstance(row, dict), f"JSONL line {number} must be an object")
        result.append(row)
    return result


def safe_path(value: str, root: Path = ROOT) -> Path:
    require(isinstance(value, str) and bool(value.strip()), "A repository-relative path is required")
    require(not Path(value).is_absolute(), "Absolute paths are not accepted")
    root = root.resolve()
    result = (root / value).resolve()
    require(result.is_relative_to(root), f"Path escapes repository: {value}")
    return result


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def report_config(value: str | None, root: Path = ROOT) -> dict:
    """Read declared input paths when available. The verifier validates the config."""
    try:
        data = load_json(safe_path(value, root))
    except (OSError, ValueError, RuntimeError):
        return {}
    return data if isinstance(data, dict) else {}


def _require_report_target(path: Path, scope: str) -> None:
    if not path.exists():
        return
    try:
        old = load_json(path) if path.is_file() else None
    except (ConfigError, UnicodeError):
        old = None
    compatible_scopes = ("starter-kit-only", "kit") if scope == "starter-kit-only" else (scope,)
    require(
        isinstance(old, dict) and old.get("scope") in compatible_scopes
        and old.get("status") in ("PASS", "FAIL", "ERROR", "TIMEOUT", "NOT_CONFIGURED_OR_INVALID"),
        f"Report path already exists and is not a {scope} report: {path.name}",
    )


def report_path(value: str, scope: str, inputs: Iterable[str | None], root: Path = ROOT) -> Path:
    root = root.resolve()
    path = safe_path(value, root)
    for parent in path.parents:
        if parent.exists():
            require(parent.is_dir(), f"Report parent is not a directory: {parent.name}")
            break
    for input_value in inputs:
        try:
            input_path = safe_path(input_value, root)
        except (OSError, ValueError, RuntimeError):
            continue  # Invalid config values are reported by the verifier.
        matches = input_path.is_relative_to(path)
        if not matches and path.exists() and input_path.exists():
            matches = path.samefile(input_path)
        require(not matches, f"Report path must differ from input files: {path.relative_to(root)}")
        if input_path.is_dir() and path.is_relative_to(input_path):
            require(
                not SOURCE_FINGERPRINT_EXCLUSIONS.isdisjoint(path.relative_to(root).parts),
                f"Report path is inside a source directory used for evaluation: {path.relative_to(root)}",
            )
    _require_report_target(path, scope)
    return path


def write_report(path: Path, data: dict) -> None:
    _require_report_target(path, data["scope"])
    content = json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent, delete=False) as stream:
        staged = Path(stream.name)
        try:
            stream.write(content)
            stream.close()
            staged.replace(path)
        finally:
            staged.unlink(missing_ok=True)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def digest(data: Any) -> str:
    return hashlib.sha256(json.dumps(data, ensure_ascii=False, sort_keys=True, allow_nan=False).encode()).hexdigest()


def nonnegative(value: Any, label: str) -> float:
    require(isinstance(value, (int, float)) and not isinstance(value, bool), f"{label}: a number is required")
    require(math.isfinite(value) and value >= 0, f"{label}: must be finite and non-negative")
    return float(value)


def rate(value: Any, label: str) -> float:
    number = nonnegative(value, label)
    require(number <= 1, f"{label}: expected a number between 0 and 1")
    return number


def positive_int(value: Any, label: str) -> int:
    require(isinstance(value, int) and not isinstance(value, bool) and value > 0, f"{label}: a positive integer is required")
    return value


def command(argv: list[str], cwd: Path, timeout: float, stdin: str | None = None,
            capture: bool = False) -> dict[str, Any]:
    require(isinstance(argv, list) and bool(argv) and all(isinstance(x, str) and x for x in argv), "argv must be a nonempty list of strings")
    require(cwd.is_dir(), f"Command working directory does not exist: {cwd}")
    require(nonnegative(timeout, "timeout_seconds") > 0, "timeout_seconds must be > 0")
    args = [sys.executable if x == "{python}" else x for x in argv]
    start = time.perf_counter()
    # No shell interpolation. This does NOT constrain what a trusted command can do.
    try:
        process = subprocess.Popen(args, cwd=cwd, text=True, encoding="utf-8",
            stdin=subprocess.PIPE if stdin is not None else subprocess.DEVNULL,
            stdout=subprocess.PIPE if capture else None,
            stderr=subprocess.PIPE if capture else None,
            start_new_session=(os.name == "posix"))
    except OSError:
        return {"status": "ERROR", "returncode": None, "duration_ms": 0,
                "reason": "executable-not-found-or-not-executable", "stdout": ""}
    try:
        stdout, _stderr = process.communicate(stdin, timeout=timeout)
        status = "PASS" if process.returncode == 0 else "FAIL"
    except subprocess.TimeoutExpired:
        if os.name == "posix":
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        else:
            process.kill()
        stdout, _stderr = process.communicate()
        status = "TIMEOUT"
    return {"status": status, "returncode": process.returncode,
            "duration_ms": round((time.perf_counter()-start)*1000, 3),
            "stdout": stdout or ""}


def source_fingerprint(paths: list[str], root: Path = ROOT) -> str:
    """Hash explicitly selected implementation/prompt/lock files to reject stale runs."""
    require(isinstance(paths, list) and bool(paths), "Configure source_paths for reproducible evaluation")
    files: dict[str, str] = {}
    root = root.resolve()
    for value in paths:
        path = safe_path(value, root)
        require(path.exists(), f"Evaluation source path does not exist: {value}")
        candidates = [path] if path.is_file() else path.rglob("*")
        for candidate in candidates:
            relative = candidate.relative_to(root)
            if not SOURCE_FINGERPRINT_EXCLUSIONS.isdisjoint(relative.parts) or not candidate.is_file():
                continue
            require(candidate.resolve().is_relative_to(root), "Source symlink escapes repository")
            files[str(relative)] = sha256(candidate)
    require(bool(files), "source_paths selected no source files")
    return digest(files)
