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
import time
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

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
    ignored = {".git", ".harness", "__pycache__", "node_modules", ".venv", "venv", ".pytest_cache", ".next", "dist", "build", "coverage"}
    files: dict[str, str] = {}
    root = root.resolve()
    for value in paths:
        path = safe_path(value, root)
        require(path.exists(), f"Evaluation source path does not exist: {value}")
        candidates = [path] if path.is_file() else path.rglob("*")
        for candidate in candidates:
            relative = candidate.relative_to(root)
            if any(part in ignored for part in relative.parts) or not candidate.is_file():
                continue
            require(candidate.resolve().is_relative_to(root), "Source symlink escapes repository")
            files[str(relative)] = sha256(candidate)
    require(bool(files), "source_paths selected no source files")
    return digest(files)
