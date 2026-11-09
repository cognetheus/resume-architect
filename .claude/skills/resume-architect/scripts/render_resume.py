#!/usr/bin/env python3
"""Render a validated private candidate ledger to a single-column DOCX.

Requires python-docx. PDF conversion is optional via LibreOffice/soffice.
Never bypasses the evidence gate; a passing ledger still requires human review.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

from evidence_gate import check


def render(data: dict, path: Path) -> None:
    try:
        from docx import Document
        from docx.enum.text import WD_ALIGN_PARAGRAPH
        from docx.shared import Inches, Pt
    except ImportError as exc:
        raise RuntimeError("Install python-docx: pip install -r requirements.txt") from exc

    report = check(data)
    if not report["passed"]:
        raise ValueError("Evidence gate failed:\n" + "\n".join(report["errors"]))

    doc = Document()
    section = doc.sections[0]
    section.top_margin = Inches(0.64)
    section.bottom_margin = Inches(0.64)
    section.left_margin = Inches(0.72)
    section.right_margin = Inches(0.72)
    normal = doc.styles["Normal"]
    normal.font.name = "Aptos"
    normal.font.size = Pt(9.6)
    normal.paragraph_format.space_after = Pt(3.8)

    def text_line(s: str, size: float | None = None, bold: bool = False) -> None:
        p = doc.add_paragraph()
        run = p.add_run(s)
        run.bold = bold
        if size is not None:
            run.font.size = Pt(size)
        p.paragraph_format.space_after = Pt(3.0)

    def heading(s: str) -> None:
        p = doc.add_paragraph()
        p.style = doc.styles["Heading 2"]
        p.paragraph_format.space_before = Pt(10)
        p.paragraph_format.space_after = Pt(4)
        r = p.add_run(s.upper())
        r.font.size = Pt(10.5)

    c = data["candidate"]
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(c["name"])
    r.bold = True
    r.font.size = Pt(17)
    if c.get("headline"):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(c["headline"])
        r.font.size = Pt(10)
    contact = [str(c[k]) for k in ("city", "email", "phone", "linkedin") if c.get(k)]
    if contact:
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run("  |  ".join(contact))
        r.font.size = Pt(8.6)

    if c.get("summary"):
        heading("Professional Summary")
        text_line(c["summary"])
    skills = c.get("skills", {})
    if isinstance(skills, dict) and skills:
        heading("Technical Skills")
        for name, value in skills.items():
            text_line(f"{name}: {value}")

    heading("Professional Experience")
    for role in data["roles"]:
        p = doc.add_paragraph()
        p.paragraph_format.keep_with_next = True
        p.paragraph_format.space_before = Pt(7)
        p.paragraph_format.space_after = Pt(2)
        run = p.add_run(f"{role['title']} | {role['employer']}")
        run.bold = True
        dates = f"{role['start']} – {role.get('end') or 'Present'}"
        if role.get("employment_type") in {"contract", "consulting"}:
            dates += " | Independent contract"
        text_line(dates, size=8.5)
        for bullet in role.get("bullets", []):
            p = doc.add_paragraph(style="List Bullet")
            p.paragraph_format.left_indent = Inches(0.22)
            p.paragraph_format.first_line_indent = Inches(-0.13)
            p.paragraph_format.space_after = Pt(3.5)
            p.add_run(bullet["text"])

    education = c.get("education", [])
    if education:
        heading("Education")
        for ed in education:
            parts = [str(ed.get(k)) for k in ("degree", "institution", "year") if ed.get(k)]
            text_line(" | ".join(parts))
    path.parent.mkdir(parents=True, exist_ok=True)
    doc.save(path)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("ledger", type=Path)
    parser.add_argument("output_docx", type=Path)
    parser.add_argument("--pdf", action="store_true", help="Also generate PDF via LibreOffice")
    args = parser.parse_args()
    try:
        data = json.loads(args.ledger.read_text(encoding="utf-8"))
        render(data, args.output_docx)
        print(f"DOCX: {args.output_docx}")
        if args.pdf:
            office = shutil.which("libreoffice") or shutil.which("soffice")
            if not office:
                raise RuntimeError("DOCX created; PDF conversion unavailable (LibreOffice not installed)")
            cmd = [office, "-env:UserInstallation=file:///tmp/resume-architect-lo",
                   "--headless", "--convert-to", "pdf", "--outdir",
                   str(args.output_docx.parent), str(args.output_docx)]
            subprocess.run(cmd, check=True, capture_output=True, text=True)
            pdf = args.output_docx.with_suffix(".pdf")
            if not pdf.is_file() or pdf.stat().st_size == 0:
                raise RuntimeError("PDF conversion reported success but output file is missing")
            print(f"PDF: {pdf}")
        return 0
    except (OSError, ValueError, RuntimeError, subprocess.CalledProcessError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
