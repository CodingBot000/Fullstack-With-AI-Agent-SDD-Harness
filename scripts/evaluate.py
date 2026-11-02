#!/usr/bin/env python3
"""Evaluate captured application runs; no model calls and no fabricated scores."""
from __future__ import annotations
import argparse
import math
from pathlib import Path
from typing import Any
from _core import (ROOT, ConfigError, digest, load_json, load_jsonl, nonnegative,
                   positive_int, rate, require, safe_path, sha256, source_fingerprint, write_json)

OPS = {"equals", "contains", "not_contains", "tool_called", "tool_not_called",
       "recall_at_k", "citations_subset", "score_at_least"}


def pointer(document: Any, path: str) -> Any:
    require(isinstance(path, str) and (path == "" or path.startswith("/")), "Use an RFC 6901 JSON pointer")
    node = document
    if path == "":
        return node
    for token in path[1:].split("/"):
        token = token.replace("~1", "/").replace("~0", "~")
        if isinstance(node, dict):
            if token not in node:
                raise KeyError(path)
            node = node[token]
        elif isinstance(node, list) and token.isdigit():
            node = node[int(token)]
        else:
            raise KeyError(path)
    return node


def json_equal(left: Any, right: Any) -> bool:
    # Python otherwise considers True == 1. Preserve JSON type semantics.
    if isinstance(left, bool) or isinstance(right, bool):
        return type(left) is type(right) and left == right
    if isinstance(left, dict) and isinstance(right, dict):
        return left.keys() == right.keys() and all(json_equal(left[k], right[k]) for k in left)
    if isinstance(left, list) and isinstance(right, list):
        return len(left) == len(right) and all(json_equal(a, b) for a, b in zip(left, right))
    return type(left) is type(right) and left == right or (
        type(left) in (int, float) and type(right) in (int, float) and left == right)


def subset(expected: Any, actual: Any) -> bool:
    if isinstance(expected, dict):
        return isinstance(actual, dict) and all(k in actual and subset(v, actual[k]) for k, v in expected.items())
    return json_equal(expected, actual)


def validate_assertion(check: dict[str, Any]) -> None:
    require(isinstance(check, dict), "Each assertion must be an object")
    op = check.get("op")
    require(op in OPS, f"Unsupported assertion operator: {op}")
    require(isinstance(check.get("critical", False), bool), "critical must be boolean")
    if op in {"equals", "contains", "not_contains"}:
        require("expected" in check, f"{op}: expected is required")
        path = check.get("path")
        require(isinstance(path, str) and path.startswith("/"), f"{op}: JSON pointer path required")
    if op in {"tool_called", "tool_not_called"}:
        require(isinstance(check.get("name"), str) and bool(check["name"]), "Tool name is required")
        if "arguments" in check:
            require(isinstance(check["arguments"], dict), "Tool arguments expectation must be an object")
    if op == "recall_at_k":
        expected = check.get("expected")
        require(isinstance(expected, list) and bool(expected) and all(isinstance(x, str) for x in expected), "Recall needs nonempty relevant document IDs")
        require(len(set(expected)) == len(expected), "Relevant document IDs must be unique")
        positive_int(check.get("k"), "recall.k")
        rate(check.get("min"), "recall.min")
    if op == "score_at_least":
        require(isinstance(check.get("metric"), str) and bool(check["metric"]), "External score metric is required")
        rate(check.get("min"), "score.min")


def validate_cases(rows: list[dict[str, Any]]) -> None:
    require(bool(rows), "Evaluation dataset is empty")
    ids = set()
    for row in rows:
        cid = row.get("case_id")
        require(isinstance(cid, str) and bool(cid) and cid not in ids, "Case IDs must be nonempty and unique")
        ids.add(cid)
        require("input" in row, f"{cid}: input required")
        require(isinstance(row.get("slice"), str) and bool(row["slice"]), f"{cid}: slice required")
        checks = row.get("assertions")
        require(isinstance(checks, list) and bool(checks), f"{cid}: at least one assertion is required")
        for check in checks:
            validate_assertion(check)


