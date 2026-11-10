import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / ".claude" / "skills" / "resume-architect" / "scripts"))
from docx_audit import audit
from render_resume import render


class ContentAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ledger = json.loads((ROOT / "examples/candidate_verified.json").read_text(encoding="utf-8"))

    def test_rendered_docx_preserves_expected_content(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "example.docx"
            render(self.ledger, path)
            result = audit(path, self.ledger)
            self.assertTrue(result["passed"], result["errors"])

    def test_missing_bullet_is_detected(self):
        from docx import Document
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "example.docx"
            render(self.ledger, path)
            doc = Document(path)
            first_bullet = self.ledger["roles"][0]["bullets"][0]["text"]
            for paragraph in doc.paragraphs:
                if paragraph.text == first_bullet:
                    paragraph._element.getparent().remove(paragraph._element)
                    break
            doc.save(path)
            result = audit(path, self.ledger)
            self.assertFalse(result["passed"])
            self.assertTrue(any("bullet 1" in e for e in result["errors"]))

    def test_missing_role_detected(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "example.docx"
            render(self.ledger, path)
            check = json.loads(json.dumps(self.ledger))
            check["roles"][0]["employer"] = "Unknown Invented Company"
            result = audit(path, check)
            self.assertFalse(result["passed"])
            self.assertTrue(any("employer" in e for e in result["errors"]))


if __name__ == "__main__":
    unittest.main()
