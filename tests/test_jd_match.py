import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / ".claude" / "skills" / "resume-architect" / "scripts"))
from jd_match import analyze, text_terms

class JDMatchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads((ROOT / "examples/candidate_verified.json").read_text(encoding="utf-8"))
        cls.jd = (ROOT / "examples/job-description.txt").read_text(encoding="utf-8")

    def test_supported_and_missing_separated(self):
        result = analyze(self.data, self.jd)
        terms = {r["skill"]: r for r in result["requirements"]}
        self.assertTrue(terms["Terraform"]["evidence_claim_ids"])
        self.assertTrue(terms["Python"]["evidence_claim_ids"])
        self.assertEqual(terms["Kubernetes"]["status"], "unverified_or_missing")
        self.assertEqual(terms["Kafka"]["status"], "unverified_or_missing")

    def test_required_vs_preferred(self):
        terms = {r["skill"]: r for r in analyze(self.data, self.jd)["requirements"]}
        self.assertEqual(terms["Terraform"]["priority"], "required")
        self.assertEqual(terms["Kubernetes"]["priority"], "preferred")

    def test_resume_only_skill_not_automatically_evidence(self):
        data = copy.deepcopy(self.data)
        for c in data["claims"]:
            c["statement"] = "Candidate interviewed about system boundaries"
        terms = {r["skill"]: r for r in analyze(data, self.jd)["requirements"]}
        self.assertEqual(terms["AWS"]["status"], "unverified_or_missing")

    def test_empty_jd_rejected(self):
        with self.assertRaises(ValueError):
            analyze(self.data, " \n")

    def test_technical_term_boundaries(self):
        self.assertNotIn("Java", text_terms("JavaScript"))
        self.assertIn("JavaScript", text_terms("JavaScript"))
        self.assertIn("C#", text_terms("C# and .NET"))
        self.assertIn(".NET", text_terms("C# and .NET"))

if __name__ == "__main__":
    unittest.main()
