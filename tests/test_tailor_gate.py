import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / ".claude" / "skills" / "resume-architect" / "scripts"))
from tailor_gate import verify

class TailorGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base = json.loads((ROOT / "examples/candidate_verified.json").read_text(encoding="utf-8"))
        cls.tailored = json.loads((ROOT / "examples/candidate_tailored.json").read_text(encoding="utf-8"))
        cls.jd = (ROOT / "examples/job-description.txt").read_text(encoding="utf-8")

    def result(self, after=None, before=None, jd=None):
        return verify(before or self.base, after or self.tailored,
                      self.jd if jd is None else jd)

    def test_candidate_sample_passes_and_is_within_budget(self):
        r = self.result()
        self.assertTrue(r["passed"], r["errors"])
        self.assertLessEqual(r["word_edit_ratio"], 0.30)
        self.assertGreater(r["word_edit_ratio"], 0.0)
        self.assertTrue(r["changed_fields"])

    def test_missing_jd_fails(self):
        self.assertFalse(self.result(jd="")["passed"])

    def test_unsupported_new_technology_in_bullet_rejected(self):
        after = copy.deepcopy(self.tailored)
        after["roles"][0]["bullets"][2]["text"] += " Managed Kubernetes clusters."
        result = self.result(after=after)
        self.assertFalse(result["passed"])
        self.assertTrue(any("Kubernetes" in e for e in result["errors"]))

    def test_skill_in_summary_requires_evidence(self):
        after = copy.deepcopy(self.tailored)
        after["candidate"]["summary"] += " Expert in Kafka."
        result = self.result(after=after)
        self.assertFalse(result["passed"])
        self.assertTrue(any("Kafka" in e for e in result["errors"]))

    def test_bullet_technology_from_wrong_role_rejected(self):
        after = copy.deepcopy(self.tailored)
        after["roles"][1]["bullets"][0]["text"] += " Applied Terraform."
        result = self.result(after=after)
        self.assertFalse(result["passed"])
        self.assertTrue(any("lacks linked candidate evidence" in e for e in result["errors"]))

    def test_dates_and_titles_protected(self):
        after = copy.deepcopy(self.tailored)
        after["roles"][0]["title"] = "Principal Platform Architect"
        self.assertFalse(self.result(after=after)["passed"])
        self.assertTrue(any("metadata changed" in e for e in self.result(after=after)["errors"]))

    def test_ledger_mutation_rejected(self):
        after = copy.deepcopy(self.tailored)
        after["claims"][0]["status"] = "verified"
        self.assertFalse(self.result(after=after)["passed"])

    def test_numeric_achievement_values_unchanged(self):
        after = copy.deepcopy(self.tailored)
        after["roles"][0]["bullets"][0]["text"] = after["roles"][0]["bullets"][0]["text"].replace("280 ms", "120 ms")
        result = self.result(after=after)
        self.assertFalse(result["passed"])
        self.assertTrue(any("quantitative values" in e for e in result["errors"]))

    def test_30_percent_hard_cap(self):
        after = copy.deepcopy(self.tailored)
        after["candidate"]["summary"] += " " + "trustworthy scalable enterprise architecture " * 28
        result = self.result(after=after)
        self.assertFalse(result["passed"])
        self.assertTrue(any("Edit budget exceeded" in e for e in result["errors"]))

    def test_less_than_ten_percent_warns_without_padded_edits(self):
        result = self.result(after=copy.deepcopy(self.base))
        self.assertTrue(result["passed"], result["errors"])
        self.assertTrue(any("<10%" in w for w in result["warnings"]))

    def test_bullet_provenance_cannot_change(self):
        after = copy.deepcopy(self.tailored)
        after["roles"][0]["bullets"][1]["claim_ids"] = ["c9"]
        result = self.result(after=after)
        self.assertFalse(result["passed"])

if __name__ == "__main__":
    unittest.main()