def grade(check: dict[str, Any], record: dict[str, Any]) -> tuple[bool, float | None]:
    """False on missing evidence. Unsupported operators are configuration errors."""
    validate_assertion(check)
    op = check["op"]
    try:
        if op in {"equals", "contains", "not_contains"}:
            actual = pointer(record, check["path"])
            expected = check["expected"]
            if op == "equals":
                return json_equal(actual, expected), None
            if isinstance(actual, str) and isinstance(expected, str):
                contains = expected in actual
            elif isinstance(actual, list):
                contains = any(json_equal(expected, value) for value in actual)
            else:
                return False, None
            return (contains if op == "contains" else not contains), None
        trace = record.get("trace", {})
        if not isinstance(trace, dict):
            return False, None
        if op in {"tool_called", "tool_not_called"}:
            calls = trace.get("tool_calls")
            if not isinstance(calls, list):
                return False, None
            matches = [call for call in calls if isinstance(call, dict) and call.get("name") == check["name"]]
            if op == "tool_not_called":
                return not matches, None
            return any(subset(check.get("arguments", {}), call.get("arguments", {})) for call in matches), None
        if op == "recall_at_k":
            retrieved = trace.get("retrieved_ids")
            if not isinstance(retrieved, list) or not all(isinstance(x, str) for x in retrieved):
                return False, None
            relevant = set(check["expected"])
            score = len(relevant.intersection(retrieved[:check["k"]])) / len(relevant)
            return score >= check["min"], score
        if op == "citations_subset":
            citations, retrieved = trace.get("citations"), trace.get("retrieved_ids")
            if not isinstance(citations, list) or not citations or not isinstance(retrieved, list):
                return False, None
            if not all(isinstance(x, str) for x in citations + retrieved):
                return False, None
            return set(citations).issubset(retrieved), None
        if op == "score_at_least":
            score = record.get("scores", {}).get(check["metric"], {})
            if not isinstance(score, dict) or not score.get("grader") or not score.get("version"):
                return False, None
            number = rate(score.get("value"), "external score")
            return number >= check["min"], number
    except (KeyError, IndexError, TypeError, AttributeError, ConfigError):
        return False, None
    return False, None


def load_config(path: Path, root: Path = ROOT) -> dict[str, Any]:
    cfg = load_json(path)
    require(isinstance(cfg, dict) and cfg.get("schema_version") == 1, "Unsupported eval configuration schema")
    for name in ("dataset", "results", "run_manifest"):
        safe_path(cfg.get(name), root)
    source_fingerprint(cfg.get("source_paths"), root)
    positive_int(cfg.get("repetitions"), "repetitions")
    positive_int(cfg.get("min_cases"), "min_cases")
    gates = cfg.get("gates")
    require(isinstance(gates, dict), "gates required")
    rate(gates.get("min_pass_rate"), "gates.min_pass_rate")
    for name in ("max_p95_latency_ms", "max_mean_cost_usd"):
        if gates.get(name) is not None:
            nonnegative(gates[name], name)
    if gates.get("max_pass_rate_drop") is not None:
        rate(gates["max_pass_rate_drop"], "max_pass_rate_drop")
    slices = gates.get("required_slices", {})
    require(isinstance(slices, dict), "required_slices must be an object")
    for name, values in slices.items():
        require(bool(name) and isinstance(values, dict), "Invalid required slice")
        positive_int(values.get("min_cases"), "slice.min_cases")
        rate(values.get("min_pass_rate"), "slice.min_pass_rate")
    return cfg


