import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / ".claude" / "skills" / "resume-architect" / "scripts"))
from jd_match import analyze
from jd_report import markdown


class JDReportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        data = json.loads((ROOT / "examples/candidate_verified.json").read_text(encoding="utf-8"))
        jd = (ROOT / "examples/job-description.txt").read_text(encoding="utf-8")
        cls.text = markdown(analyze(data, jd))

    def test_required_missing_identified(self):
        self.assertIn("Requirement matrix", self.text)
        self.assertIn("Required qualifications needing confirmation", self.text)

    def test_supported_and_unsupported_visible(self):
        self.assertIn("Terraform", self.text)
        self.assertIn("Kubernetes", self.text)
        self.assertIn("Unverified or missing", self.text)
        self.assertIn("Supporting claim IDs", self.text)

    def test_not_fake_ats_score(self):
        self.assertIn("Not an ATS score", self.text)


if __name__ == "__main__":
    unittest.main()
