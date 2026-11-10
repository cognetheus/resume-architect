import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

from pypdf import PdfReader, PdfWriter
from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / ".claude" / "skills" / "resume-architect" / "scripts"))
from pdf_layout_audit import assess_text_pages, audit_pdf


def make_pdf(path: Path, lines_per_page: list[list[str]]) -> None:
    """Generate real selectable-text PDFs with pypdf alone (no rendering dependency)."""
    writer = PdfWriter()
    font = DictionaryObject({
        NameObject("/Type"): NameObject("/Font"),
        NameObject("/Subtype"): NameObject("/Type1"),
        NameObject("/BaseFont"): NameObject("/Helvetica")
    })
    font_ref = writer._add_object(font)
    for lines in lines_per_page:
        page = writer.add_blank_page(width=612, height=792)
        page[NameObject("/Resources")] = DictionaryObject({
            NameObject("/Font"): DictionaryObject({NameObject("/F1"): font_ref})
        })
        stream = DecodedStreamObject()
        commands = ["BT", "/F1 10 Tf", "72 740 Td"]
        for line in lines:
            escaped = line.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
            commands.extend([f"({escaped}) Tj", "0 -14 Td"])
        commands.append("ET")
        stream.set_data("\n".join(commands).encode("latin-1"))
        page[NameObject("/Contents")] = writer._add_object(stream)
    with path.open("wb") as f:
        writer.write(f)


class PdfLayoutTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ledger = json.loads((ROOT / "examples/candidate_verified.json").read_text())

    def test_single_page_ok(self):
        report = assess_text_pages(["Senior Engineer\nProfessional Summary\n" +
                                    "Built backend services with automated releases. " * 35])
        self.assertTrue(report["passed"])
        self.assertFalse(report["issues"])

    def test_page_count_warning(self):
        pages = ["Built services with Python and SQL. " * 25] * 3
        issues = assess_text_pages(pages)["issues"]
        self.assertTrue(any(x["code"] == "page_limit" for x in issues))

    def test_sparse_last_page(self):
        pages = ["Designed reliable systems with deployment automation. " * 55,
                 "Education\nUniversity"]
        issues = assess_text_pages(pages)["issues"]
        self.assertTrue(any(x["code"] == "sparse_continuation" and x["page"] == 2
                            for x in issues))

    def test_orphan_section_heading(self):
        pages = ["Senior Engineer\nProfessional Experience",
                 "Built transaction and integration services. " * 45]
        issues = assess_text_pages(pages)["issues"]
        self.assertTrue(any(x["code"] == "orphan_heading" for x in issues))

    def test_orphan_role_heading_and_date(self):
        pages = ["Senior Backend Engineer | Sample Systems (fictional)\n2021-04 - Present",
                 "Built backend services with a PostgreSQL database. " * 40]
        issues = assess_text_pages(pages, ledger=self.ledger)["issues"]
        self.assertTrue(any(x["code"] == "orphan_heading" for x in issues))

    def test_blank_page_error(self):
        self.assertFalse(assess_text_pages(["No text on next page", ""])["passed"])

    def test_real_pdf_text(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "sample.pdf"
            make_pdf(path, [["Professional Summary", "Senior backend engineer",
                             "Built reliable APIs with tested deployments."],
                            ["Professional Experience", "Database Engineer"]])
            report = audit_pdf(path)
            self.assertEqual(report["page_count"], 2)
            self.assertTrue(report["passed"], report["issues"])
            self.assertEqual(len(report["page_word_counts"]), 2)
            self.assertTrue(any(x["code"] == "orphan_heading" for x in report["issues"]))

    def test_blank_real_pdf_detected(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "blank.pdf"
            writer = PdfWriter()
            writer.add_blank_page(width=612, height=792)
            with p.open("wb") as f:
                writer.write(f)
            report = audit_pdf(p)
            self.assertFalse(report["passed"])
            self.assertTrue(any(x["code"] == "no_selectable_text" for x in report["issues"]))


if __name__ == "__main__":
    unittest.main()
