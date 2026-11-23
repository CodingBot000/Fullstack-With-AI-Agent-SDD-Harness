"""Tests of kit mechanics. Temporary commands are not product test recommendations."""
import contextlib
import io
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from _core import ConfigError, ROOT, load_json, write_json
from harness import (EvidenceFailed, REQUIRED_GATES, doctor, new_change, preflight, project_config,
                     skill_names, sync_skills, verify, verify_change)

class HarnessTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)/"repo"
        self.root.mkdir()
        # Copy only kit fixtures, never an adopting product's source/customer data/dependencies.
        required = ["AGENTS.md", "CLAUDE.md", "README.md", "CODEX_BOOTSTRAP.md", "CLAUDE_BOOTSTRAP.md",
                    "docs/SOURCES.md", "docs/PROJECT_CONTEXT.md", "harness/managed-skills.json"]
        required += [f"policies/{area}.md" for area in ("frontend", "backend", "ai", "rag", "agent", "streaming")]
        required += [str(p.relative_to(ROOT)) for p in (ROOT/"templates/change").glob("*.md")]
        for name in load_json(ROOT/"harness/managed-skills.json"):
            for parent in (".agents/skills", ".claude/skills"):
                for file in (ROOT/parent/name).rglob("*"):
                    if file.is_file():
                        required.append(str(file.relative_to(ROOT)))
        for relative in required:
            target = self.root/relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT/relative, target)
        write_json(self.root/"harness/project.json", {"schema_version":1, "mode":"starter", "capabilities":[],
                   "commands":[], "ai_evaluation":{"enabled":False,"config":"evals/config.json","baseline":None}})

    def write_cfg(self,cfg): write_json(self.root/"harness/project.json",cfg)

    def copy_cli(self):
        shutil.copytree(ROOT / "scripts", self.root / "scripts", ignore=shutil.ignore_patterns("__pycache__"))

    def run_cli(self, *args):
        return subprocess.run(
            [sys.executable, "scripts/harness.py", *args], cwd=self.root,
            capture_output=True, text=True, timeout=15,
        )

    def frontend_cfg(self, failure=False):
        cfg=load_json(self.root/"harness/project.json")
        cfg.update(mode="project",capabilities=["frontend"])
        cfg["commands"]=[{"id":f"test-{gate}","area":"frontend","gate":gate,
            "argv":["{python}","-c","raise SystemExit(1)" if failure else "raise SystemExit(0)"],"cwd":".","timeout_seconds":3}
            for gate in sorted(REQUIRED_GATES["frontend"])]
        self.write_cfg(cfg); return cfg

    def test_root_structure_passes(self): self.assertEqual(doctor(self.root)["status"],"PASS")

    def test_sync_skills_accepts_symlinked_root(self):
        alias = self.root.parent / "repo-alias"
        try:
            alias.symlink_to(self.root, target_is_directory=True)
        except (OSError, NotImplementedError) as exc:
            self.skipTest(f"Directory symlinks unavailable: {exc}")
        self.assertEqual(sync_skills(alias, check=True), [])
        self.assertEqual(sync_skills(alias), [])

    def test_starter_is_not_product_ready(self):
        with self.assertRaises(ConfigError): project_config(self.root,ready=True)

    def test_missing_product_gates_rejected(self):
        cfg=load_json(self.root/"harness/project.json"); cfg.update(mode="project",capabilities=["frontend"]); self.write_cfg(cfg)
        with self.assertRaises(ConfigError): project_config(self.root,ready=True)

    def test_capability_dependencies_checked(self):
        cfg=load_json(self.root/"harness/project.json"); cfg["capabilities"]=["rag"]; self.write_cfg(cfg)
        with self.assertRaises(ConfigError): project_config(self.root)

    def test_command_path_escape_rejected(self):
        cfg=self.frontend_cfg(); cfg["commands"][0]["cwd"]="../outside"; self.write_cfg(cfg)
        with self.assertRaises(ConfigError): project_config(self.root)

    def test_frontend_required_gates_registered(self):
        self.frontend_cfg(); self.assertEqual(project_config(self.root,True)["mode"],"project")

    def test_project_command_failure_is_failure(self):
        self.frontend_cfg(failure=True)
        report,code=verify("project",root=self.root)
        self.assertEqual(code,1); self.assertEqual(report["status"],"FAIL")

    def test_project_without_change_does_not_claim_traceability(self):
        self.frontend_cfg()
        report,code=verify("project",root=self.root)
        self.assertEqual(code,0); self.assertEqual(report["traceability"]["status"],"NOT_REQUESTED")

    def test_skill_drift_detected_and_repaired(self):
        target=self.root/".claude/skills/kit-onboard/SKILL.md"; target.write_text("bad")
        self.assertTrue(sync_skills(self.root,check=True))
        sync_skills(self.root); self.assertEqual(sync_skills(self.root,check=True),[])

    def test_unmanaged_skill_preserved(self):
        custom=self.root/".claude/skills/user-custom/SKILL.md"; custom.parent.mkdir(); custom.write_text("preserve me")
        sync_skills(self.root); self.assertEqual(custom.read_text(),"preserve me")

    def test_extra_generated_file_not_silently_deleted(self):
        extra=self.root/".claude/skills/kit-onboard/custom.txt"; extra.write_text("preserve")
        with self.assertRaises(ConfigError): sync_skills(self.root)
        self.assertTrue(extra.exists())

    def test_claude_import_is_required(self):
        (self.root/"CLAUDE.md").write_text("Missing import")
        with self.assertRaises(ConfigError): doctor(self.root)

    def test_each_skill_requires_preflight(self):
        for name in skill_names(self.root):
            text=(self.root/".agents/skills"/name/"SKILL.md").read_text()
            self.assertIn("scripts/harness.py preflight",text)
            self.assertIn("AGENTS.md",text)

    def test_new_change_includes_ai_docs(self):
        folder=new_change("synthetic-change",["frontend","ai"],"medium",self.root)
        self.assertTrue((folder/"ai-spec.md").exists())
        self.assertEqual(load_json(folder/"change.json")["approval"]["status"],"pending")

    def test_new_change_cannot_overwrite(self):
        new_change("synthetic-change",["frontend"],"low",self.root)
        with self.assertRaises(ConfigError): new_change("synthetic-change",["frontend"],"low",self.root)

    def test_new_change_slug_escape_rejected(self):
        with self.assertRaises(ConfigError): new_change("../outside",["ai"],"low",self.root)

    def test_preflight_prints_rules_and_selected_policy(self):
        output=io.StringIO()
        with contextlib.redirect_stdout(output): preflight(self.root,["backend"],[])
        self.assertIn("AGENTS.md",output.getvalue()); self.assertIn("policies/backend.md",output.getvalue())

    def test_traceability_requires_real_approval_reference(self):
        folder=new_change("synthetic-change",["frontend"],"low",self.root)
        with self.assertRaises(ConfigError): verify_change(folder,{"capabilities":["frontend","ai","agent"]},[],None,self.root)

    def test_traceability_rejects_missing_command_evidence(self):
        folder=new_change("synthetic-change",["frontend"],"low",self.root)
        change=load_json(folder/"change.json")
        change["approval"]={"status":"approved","reference":"test-only-approval"}
        change["requirements"]=[{"id":"req-test","description":"synthetic requirement","evidence":[{"kind":"command","id":"test-static"}]}]
        write_json(folder/"change.json",change)
        for name in ("spec.md","design.md","tasks.md","verification.md"): (folder/name).write_text("req-test synthetic evidence")
        with self.assertRaises(ConfigError): verify_change(folder,{"capabilities":["frontend","ai","agent"]},[],None,self.root)
        result=verify_change(folder,{"capabilities":["frontend","ai","agent"]},[{"id":"test-static","status":"PASS"}],None,self.root)
        self.assertEqual(result["status"],"PASS")

    def test_ai_documents_must_be_complete(self):
        folder = new_change("synthetic-ai", ["agent"], "medium", self.root)
        change = load_json(folder / "change.json")
        change["approval"] = {"status": "approved", "reference": "fixture-only"}
        change["requirements"] = [{"id": "req-test", "description": "fixture", "evidence": [{"kind": "command", "id": "test-static"}]}]
        write_json(folder / "change.json", change)
        for name in ("spec.md", "design.md", "tasks.md", "verification.md"):
            (folder / name).write_text("req-test fixture")
        results = [{"id": "test-static", "status": "PASS"}]
        with self.assertRaises(ConfigError): verify_change(folder, {"capabilities":["frontend","ai","agent"]}, results, None, self.root)
        (folder / "ai-spec.md").write_text("fixture")
        (folder / "eval-plan.md").unlink()
        with self.assertRaises(OSError): verify_change(folder, {"capabilities":["frontend","ai","agent"]}, results, None, self.root)
        (folder / "eval-plan.md").write_text("fixture")
        self.assertEqual(verify_change(folder, {"capabilities":["frontend","ai","agent"]}, results, None, self.root)["status"], "PASS")

    def test_new_project_cli_flow_and_failed_evidence(self):
        # Synthetic fixture: no product, real approval, external service, or model.
        self.copy_cli()
        run = self.run_cli
        self.assertEqual(run("verify", "--scope", "project").returncode, 2)
        self.assertEqual(run("new-change", "fixture", "--areas", "frontend").returncode, 0)
        folder = self.root / "specs/fixture"
        change = load_json(folder / "change.json")
        change["approval"] = {"status": "approved", "reference": "synthetic fixture only"}
        change["requirements"] = [{"id": "req-test", "description": "fixture", "evidence": [{"kind": "command", "id": "test-static"}]}]
        write_json(folder / "change.json", change)
        for name in ("spec.md", "design.md", "tasks.md"):
            (folder / name).write_text("req-test fixture")
        self.frontend_cfg()
        self.assertEqual(run("verify", "--scope", "project").returncode, 0)
        project_report = self.root / ".harness/reports/project.json"
        self.assertEqual(load_json(project_report)["traceability"]["status"], "NOT_REQUESTED")
        (folder / "verification.md").write_text("req-test passed in the product report")
        change_args = (
            "verify", "--scope", "project", "--change", "specs/fixture",
            "--report", ".harness/reports/change.json",
        )
        self.assertEqual(run(*change_args).returncode, 0)
        self.assertEqual(load_json(project_report)["traceability"]["status"], "NOT_REQUESTED")
        self.frontend_cfg(failure=True)
        failed = run(*change_args)
        self.assertEqual(failed.returncode, 1, failed.stdout + failed.stderr)
        report = load_json(self.root / ".harness/reports/change.json")
        self.assertEqual(report["status"], "FAIL")
        self.assertEqual(report["traceability"]["status"], "FAIL")
        (folder / "spec.md").write_text("[TODO]")
        mixed = run(*change_args)
        self.assertEqual(mixed.returncode, 1)
        report = load_json(self.root / ".harness/reports/change.json")
        self.assertEqual(report["traceability"]["status"], "NOT_CONFIGURED_OR_INVALID")
        self.assertTrue(any(item["status"] == "FAIL" for item in report["commands"]))
        self.frontend_cfg()
        self.assertEqual(run(*change_args).returncode, 2)

    def test_kit_scope_isolated_from_product_tests_and_report(self):
        self.copy_cli()
        suites = self.root / "harness/tests"
        suites.mkdir()
        shutil.copyfile(ROOT / "harness/tests/run.py", suites / "run.py")
        fixture = (
            "import unittest\n"
            "class Fixture(unittest.TestCase):\n"
            "    def test_fixture(self):\n"
            "        self.assertEqual(1 + 1, 2)\n"
        )
        for source in (ROOT / "harness/tests").glob("test_*.py"):
            (suites / source.name).write_text(fixture, encoding="utf-8")
        product = self.root / "tests"
        product.mkdir()
        (product / "test_product.py").write_text("raise RuntimeError('Product test was imported')\n")

        kit = self.run_cli("verify", "--scope", "kit")
        self.assertEqual(kit.returncode, 0, kit.stdout + kit.stderr)
        kit_report = (self.root / ".harness/reports/kit.json").read_bytes()
        self.assertEqual(self.run_cli("verify", "--scope", "project").returncode, 2)
        self.assertEqual((self.root / ".harness/reports/kit.json").read_bytes(), kit_report)
        self.assertEqual(load_json(self.root / ".harness/reports/project.json")["scope"], "project")

        required = suites / "test_core.py"
        required.write_text("", encoding="utf-8")
        empty = self.run_cli("verify", "--scope", "kit")
        self.assertEqual(empty.returncode, 1, empty.stdout + empty.stderr)
        self.assertIn("No tests discovered", empty.stderr)
        required.unlink()
        missing = self.run_cli("verify", "--scope", "kit")
        self.assertEqual(missing.returncode, 1, missing.stdout + missing.stderr)
        self.assertIn("Missing required kit test suite", missing.stderr)

    def test_report_cannot_overwrite_project_config_or_start_gates(self):
        self.copy_cli()
        cfg = self.frontend_cfg()
        cfg["commands"][0]["argv"] = [
            "{python}", "-c", "from pathlib import Path; Path('gate-started').touch()",
        ]
        self.write_cfg(cfg)
        config = self.root / "harness/project.json"
        original = config.read_bytes()
        for path, message in (
            ("./harness/project.json", "Report path must differ from input files"),
            ("harness/project.json/report.json", "Report parent is not a directory"),
        ):
            with self.subTest(path=path):
                result = self.run_cli("verify", "--scope", "project", "--report", path)
                self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
                self.assertIn(message, result.stderr)
                self.assertFalse((self.root / "gate-started").exists())
                self.assertEqual(config.read_bytes(), original)
        result = self.run_cli(
            "verify", "--scope", "project", "--change", "specs/first", "--report", "specs/first",
        )
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertFalse((self.root / "specs/first").exists())
        self.assertFalse((self.root / "gate-started").exists())

        managed_skills = self.root / "harness/managed-skills.json"
        managed_skills.unlink()
        result = self.run_cli("verify", "--scope", "kit", "--report", "harness/managed-skills.json")
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertFalse(managed_skills.exists())

    def test_evaluation_evidence_distinguishes_failed_and_missing(self):
        folder = new_change("synthetic-eval", ["ai"], "low", self.root)
        change = load_json(folder / "change.json")
        change["approval"] = {"status": "approved", "reference": "fixture-only"}
        change["requirements"] = [{"id": "req-test", "description": "fixture", "evidence": [{"kind": "eval_case", "id": "case-test"}]}]
        write_json(folder / "change.json", change)
        for name in ("spec.md", "design.md", "tasks.md", "verification.md", "ai-spec.md", "eval-plan.md"):
            (folder / name).write_text("req-test fixture")
        with self.assertRaises(ConfigError): verify_change(folder, {"capabilities":["frontend","ai","agent"]}, [], {"results": []}, self.root)
        with self.assertRaises(EvidenceFailed):
            verify_change(folder, {"capabilities":["frontend","ai","agent"]}, [], {"results": [{"case_id": "case-test", "passed": True}, {"case_id": "case-test", "passed": False}]}, self.root)

    def test_evaluation_misconfiguration_preserves_command_failures(self):
        cfg = self.frontend_cfg(failure=True)
        cfg["ai_evaluation"]["enabled"] = True
        self.write_cfg(cfg)
        report, code = verify("project", root=self.root)
        self.assertEqual(code, 1)
        self.assertEqual(report["evaluation"]["status"], "NOT_CONFIGURED_OR_INVALID")
        self.assertTrue(any(item["status"] == "FAIL" for item in report["commands"]))
        cfg = self.frontend_cfg()
        cfg["ai_evaluation"]["enabled"] = True
        self.write_cfg(cfg)
        self.assertEqual(verify("project", root=self.root)[1], 2)

    def test_change_areas_and_exact_requirement_ids(self):
        self.frontend_cfg()
        folder = new_change("fixture-areas", ["ai"], "low", self.root)
        change = load_json(folder / "change.json")
        change["approval"] = {"status": "approved", "reference": "fixture"}
        change["requirements"] = [{"id": "REQ-1", "description": "fixture", "evidence": [{"kind": "command", "id": "test-static"}]}]
        write_json(folder / "change.json", change)
        for name in ("spec.md", "design.md", "tasks.md", "verification.md", "ai-spec.md", "eval-plan.md"):
            (folder / name).write_text("REQ-10 fixture")
        report, code = verify("project", "specs/fixture-areas", self.root)
        self.assertEqual(code, 2)
        self.assertIn("capabilities", report["traceability"]["reason"])
        change["areas"] = ["frontend"]
        write_json(folder / "change.json", change)
        report, code = verify("project", "specs/fixture-areas", self.root)
        self.assertEqual(code, 2)
        self.assertIn("missing from spec/tasks", report["traceability"]["reason"])
        for name in ("spec.md", "tasks.md"): (folder / name).write_text("REQ-1.1 fixture")
        self.assertEqual(verify("project", "specs/fixture-areas", self.root)[1], 2)
        for name in ("spec.md", "tasks.md"): (folder / name).write_text("REQ-1 fixture")
        self.assertEqual(verify("project", "specs/fixture-areas", self.root)[1], 0)

    def test_malformed_change_objects_report_invalid(self):
        self.frontend_cfg()
        folder = new_change("fixture-malformed", ["frontend"], "low", self.root)
        original = load_json(folder / "change.json")
        for bad in ({**original, "approval": None},
                    {**original, "approval": {"status":"approved", "reference":"fixture"}, "requirements": [None]},
                    {**original, "approval": {"status":"approved", "reference":"fixture"}, "requirements": [{"id":"REQ-1", "description":"x", "evidence":[None]}]}):
            write_json(folder / "change.json", bad)
            for name in ("spec.md", "design.md", "tasks.md", "verification.md"): (folder / name).write_text("REQ-1 fixture")
            report, code = verify("project", "specs/fixture-malformed", self.root)
            self.assertEqual(code, 2)
            self.assertEqual(report["traceability"]["status"], "NOT_CONFIGURED_OR_INVALID")
