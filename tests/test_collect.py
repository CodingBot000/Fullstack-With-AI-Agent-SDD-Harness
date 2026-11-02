"""Synthetic subprocess adapters test collection plumbing; no paid/model calls."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from _core import ConfigError, load_jsonl, sha256
from collect_eval import collect
from evaluate import evaluate

class CollectionTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        (self.root/"app.py").write_text("# synthetic fixture only\n")
        case={"case_id":"one","input":{"text":"fixture"},"slice":"synthetic",
              "assertions":[{"op":"equals","path":"/output/text","expected":"fixture"}]}
        (self.root/"data.jsonl").write_text(json.dumps(case)+"\n")
        self.cfg={"schema_version":1,"dataset":"data.jsonl","results":"results.jsonl","run_manifest":"run.json",
                  "source_paths":["app.py"],"repetitions":1,"min_cases":1,
                  "run_metadata":{"code_ref":"fixture","model":"no-real-model","prompt_version":"fixture",
                                  "corpus_version":"not-applicable","tool_policy_version":"fixture"},
                  "adapter":{"argv":["{python}","-c", "import json,sys; x=json.load(sys.stdin); assert set(x)=={'case_id','trial','input'}; print(json.dumps({'output':x['input']}))"],
                             "cwd":".","timeout_seconds":5},
                  "gates":{"min_pass_rate":1.0,"max_p95_latency_ms":None,"max_mean_cost_usd":None,"max_pass_rate_drop":None,"required_slices":{}}}

    def test_adapter_receives_no_assertions(self):
        manifest=collect(self.cfg,self.root)
        self.assertEqual(manifest["failed_trials"],0)
        self.assertEqual(evaluate(self.cfg,self.root)["status"],"PASS")

    def test_adapter_failure_is_recorded(self):
        self.cfg["adapter"]["argv"]=["{python}","-c","raise SystemExit(7)"]
        manifest=collect(self.cfg,self.root)
        self.assertEqual(manifest["failed_trials"],1)
        self.assertEqual(evaluate(self.cfg,self.root)["status"],"FAIL")

    def test_adapter_bad_json_is_recorded(self):
        self.cfg["adapter"]["argv"]=["{python}","-c","print('not JSON')"]
        collect(self.cfg,self.root)
        self.assertEqual(load_jsonl(self.root/"results.jsonl")[0]["error_code"],"INVALID_ADAPTER_OUTPUT")

    def test_existing_run_not_overwritten(self):
        collect(self.cfg,self.root)
        before=sha256(self.root/"results.jsonl")
        with self.assertRaises(ConfigError): collect(self.cfg,self.root)
        self.assertEqual(before,sha256(self.root/"results.jsonl"))

    def test_missing_run_metadata_is_not_configured(self):
        self.cfg["run_metadata"]["model"]=None
        with self.assertRaises(ConfigError): collect(self.cfg,self.root)

    def test_timeout_produces_failed_trial(self):
        self.cfg["adapter"]["argv"]=["{python}","-c","import time; time.sleep(5)"]
        self.cfg["adapter"]["timeout_seconds"]=0.03
        collect(self.cfg,self.root)
        self.assertEqual(load_jsonl(self.root/"results.jsonl")[0]["error_code"],"TIMEOUT")

    def test_output_cannot_overwrite_input_dataset(self):
        self.cfg["results"]="data.jsonl"
        with self.assertRaises(ConfigError): collect(self.cfg,self.root)
