import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / ".claude" / "skills" / "resume-architect" / "scripts"))
from jd_match import analyze
from jd_report import markdown


class ResponsibilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads((ROOT / "examples/candidate_verified.json").read_text())
        cls.jd = (ROOT / "examples/job-description-architecture.txt").read_text()

    def test_architecture_and_distributed_patterns_are_evidence_backed(self):
        rows = {r["responsibility"]: r for r in analyze(self.data, self.jd)["responsibilities"]}
        self.assertIn("System architecture and design", rows)
        self.assertIn("Distributed and event-driven systems", rows)
        self.assertEqual(rows["System architecture and design"]["priority"], "required")
        self.assertIn("c5", rows["System architecture and design"]["evidence_claim_ids"])
        self.assertIn("c6", rows["Distributed and event-driven systems"]["evidence_claim_ids"])

    def test_reliability_gap_is_not_invented(self):
        rows = {r["responsibility"]: r for r in analyze(self.data, self.jd)["responsibilities"]}
        self.assertEqual(rows["Reliability and production operations"]["status"],
                         "unverified_or_missing")
        self.assertFalse(rows["Reliability and production operations"]["evidence_claim_ids"])

    def test_leadership_and_security_are_not_interpreted_as_people_management(self):
        rows = {r["responsibility"]: r for r in analyze(self.data, self.jd)["responsibilities"]}
        self.assertIn("c5", rows["Technical leadership and reviews"]["evidence_claim_ids"])
        self.assertIn("c8", rows["Security and compliance"]["evidence_claim_ids"])
        self.assertIn("scope", rows["Technical leadership and reviews"]["caveat"])

    def test_unverified_claim_does_not_count(self):
        modified = json.loads(json.dumps(self.data))
        for claim in modified["claims"]:
            if claim["id"] == "c5":
                claim["status"] = "source_reported"
        rows = {r["responsibility"]: r for r in analyze(modified, self.jd)["responsibilities"]}
        self.assertNotIn("c5", rows["System architecture and design"]["evidence_claim_ids"])

    def test_report_includes_nonkeyword_themes_and_coverage_gaps(self):
        report = markdown(analyze(self.data, self.jd))
        self.assertIn("Engineering responsibilities", report)
        self.assertIn("Required responsibilities needing confirmation", report)
        self.assertIn("Reliability and production operations", report)
        self.assertIn("Relevant evidence", report)


if __name__ == "__main__":
    unittest.main()