def evaluate(cfg: dict[str, Any], root: Path = ROOT, baseline: dict[str, Any] | None = None) -> dict[str, Any]:
    dataset_path, records_path, manifest_path = (safe_path(cfg[name], root) for name in ("dataset", "results", "run_manifest"))
    cases, records, manifest = load_jsonl(dataset_path), load_jsonl(records_path), load_json(manifest_path)
    validate_cases(cases)
    require(len(cases) >= cfg["min_cases"], "Dataset smaller than configured min_cases")
    dataset_hash = sha256(dataset_path)
    require(isinstance(manifest, dict), "Run manifest must be an object")
    require(manifest.get("dataset_sha256") == dataset_hash, "Dataset changed since run capture")
    require(manifest.get("results_sha256") == sha256(records_path), "Results changed since run capture")
    for field in ("run_id", "code_ref", "model", "prompt_version", "corpus_version", "tool_policy_version"):
        require(isinstance(manifest.get(field), str) and bool(manifest[field].strip()), f"Run manifest missing {field}")
    require(manifest.get("repetitions") == cfg["repetitions"], "Run repetitions mismatch")
    require(manifest.get("source_sha256") == source_fingerprint(cfg.get("source_paths"), root), "Source changed since capture; rerun the evaluation")
    for field, expected in cfg.get("run_metadata", {}).items():
        if expected is not None:
            require(manifest.get(field) == expected, f"Run metadata mismatch: {field}")
    expected_keys = {(case["case_id"], n) for case in cases for n in range(1, cfg["repetitions"] + 1)}
    indexed = {}
    for record in records:
        require(isinstance(record.get("case_id"), str), "Result case_id required")
        positive_int(record.get("trial"), "trial")
        key = (record["case_id"], record["trial"])
        require(key in expected_keys and key not in indexed, "Duplicate, unknown, or out-of-range result")
        require(record.get("status") in {"ok", "error"}, "Result status must be ok or error")
        require(record.get("run_id") == manifest["run_id"], "Mixed run IDs in results")
        indexed[key] = record
    require(set(indexed) == expected_keys, "Missing evaluation trials; cannot silently exclude failures")
    grades, slice_rows, critical_failures = [], {}, 0
    for case in cases:
        for trial in range(1, cfg["repetitions"]+1):
            record = indexed[(case["case_id"], trial)]
            checks = []
            for index, assertion in enumerate(case["assertions"]):
                passed, value = grade(assertion, record) if record["status"] == "ok" else (False, None)
                if assertion.get("critical", False) and not passed:
                    critical_failures += 1
                checks.append({"index": index, "op": assertion["op"], "passed": passed, "value": value})
            passed = record["status"] == "ok" and all(item["passed"] for item in checks)
            grades.append({"case_id": case["case_id"], "trial": trial, "slice": case["slice"], "passed": passed, "checks": checks})
            slice_rows.setdefault(case["slice"], []).append(passed)
    pass_rate = sum(item["passed"] for item in grades)/len(grades)
    per_slice = {name: {"trials": len(values), "cases": sum(case["slice"] == name for case in cases),
                       "pass_rate": sum(values)/len(values)} for name, values in slice_rows.items()}
    measurements = {}
    for metric in ("latency_ms", "ttft_ms", "cost_usd", "input_tokens", "output_tokens"):
        values = []
        for record in records:
            metrics = record.get("metrics", {})
            require(isinstance(metrics, dict), "metrics must be an object")
            if metrics.get(metric) is not None:
                values.append(nonnegative(metrics[metric], metric))
        values.sort()
        measurements[metric] = {"observed": len(values), "total": len(records),
            "mean": sum(values)/len(values) if values else None,
            "p95": values[max(0, math.ceil(len(values)*0.95)-1)] if values else None}
    gates, failures = cfg["gates"], []
    if pass_rate < gates["min_pass_rate"]:
        failures.append("overall-pass-rate")
    if critical_failures:
        failures.append("critical-assertion-failed")
    for name, limits in gates.get("required_slices", {}).items():
        actual = per_slice.get(name)
        if actual is None or actual["cases"] < limits["min_cases"] or actual["pass_rate"] < limits["min_pass_rate"]:
            failures.append(f"slice:{name}")
    for gate, metric, statistic in (("max_p95_latency_ms", "latency_ms", "p95"), ("max_mean_cost_usd", "cost_usd", "mean")):
        if gates.get(gate) is not None:
            observed = measurements[metric]
            if observed["observed"] != len(records) or observed[statistic] is None or observed[statistic] > gates[gate]:
                failures.append(gate)
    grader_source = digest({name: sha256(Path(__file__).resolve().with_name(name))
                            for name in ("evaluate.py", "_core.py")})
    contract_hash = digest({"grader_source_sha256": grader_source, "dataset_sha256": dataset_hash, "repetitions": cfg["repetitions"], "min_cases": cfg["min_cases"], "gates": {k: v for k, v in gates.items() if k != "max_pass_rate_drop"}, "grader_version": "starter-1"})
    comparison = None
    if gates.get("max_pass_rate_drop") is not None:
        require(baseline is not None, "Regression budget configured but no baseline report provided")
    if baseline is not None:
        require(baseline.get("contract_sha256") == contract_hash, "Baseline dataset, repetitions, or grading contract differs")
        old_rate = rate(baseline.get("pass_rate"), "baseline.pass_rate")
        delta = pass_rate - old_rate
        comparison = {"baseline_run_id": baseline.get("run_id"), "pass_rate_delta": delta,
                      "note": "Descriptive paired-dataset comparison, not a significance test"}
        if gates.get("max_pass_rate_drop") is not None and -delta > gates["max_pass_rate_drop"]:
            failures.append("pass-rate-regression")
    return {"schema_version": 1, "scope": "ai-evaluation", "status": "FAIL" if failures else "PASS",
            "run_id": manifest["run_id"], "dataset_sha256": dataset_hash, "contract_sha256": contract_hash,
            "grader_source_sha256": grader_source,
            "cases": len(cases), "trials": len(grades), "pass_rate": pass_rate,
            "critical_failures": critical_failures, "slices": per_slice, "measurements": measurements,
            "gate_failures": failures, "comparison": comparison, "results": grades,
            "limitations": ["Only configured assertions are evaluated", "Citation membership is not factuality",
                            "External judge scores require independent calibration", "No statistical confidence claim"]}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="evals/config.json")
    parser.add_argument("--report", default=".harness/reports/eval.json")
    parser.add_argument("--baseline")
    args = parser.parse_args()
    try:
        config = load_config(safe_path(args.config))
        baseline = load_json(safe_path(args.baseline)) if args.baseline else None
        report = evaluate(config, baseline=baseline)
        code = 0 if report["status"] == "PASS" else 1
    except (ConfigError, OSError, TypeError, ValueError) as exc:
        report = {"scope": "ai-evaluation", "status": "NOT_CONFIGURED_OR_INVALID", "reason": str(exc)}
        code = 2
    write_json(safe_path(args.report), report)
    print(f"{report['scope']}: {report['status']}")
    if "reason" in report:
        print(report["reason"])
    return code

if __name__ == "__main__":
    raise SystemExit(main())
