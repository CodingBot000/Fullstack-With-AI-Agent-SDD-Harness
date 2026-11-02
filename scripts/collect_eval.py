#!/usr/bin/env python3
"""Opt-in execution of a project-owned evaluation adapter. Never passes answer labels."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import time
import uuid
from _core import (ROOT, ConfigError, command, load_jsonl, require, safe_path, sha256, source_fingerprint, write_json)
from evaluate import load_config, validate_cases


def collect(cfg: dict, root: Path = ROOT) -> dict:
    dataset = safe_path(cfg["dataset"], root)
    before_dataset = sha256(dataset)
    rows = load_jsonl(dataset)
    validate_cases(rows)
    require(len(rows) >= cfg["min_cases"], "Dataset smaller than min_cases")
    adapter = cfg.get("adapter", {})
    require(isinstance(adapter, dict) and bool(adapter.get("argv")), "Project adapter command is not configured")
    metadata = cfg.get("run_metadata", {})
    for field in ("code_ref", "model", "prompt_version", "corpus_version", "tool_policy_version"):
        require(isinstance(metadata.get(field), str) and bool(metadata[field].strip()), f"Set run_metadata.{field}; use explicit not-applicable only when justified")
    results_path = safe_path(cfg["results"], root)
    manifest_path = safe_path(cfg["run_manifest"], root)
    require(len({dataset, results_path, manifest_path}) == 3, "Dataset, results and manifest must be different files")
    # Do not overwrite evidence from an earlier run. A new run uses new paths.
    require(not results_path.exists() and not manifest_path.exists(), "Run output already exists; choose new output paths")
    before_source = source_fingerprint(cfg.get("source_paths"), root)
    run_id = uuid.uuid4().hex
    records = []
    for case in rows:
        for trial in range(1, cfg["repetitions"] + 1):
            # Assertions, reference answers and slice labels never enter this payload.
            payload = {"case_id": case["case_id"], "trial": trial, "input": case["input"]}
            execution = command(adapter["argv"], safe_path(adapter.get("cwd", "."), root),
                adapter.get("timeout_seconds", 60), stdin=json.dumps(payload, ensure_ascii=False) + "\n", capture=True)
            base = {"case_id": case["case_id"], "trial": trial, "run_id": run_id,
                    "harness_wall_ms": execution["duration_ms"]}
            if execution["status"] != "PASS":
                records.append({**base, "status": "error", "error_code": execution["status"], "metrics": {}})
                continue
            try:
                from _core import parse_json
                result = parse_json(execution["stdout"])
                require(isinstance(result, dict) and "output" in result, "Adapter must return an object containing output")
                # Keep only the public adapter fields, not arbitrary stdout/log metadata.
                data = {key: result[key] for key in ("output", "trace", "metrics", "scores", "environment") if key in result}
                require(isinstance(data.get("metrics", {}), dict), "Adapter metrics must be an object")
                records.append({**data, **base, "status": "ok"})
            except (ConfigError, TypeError):
                records.append({**base, "status": "error", "error_code": "INVALID_ADAPTER_OUTPUT", "metrics": {}})
    require(sha256(dataset) == before_dataset, "Dataset changed during collection; discard this run")
    require(source_fingerprint(cfg.get("source_paths"), root) == before_source, "Source changed during collection; discard this run")
    results_path.parent.mkdir(parents=True, exist_ok=True)
    # 'x' protects against an accidental overwrite; raw outputs remain local by default.
    with results_path.open("x", encoding="utf-8") as file:
        for record in records:
            file.write(json.dumps(record, ensure_ascii=False, allow_nan=False) + "\n")
    manifest = {"schema_version": 1, "run_id": run_id, "captured_at_unix": time.time(),
        **{field: metadata[field] for field in ("code_ref", "model", "prompt_version", "corpus_version", "tool_policy_version")},
        "dataset_sha256": before_dataset, "results_sha256": sha256(results_path), "source_sha256": before_source,
        "repetitions": cfg["repetitions"], "adapter_argv": adapter["argv"],
        "failed_trials": sum(record["status"] == "error" for record in records)}
    write_json(manifest_path, manifest)
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="evals/config.json")
    parser.add_argument("--execute-adapter", action="store_true", help="Explicitly authorize execution of the configured project command; it may use network/API credits")
    args = parser.parse_args()
    try:
        require(args.execute_adapter, "Adapter execution is opt-in: inspect its code and pass --execute-adapter")
        config = load_config(safe_path(args.config))
        manifest = collect(config)
        print(f"Captured run {manifest['run_id']}; failed trials={manifest['failed_trials']}")
        return 1 if manifest["failed_trials"] else 0
    except (ConfigError, OSError, TypeError, ValueError) as exc:
        print(f"NOT_CONFIGURED_OR_INVALID: {exc}")
        return 2

if __name__ == "__main__":
    raise SystemExit(main())
