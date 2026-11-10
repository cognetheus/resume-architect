import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / ".claude" / "skills" / "resume-architect" / "scripts"))
from resume_intake import extract, report


class IntakeTests(unittest.TestCase):
    def test_docx_text_and_table_extraction(self):
        xml = (b'<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
               b'<w:body><w:p><w:r><w:t>Candidate Example</w:t></w:r></w:p>'
               b'<w:tbl><w:tr><w:tc><w:p><w:r><w:t>Backend Engineer</w:t>'
               b'</w:r></w:p></w:tc></w:tr></w:tbl></w:body></w:document>')
        with tempfile.TemporaryDirectory() as temp:
            p = Path(temp) / "resume.docx"
            with zipfile.ZipFile(p, "w") as z:
                z.writestr("word/document.xml", xml)
            extracted, warnings = extract(p)
            self.assertIn("Candidate Example", extracted)
            self.assertIn("Backend Engineer", extracted)
            self.assertFalse(warnings)
            md = report(extracted, "resume.docx", [])
            self.assertIn("UNVERIFIED SOURCE EXTRACTION", md)
            self.assertIn("> Candidate Example", md)

    def test_plain_text_extraction(self):
        with tempfile.TemporaryDirectory() as temp:
            p = Path(temp) / "resume.txt"
            p.write_text("DevOps Engineer\nCloud migration", encoding="utf-8")
            text, warnings = extract(p)
            self.assertIn("Cloud migration", text)
            self.assertFalse(warnings)

    def test_pdf_extraction(self):
        try:
            from pypdf import PdfWriter
        except ImportError:
            self.skipTest("pypdf not installed")
        # A blank page must not be silently mistaken for a machine-readable resume.
        with tempfile.TemporaryDirectory() as temp:
            p = Path(temp) / "scan.pdf"
            w = PdfWriter()
            w.add_blank_page(width=612, height=792)
            with p.open("wb") as f:
                w.write(f)
            with self.assertRaisesRegex(ValueError, "No usable text"):
                extract(p)

    def test_no_text_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            p = Path(temp) / "empty.txt"
            p.write_text("")
            with self.assertRaisesRegex(ValueError, "No usable text"):
                extract(p)

    def test_rejects_unsupported_format(self):
        with tempfile.TemporaryDirectory() as temp:
            p = Path(temp) / "candidate.exe"
            p.write_text("not a resume")
            with self.assertRaisesRegex(ValueError, "Supported resume formats"):
                extract(p)


if __name__ == "__main__":
    unittest.main()
