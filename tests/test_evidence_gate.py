import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / ".claude" / "skills" / "resume-architect" / "scripts"
sys.path.insert(0, str(SCRIPTS))
from evidence_gate import check


class EvidenceGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.good = json.loads((ROOT / "examples/candidate_verified.json").read_text())
        cls.bad = json.loads((ROOT / "examples/candidate_blocked.json").read_text())

    def test_known_good_fixture_passes(self):
        result = check(copy.deepcopy(self.good))
        self.assertTrue(result["passed"], result["errors"])
        self.assertEqual(result["quantified_bullets"], 1)

    def test_hypothesis_in_bullet_rejected(self):
        result = check(copy.deepcopy(self.bad))
        self.assertFalse(result["passed"])
        self.assertTrue(any("not cleared" in s for s in result["errors"]))

    def test_metric_without_measurement_method_rejected(self):
        data = copy.deepcopy(self.good)
        data["claims"][-1]["metric"].pop("method")
        result = check(data)
        self.assertFalse(result["passed"])
        self.assertTrue(any("missing method" in s for s in result["errors"]))

    def test_unverified_metric_rejected(self):
        data = copy.deepcopy(self.good)
        data["claims"][-1]["status"] = "candidate_confirmed"
        result = check(data)
        self.assertFalse(result["passed"])
        self.assertTrue(any("requires verified" in s for s in result["errors"]))

    def test_unexplained_overlap_rejected(self):
        data = copy.deepcopy(self.good)
        data["roles"][1]["end"] = "2023-04"
        result = check(data)
        self.assertFalse(result["passed"])
        self.assertTrue(any("overlapping roles" in s for s in result["errors"]))

    def test_explicit_concurrent_contract_allowed(self):
        data = copy.deepcopy(self.good)
        data["roles"][1]["end"] = "2023-04"
        data["roles"][1]["concurrent"] = True
        data["roles"][1]["employment_type"] = "consulting"
        data["roles"][1]["overlap_explanation"] = "Independent part-time consulting parallel to senior role"
        result = check(data)
        self.assertTrue(result["passed"], result["errors"])

    def test_cross_role_claim_rejected(self):
        data = copy.deepcopy(self.good)
        data["roles"][0]["bullets"][1]["claim_ids"] = ["c7"]
        result = check(data)
        self.assertFalse(result["passed"])
        self.assertTrue(any("another role" in s for s in result["errors"]))

    def test_excessive_numeric_bullets_rejected(self):
        data = copy.deepcopy(self.good)
        data["roles"][0]["bullets"][1]["quantified"] = True
        data["roles"][0]["bullets"][1]["metric_claim_ids"] = ["m1"]
        data["roles"][0]["bullets"][1]["claim_ids"].append("m1")
        data["roles"][0]["bullets"][2]["quantified"] = True
        data["roles"][0]["bullets"][2]["metric_claim_ids"] = ["m1"]
        data["roles"][0]["bullets"][2]["claim_ids"].append("m1")
        result = check(data)
        self.assertFalse(result["passed"])
        self.assertTrue(any("exceeds 30%" in s for s in result["errors"]))

    def test_numeric_unmarked_detected(self):
        data = copy.deepcopy(self.good)
        data["roles"][0]["bullets"][0]["quantified"] = False
        data["roles"][0]["bullets"][0]["metric_claim_ids"] = []
        result = check(data)
        self.assertFalse(result["passed"])
        self.assertTrue(any("numeric outcome not marked" in s for s in result["errors"]))


if __name__ == "__main__":
    unittest.main()
