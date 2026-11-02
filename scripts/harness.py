#!/usr/bin/env python3
"""Shared Codex / Claude Code harness. Python standard library only."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import re
import shutil
import sys
from _core import (ROOT, ConfigError, command, load_json, positive_int, require,
                   safe_path, sha256, write_json)

CAPABILITIES = {"frontend", "backend", "ai", "rag", "agent", "streaming"}
REQUIRED_GATES = {
    "frontend": {"static", "unit", "build", "e2e"},
    "backend": {"static", "unit", "integration", "build", "security"},
    "ai": {"unit", "contract", "security"},
    "rag": {"retrieval"},
    "agent": {"tools"},
    "streaming": {"integration"},
}
GENERATED = "<!-- Generated from .agents/skills; edit the canonical file, then run sync-skills. -->\n"

class EvidenceFailed(Exception):
    """A configured verification ran but its evidence failed."""


def skill_names(root: Path = ROOT) -> list[str]:
    names = load_json(root / "harness/managed-skills.json")
    require(isinstance(names, list) and bool(names) and len(names) == len(set(names)), "Managed skill list must be nonempty and unique")
    for name in names:
        require(isinstance(name, str) and bool(re.fullmatch(r"kit-[a-z0-9]+(?:-[a-z0-9]+)*", name)) and len(name) <= 64, "Invalid managed skill name")
    return names


def rendered_skill(text: str) -> str:
    require(text.startswith("---\n"), "Skill must start with YAML frontmatter")
    end = text.find("\n---\n", 4)
    require(end >= 0, "Unclosed skill frontmatter")
    return text[:end+5] + "\n" + GENERATED + text[end+5:]


def sync_skills(root: Path = ROOT, check: bool = False) -> list[str]:
    # safe_path resolves symlinks, so compare its results with the same root.
    root = root.resolve()
    drift = []
    for name in skill_names(root):
        source = safe_path(f".agents/skills/{name}", root)
        destination = safe_path(f".claude/skills/{name}", root)
        require((source / "SKILL.md").is_file(), f"Missing canonical skill: {name}")
        source_files = {p.relative_to(source) for p in source.rglob("*") if p.is_file()}
        destination_files = {p.relative_to(destination) for p in destination.rglob("*") if p.is_file()} if destination.exists() else set()
        for relative in sorted(source_files):
            source_file = safe_path(str((source / relative).relative_to(root)), root)
            data = source_file.read_bytes()
            if relative == Path("SKILL.md"):
                data = rendered_skill(data.decode("utf-8")).encode("utf-8")
            target = safe_path(str((destination / relative).relative_to(root)), root)
            if not target.exists() or target.read_bytes() != data:
                drift.append(str(target.relative_to(root)))
                if not check:
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(data)
        extras = destination_files - source_files
        for extra in sorted(extras):
            drift.append(str((destination/extra).relative_to(root)))
        # Never delete unfamiliar files automatically, even inside a managed directory.
        require(check or not extras, f"Unexpected files in generated skill {name}; inspect manually")
    return drift


def project_config(root: Path = ROOT, ready: bool = False) -> dict:
    cfg = load_json(root / "harness/project.json")
    require(isinstance(cfg, dict) and cfg.get("schema_version") == 1, "Unsupported project configuration")
    require(cfg.get("mode") in {"starter", "project"}, "mode must be starter or project")
    caps = cfg.get("capabilities")
    require(isinstance(caps, list) and all(isinstance(c, str) and c in CAPABILITIES for c in caps), "Unknown project capability")
    require(len(caps) == len(set(caps)), "Duplicate project capability")
    require(not ({"rag", "agent"} & set(caps)) or "ai" in caps, "rag/agent requires ai capability")
    commands = cfg.get("commands")
    require(isinstance(commands, list), "commands must be a list")
    ids = set()
    covered = set()
    for cmd in commands:
        require(isinstance(cmd, dict), "Each command must be an object")
        cid = cmd.get("id")
        require(isinstance(cid, str) and bool(re.fullmatch(r"[a-z][a-z0-9-]*", cid)) and cid not in ids, "Command IDs must be unique lowercase identifiers")
        ids.add(cid)
        require(cmd.get("area") in CAPABILITIES | {"integration"}, "Invalid command area")
        require(isinstance(cmd.get("gate"), str) and bool(cmd["gate"]), "Command gate required")
        require(isinstance(cmd.get("argv"), list) and bool(cmd["argv"]) and all(isinstance(x, str) and x for x in cmd["argv"]), "Command argv must be nonempty")
        safe_path(cmd.get("cwd", "."), root)
        positive_int(cmd.get("timeout_seconds"), "timeout_seconds")
        covered.add((cmd["area"], cmd["gate"]))
    ai_cfg = cfg.get("ai_evaluation")
    require(isinstance(ai_cfg, dict) and isinstance(ai_cfg.get("enabled"), bool), "ai_evaluation.enabled must be boolean")
    safe_path(ai_cfg.get("config"), root)
    if ready:
        require(cfg["mode"] == "project", "NOT_CONFIGURED: starter mode validates the kit, not a product")
        require(bool(caps) and bool(commands), "NOT_CONFIGURED: discover capabilities and real verification commands first")
        for cap in caps:
            for gate in REQUIRED_GATES[cap]:
                require((cap, gate) in covered, f"Missing project gate: {cap}/{gate}")
        if "frontend" in caps and "backend" in caps:
            require(("integration", "contract") in covered, "Missing cross-stack API contract gate")
        if "ai" in caps:
            require(ai_cfg["enabled"], "AI capability requires configured evaluation")
    return cfg


def doctor(root: Path = ROOT) -> dict:
    require(sys.version_info >= (3, 10), "Python 3.10+ is required")
    required = ["AGENTS.md", "CLAUDE.md", "README.md", "CODEX_BOOTSTRAP.md", "CLAUDE_BOOTSTRAP.md",
                "docs/SOURCES.md", "docs/PROJECT_CONTEXT.md", "policies/frontend.md", "policies/backend.md",
                "policies/ai.md", "policies/rag.md", "policies/agent.md", "policies/streaming.md"]
    for item in required:
        require((root / item).is_file(), f"Missing file: {item}")
    require("@AGENTS.md" in (root/"CLAUDE.md").read_text(), "CLAUDE.md must import @AGENTS.md")
    require(len((root/"AGENTS.md").read_text().splitlines()) <= 160, "Keep root AGENTS.md small; move details to docs/policies")
    cfg = project_config(root)
    drift = sync_skills(root, check=True)
    require(not drift, "Generated Claude skill drift: " + ", ".join(drift))
    for name in skill_names(root):
        text = (root/".agents/skills"/name/"SKILL.md").read_text()
        require(f"name: {name}\n" in text, f"Skill name/directory mismatch: {name}")
        description = re.search(r"^description: (.+)$", text, re.M)
        require(description is not None and 0 < len(description.group(1)) <= 1024, f"Invalid skill description: {name}")
        require("scripts/harness.py preflight" in text and "AGENTS.md" in text, f"Missing AGENTS preflight: {name}")
    return {"scope": "kit-structure", "status": "PASS", "mode": cfg["mode"], "managed_skills": len(skill_names(root))}


def preflight(root: Path = ROOT, areas: list[str] | None = None, paths: list[str] | None = None) -> None:
    require((root/"AGENTS.md").is_file(), "AGENTS.md missing; stop instead of inventing rules")
    selected = [root/"AGENTS.md", root/"docs/PROJECT_CONTEXT.md"]
    for area in areas or []:
        require(area in CAPABILITIES, "Unknown area")
        selected.append(root / "policies" / f"{area}.md")
    for value in paths or []:
        target = safe_path(value, root)
        parent = target if target.is_dir() else target.parent
        scoped = []
        while parent != root:
            for filename in ("AGENTS.md", "AGENTS.override.md", "CLAUDE.md"):
                candidate = parent / filename
                if candidate.is_file():
                    scoped.append(candidate)
            parent = parent.parent
        selected.extend(reversed(scoped))
    seen = set()
    for path in selected:
        if path in seen:
            continue
        seen.add(path)
        require(path.is_file(), f"Missing instruction file: {path}")
        print(f"\n===== {path.relative_to(root)} | sha256={sha256(path)} =====\n")
        print(path.read_text(encoding="utf-8"))
    print("\nRead the output before editing. This is context delivery, not proof of model compliance.")


def new_change(slug: str, areas: list[str], risk: str, root: Path = ROOT) -> Path:
    require(bool(re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", slug)), "Use a lowercase kebab-case change slug")
    require(bool(areas) and all(area in CAPABILITIES for area in areas), "Select at least one supported area")
    destination = safe_path(f"specs/{slug}", root)
    require(not destination.exists(), "Change already exists; no overwrite performed")
    destination.mkdir(parents=True)
    filenames = ["spec.md", "design.md", "tasks.md", "verification.md"]
    if "ai" in areas or "agent" in areas or "rag" in areas:
        filenames += ["ai-spec.md", "eval-plan.md"]
    for filename in filenames:
        content = (root/"templates/change"/filename).read_text(encoding="utf-8")
        (destination/filename).write_text(content.replace("{{CHANGE_NAME}}", slug), encoding="utf-8")
    write_json(destination/"change.json", {"schema_version": 1, "name": slug, "areas": areas, "risk": risk,
        "approval": {"status": "pending", "reference": None}, "requirements": []})
    return destination


def verify_change(path: Path, cfg: dict, command_results: list[dict], evaluation: dict | None, root: Path = ROOT) -> dict:
    change = load_json(path/"change.json")
    require(isinstance(change, dict), "Invalid change schema")
    require(change.get("schema_version") == 1, "Invalid change schema")
    approval = change.get("approval", {})
    require(isinstance(approval, dict), "Invalid approval")
    require(approval.get("status") == "approved" and isinstance(approval.get("reference"), str) and bool(approval["reference"].strip()), "Change requires a real approval reference; never self-approve for the user")
    requirements = change.get("requirements")
    require(isinstance(requirements, list) and bool(requirements), "No acceptance requirements recorded")
    documents = {}
    areas = change.get("areas")
    require(isinstance(areas, list) and bool(areas) and all(isinstance(a, str) and a in CAPABILITIES for a in areas), "Invalid change areas")
    require(set(areas) <= set(cfg.get("capabilities", [])), "Change areas must be enabled project capabilities")
    names = ["spec.md", "design.md", "tasks.md", "verification.md"]
    if {"ai", "agent", "rag"} & set(areas):
        names += ["ai-spec.md", "eval-plan.md"]
    for name in names:
        text = (path/name).read_text(encoding="utf-8")
        require(bool(text.strip()) and "[TODO]" not in text and "{{" not in text, f"Unresolved or empty template in {name}")
        documents[name] = text
    command_states = {result["id"]: result["status"] for result in command_results}
    ids = set()
    for req in requirements:
        require(isinstance(req, dict), "Requirement must be an object")
        rid = req.get("id")
        require(isinstance(rid, str) and bool(rid) and rid not in ids, "Requirement IDs must be unique")
        ids.add(rid)
        require(isinstance(req.get("description"), str) and bool(req["description"].strip()), "Requirement description required")
        pattern = re.compile(r"(?<![\w.:-])" + re.escape(rid) + r"(?![\w:-]|\.[\w])")
        require(all(pattern.search(documents[name]) for name in ("spec.md", "tasks.md")), f"Requirement {rid} missing from spec/tasks")
        evidence = req.get("evidence")
        require(isinstance(evidence, list) and bool(evidence), f"Requirement {rid} lacks verification evidence")
        for item in evidence:
            require(isinstance(item, dict), f"{rid}: evidence must be an object")
            kind = item.get("kind")
            if kind == "command":
                state = command_states.get(item.get("id"))
                require(state is not None, f"{rid}: referenced command not configured")
                if state != "PASS":
                    raise EvidenceFailed(f"{rid}: referenced command did not pass")
            elif kind == "eval_case":
                rows = [row for row in (evaluation or {}).get("results", []) if row["case_id"] == item.get("id")]
                require(bool(rows), f"{rid}: referenced evaluation case not found")
                if not all(row["passed"] for row in rows):
                    raise EvidenceFailed(f"{rid}: referenced evaluation case did not pass all trials")
            elif kind == "manual":
                evidence_path = safe_path(item.get("path"), root)
                require(evidence_path.is_file() and bool(evidence_path.read_text().strip()), f"{rid}: manual evidence missing")
                require(isinstance(item.get("reviewer"), str) and bool(item["reviewer"].strip()), "Manual evidence needs reviewer attribution")
            else:
                raise ConfigError(f"Unsupported evidence kind: {kind}")
    return {"status": "PASS", "requirements": len(requirements), "note": "Structural traceability only; review verifies evidence relevance and approval authenticity"}


def verify(scope: str, change_path: str | None = None, root: Path = ROOT) -> tuple[dict, int]:
    structure = doctor(root)
    if scope == "kit":
        execution = command(["{python}", "-m", "unittest", "discover", "-s", "tests", "-v"], root, 180)
        execution.pop("stdout", None)
        report = {"scope": "starter-kit-only", "status": execution["status"], "structure": structure, "self_tests": execution,
                  "product_quality": "NOT_EVALUATED", "agent_cli_integration": "NOT_TESTED_BY_THIS_COMMAND"}
        return report, 0 if execution["status"] == "PASS" else 1
    cfg = project_config(root, ready=True)
    results = []
    for cmd in cfg["commands"]:
        print(f"Running gate: {cmd['id']}", flush=True)
        result = command(cmd["argv"], safe_path(cmd.get("cwd", "."), root), cmd["timeout_seconds"])
        result.pop("stdout", None)
        results.append({"id": cmd["id"], "area": cmd["area"], "gate": cmd["gate"], **result})
    evaluation = None
    evaluation_error = None
    if cfg["ai_evaluation"]["enabled"]:
        try:
            from evaluate import evaluate, load_config
            ev_cfg = load_config(safe_path(cfg["ai_evaluation"]["config"], root), root)
            baseline_file = cfg["ai_evaluation"].get("baseline")
            baseline = load_json(safe_path(baseline_file, root)) if baseline_file else None
            evaluation = evaluate(ev_cfg, root, baseline)
        except (ConfigError, OSError, TypeError, ValueError) as exc:
            evaluation_error = {"status": "NOT_CONFIGURED_OR_INVALID", "reason": str(exc)}
    try:
        traceability = verify_change(safe_path(change_path, root), cfg, results, evaluation, root) if change_path else {"status": "NOT_REQUESTED"}
    except EvidenceFailed as exc:
        traceability = {"status": "FAIL", "reason": str(exc)}
    except (ConfigError, OSError, TypeError, ValueError) as exc:
        traceability = {"status": "NOT_CONFIGURED_OR_INVALID", "reason": str(exc)}
    failed = any(result["status"] != "PASS" for result in results) or (evaluation is not None and evaluation["status"] != "PASS") or traceability["status"] == "FAIL"
    code = 1 if failed else 2 if evaluation_error or traceability["status"] == "NOT_CONFIGURED_OR_INVALID" else 0
    report = {"scope": "project", "status": "FAIL" if code == 1 else "NOT_CONFIGURED_OR_INVALID" if code == 2 else "PASS", "commands": results,
              "evaluation": evaluation_error or evaluation, "traceability": traceability,
              "limitations": ["Configured commands and declared evidence only; not proof of full requirement coverage"]}
    return report, code


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("doctor")
    sub.add_parser("mode")
    sync = sub.add_parser("sync-skills")
    sync.add_argument("--check", action="store_true")
    flight = sub.add_parser("preflight")
    flight.add_argument("--area", action="append", choices=sorted(CAPABILITIES))
    flight.add_argument("--path", action="append")
    change = sub.add_parser("new-change")
    change.add_argument("name")
    change.add_argument("--areas", nargs="+", choices=sorted(CAPABILITIES), required=True)
    change.add_argument("--risk", choices=["low", "medium", "high"], default="medium")
    check = sub.add_parser("verify")
    check.add_argument("--scope", choices=["kit", "project"], required=True)
    check.add_argument("--change")
    check.add_argument("--report", default=".harness/reports/verification.json")
    args = parser.parse_args()
    try:
        if args.command == "doctor":
            print(json.dumps(doctor(), ensure_ascii=False, indent=2))
        elif args.command == "mode":
            print(project_config()["mode"])
        elif args.command == "sync-skills":
            drift = sync_skills(check=args.check)
            if args.check and drift:
                print("Skill drift:\n" + "\n".join(drift))
                return 1
            print(f"Skills {'checked' if args.check else 'synchronized'}: {len(skill_names())}")
        elif args.command == "preflight":
            preflight(areas=args.area, paths=args.path)
        elif args.command == "new-change":
            print(new_change(args.name, args.areas, args.risk).relative_to(ROOT))
        elif args.command == "verify":
            try:
                report, code = verify(args.scope, args.change)
            except (ConfigError, OSError, TypeError, ValueError) as exc:
                report, code = {"scope": args.scope, "status": "NOT_CONFIGURED_OR_INVALID", "reason": str(exc)}, 2
            write_json(safe_path(args.report), report)
            print(f"{report['scope']}: {report['status']}")
            if "reason" in report:
                print(report["reason"])
            return code
        return 0
    except (ConfigError, OSError, TypeError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

if __name__ == "__main__":
    raise SystemExit(main())
