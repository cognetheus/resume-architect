import io
import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / ".claude" / "skills" / "resume-architect" / "scripts"))
from docx_audit import audit


def fake_docx(text):
    xml = ('<w:document xmlns:w="http://schemas.openxmlformats.org/'
           'wordprocessingml/2006/main"><w:body><w:p><w:r><w:t>'
           + text + '</w:t></w:r></w:p></w:body></w:document>')
    with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as f:
        path = Path(f.name)
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("word/document.xml", xml.encode())
    return path


class DocxAuditTests(unittest.TestCase):
    def test_extractable_text(self):
        path = fake_docx("Professional Summary")
        try:
            result = audit(path)
            self.assertTrue(result["passed"], result["errors"])
            self.assertEqual(result["paragraph_count"], 1)
        finally:
            path.unlink()

    def test_literal_html_entities_warning(self):
        path = fake_docx("Professional Summary &amp;#x20; test")
        try:
            result = audit(path)
            self.assertTrue(result["passed"], result["errors"])
            self.assertTrue(any("HTML entities" in w for w in result["warnings"]))
        finally:
            path.unlink()

    def test_non_docx_is_rejected(self):
        with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as f:
            f.write(b"not a zip")
            p = Path(f.name)
        try:
            self.assertFalse(audit(p)["passed"])
        finally:
            p.unlink()


if __name__ == "__main__":
    unittest.main()
