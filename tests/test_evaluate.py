"""All fixtures are synthetic evaluator tests, never a model benchmark."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from _core import ConfigError, load_json, sha256, source_fingerprint, write_json
from evaluate import evaluate, grade, load_config, pointer, validate_cases


class EvalFixture(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        (self.root/"source.py").write_text("# synthetic evaluator fixture\n")
        self.cases=[{"case_id":"case-a","input":{"text":"a"},"slice":"core","assertions":[{"op":"equals","path":"/output/text","expected":"a"}]},
                    {"case_id":"case-b","input":{"text":"b"},"slice":"edge","assertions":[{"op":"equals","path":"/output/text","expected":"b"}]}]
        self.records=[{"case_id":case["case_id"],"trial":trial,"run_id":"synthetic-run","status":"ok","output":case["input"],
                       "trace":{"tool_calls":[],"retrieved_ids":[],"citations":[]},
                       "metrics":{"latency_ms":float(trial),"cost_usd":0.0}} for case in self.cases for trial in (1,2)]
        self.cfg={"schema_version":1,"dataset":"data.jsonl","results":"results.jsonl","run_manifest":"manifest.json",
                  "source_paths":["source.py"],"repetitions":2,"min_cases":2,
                  "gates":{"min_pass_rate":1.0,"max_p95_latency_ms":None,"max_mean_cost_usd":None,"max_pass_rate_drop":None,"required_slices":{}}}
        self.manifest={"run_id":"synthetic-run","code_ref":"fixture","model":"no-real-model","prompt_version":"fixture",
                       "corpus_version":"not-applicable","tool_policy_version":"fixture","repetitions":2}
        self.persist()

    def persist(self):
        for name,rows in (("data.jsonl",self.cases),("results.jsonl",self.records)):
            (self.root/name).write_text("".join(json.dumps(row)+"\n" for row in rows))
        self.manifest.update(dataset_sha256=sha256(self.root/"data.jsonl"),results_sha256=sha256(self.root/"results.jsonl"),
                             source_sha256=source_fingerprint(["source.py"],self.root))
        write_json(self.root/"manifest.json",self.manifest)
        write_json(self.root/"config.json",self.cfg)

    def run_eval(self):
        cfg=load_config(self.root/"config.json",self.root)
        return evaluate(cfg,self.root)


class EvaluationTests(EvalFixture):
    def test_valid_capture_passes(self):
        result=self.run_eval()
        self.assertEqual(result["status"],"PASS")
        self.assertEqual(result["cases"],2); self.assertEqual(result["trials"],4)
        self.assertEqual(result["measurements"]["ttft_ms"]["observed"],0)
        self.assertIsNone(result["measurements"]["ttft_ms"]["mean"])

    def test_wrong_output_fails(self):
        self.records[0]["output"]={"text":"wrong"}; self.persist()
        result=self.run_eval(); self.assertEqual(result["status"],"FAIL")
        self.assertEqual(result["pass_rate"],0.75)

    def test_failed_trial_cannot_be_dropped(self):
        self.records.pop(); self.persist()
        with self.assertRaises(ConfigError): self.run_eval()

    def test_duplicate_trial_rejected(self):
        self.records.append(copy.deepcopy(self.records[0])); self.persist()
        with self.assertRaises(ConfigError): self.run_eval()

    def test_unknown_case_rejected(self):
        self.records[0]["case_id"]="unknown"; self.persist()
        with self.assertRaises(ConfigError): self.run_eval()

    def test_out_of_range_trial_rejected(self):
        self.records[0]["trial"]=3; self.persist()
        with self.assertRaises(ConfigError): self.run_eval()

    def test_mixed_runs_rejected(self):
        self.records[0]["run_id"]="another-run"; self.persist()
        with self.assertRaises(ConfigError): self.run_eval()

    def test_empty_dataset_rejected(self):
        self.cases=[]; self.persist()
        with self.assertRaises(ConfigError): self.run_eval()

    def test_empty_assertions_rejected(self):
        self.cases[0]["assertions"]=[]; self.persist()
        with self.assertRaises(ConfigError): self.run_eval()

    def test_duplicate_case_id_rejected(self):
        self.cases[1]["case_id"]="case-a"; self.persist()
        with self.assertRaises(ConfigError): self.run_eval()

    def test_unknown_assertion_rejected(self):
        self.cases[0]["assertions"][0]["op"]="silent-success"; self.persist()
        with self.assertRaises(ConfigError): self.run_eval()

    def test_error_record_is_failed_trial(self):
        self.records[0]["status"]="error"; self.persist()
        self.assertEqual(self.run_eval()["pass_rate"],0.75)

    def test_critical_failure_overrides_aggregate_threshold(self):
        self.cfg["gates"]["min_pass_rate"]=0.5
        self.cases[0]["assertions"][0]["critical"]=True
        self.records[0]["output"]={"text":"wrong"}; self.persist()
        result=self.run_eval()
        self.assertEqual(result["critical_failures"],1)
        self.assertIn("critical-assertion-failed",result["gate_failures"])

    def test_slice_threshold_enforced(self):
        self.cfg["gates"]["min_pass_rate"]=0.5
        self.cfg["gates"]["required_slices"]={"edge":{"min_cases":1,"min_pass_rate":1.0}}
        self.records[2]["output"]={"text":"wrong"}; self.persist()
        self.assertIn("slice:edge",self.run_eval()["gate_failures"])

    def test_missing_required_slice_fails(self):
        self.cfg["gates"]["required_slices"]={"not-observed":{"min_cases":1,"min_pass_rate":1.0}}; self.persist()
        self.assertEqual(self.run_eval()["status"],"FAIL")

    def test_metric_gate_rejects_missing_measurement(self):
        self.cfg["gates"]["max_p95_latency_ms"]=3
        self.records[0]["metrics"].pop("latency_ms"); self.persist()
        self.assertIn("max_p95_latency_ms",self.run_eval()["gate_failures"])

    def test_latency_gate_and_nearest_rank(self):
        self.cfg["gates"]["max_p95_latency_ms"]=1; self.persist()
        result=self.run_eval()
        self.assertEqual(result["measurements"]["latency_ms"]["p95"],2)
        self.assertEqual(result["status"],"FAIL")

    def test_negative_metric_rejected(self):
        self.records[0]["metrics"]["cost_usd"]=-1; self.persist()
        with self.assertRaises(ConfigError): self.run_eval()

    def test_dataset_hash_tamper_rejected(self):
        with (self.root/"data.jsonl").open("a") as f: f.write("\n")
        with self.assertRaises(ConfigError): self.run_eval()

    def test_result_hash_tamper_rejected(self):
        with (self.root/"results.jsonl").open("a") as f: f.write("\n")
        with self.assertRaises(ConfigError): self.run_eval()

    def test_stale_source_rejected(self):
        (self.root/"source.py").write_text("# changed\n")
        with self.assertRaises(ConfigError): self.run_eval()

    def test_expected_model_version_checked(self):
        self.cfg["run_metadata"]={"model":"different"}; self.persist()
        with self.assertRaises(ConfigError): self.run_eval()

    def test_repetition_mismatch_rejected(self):
        self.manifest["repetitions"]=3; self.persist()
        with self.assertRaises(ConfigError): self.run_eval()

    def test_baseline_regression_and_bootstrap(self):
        self.cfg["gates"]["min_pass_rate"]=0; self.persist()
        baseline=self.run_eval()
        self.cfg["gates"]["max_pass_rate_drop"]=0.1
        self.records[0]["output"]={"text":"wrong"}; self.persist()
        candidate=evaluate(self.cfg,self.root,baseline)
        self.assertEqual(candidate["comparison"]["pass_rate_delta"],-0.25)
        self.assertIn("pass-rate-regression",candidate["gate_failures"])

    def test_baseline_incompatible_contract_rejected(self):
        baseline=self.run_eval()
        self.cfg["gates"]["min_pass_rate"]=0.5
        with self.assertRaises(ConfigError): evaluate(self.cfg,self.root,baseline)

    def test_required_baseline_missing_rejected(self):
        self.cfg["gates"]["max_pass_rate_drop"]=0.1; self.persist()
        with self.assertRaises(ConfigError): self.run_eval()

    def test_zero_repetitions_rejected(self):
        self.cfg["repetitions"]=0; self.persist()
        with self.assertRaises(ConfigError): self.run_eval()


class GraderTests(unittest.TestCase):
    def test_json_pointer_escaped_keys(self):
        self.assertEqual(pointer({"a/b":{"x~y":[3]}},"/a~1b/x~0y/0"),3)

    def test_boolean_is_not_number(self):
        self.assertFalse(grade({"op":"equals","path":"/output","expected":True},{"output":1})[0])

    def test_missing_evidence_does_not_pass_negative_assertion(self):
        self.assertFalse(grade({"op":"not_contains","path":"/output/missing","expected":"x"},{"output":{}})[0])
        self.assertFalse(grade({"op":"tool_not_called","name":"synthetic-write"},{})[0])

    def test_tool_argument_subset(self):
        record={"trace":{"tool_calls":[{"name":"synthetic-read","arguments":{"key":"x","limit":2}}]}}
        self.assertTrue(grade({"op":"tool_called","name":"synthetic-read","arguments":{"key":"x"}},record)[0])
        self.assertFalse(grade({"op":"tool_called","name":"synthetic-read","arguments":{"key":"y"}},record)[0])

    def test_recall_duplicates_do_not_inflate(self):
        passed,score=grade({"op":"recall_at_k","expected":["a","b"],"k":2,"min":1.0},{"trace":{"retrieved_ids":["a","a","b"]}})
        self.assertFalse(passed); self.assertEqual(score,0.5)

    def test_citation_membership_is_nonempty(self):
        self.assertFalse(grade({"op":"citations_subset"},{"trace":{"citations":[],"retrieved_ids":[]}})[0])
        self.assertTrue(grade({"op":"citations_subset"},{"trace":{"citations":["a"],"retrieved_ids":["a"]}})[0])

    def test_external_judge_requires_provenance(self):
        check={"op":"score_at_least","metric":"quality","min":0.8}
        self.assertFalse(grade(check,{"scores":{"quality":{"value":1.0}}})[0])
        self.assertTrue(grade(check,{"scores":{"quality":{"value":0.9,"grader":"synthetic-test","version":"1"}}})[0])

    def test_array_contains_respects_boolean_type(self):
        self.assertFalse(grade({"op":"contains","path":"/output","expected":True},{"output":[1]})[0])
