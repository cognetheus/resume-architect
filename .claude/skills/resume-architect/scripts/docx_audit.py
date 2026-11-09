#!/usr/bin/env python3
"""Inspect DOCX package integrity and basic ATS extraction risks (stdlib only)."""
from __future__ import annotations

import argparse
import json
import re
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
ENTITY = re.compile(r"&(?:#x[0-9a-fA-F]+|#\d+|[A-Za-z]+);")
XML_DOC = "word/document.xml"


def audit(path: Path) -> dict:
    errors, warnings = [], []
    paragraphs = []
    try:
        with zipfile.ZipFile(path) as z:
            if z.testzip():
                errors.append("DOCX ZIP integrity error")
            if XML_DOC not in z.namelist():
                errors.append("Missing Word document.xml")
            else:
                root = ET.fromstring(z.read(XML_DOC))
                for p in root.findall(".//w:p", NS):
                    text = "".join(t.text or "" for t in p.findall(".//w:t", NS))
                    if text.strip():
                        paragraphs.append(text.strip())
                if root.findall(".//w:tbl", NS):
                    warnings.append("Contains tables; check ATS text order")
                for col in root.findall(".//w:cols", NS):
                    num = col.get("{%s}num" % NS["w"], "1")
                    if num != "1":
                        warnings.append(f"Multiple Word columns: {num}")
                if not paragraphs:
                    errors.append("No extractable paragraph text")
                full = "\n".join(paragraphs)
                if ENTITY.search(full):
                    warnings.append("Literal HTML entities appear in extracted text")
                if "\ufffd" in full:
                    warnings.append("Replacement Unicode characters found")
                if any(ord(c) < 32 and c not in "\n\t" for c in full):
                    warnings.append("Control characters found")
                if "Summary" not in full and "Professional" not in full:
                    warnings.append("No conventional summary or experience heading detected")
    except (OSError, zipfile.BadZipFile, ET.ParseError) as exc:
        errors.append(f"Unreadable DOCX: {exc}")
    return {
        "passed": not errors,
        "errors": errors,
        "warnings": warnings,
        "paragraph_count": len(paragraphs),
        "extracted_characters": sum(len(p) for p in paragraphs),
        "first_paragraphs": paragraphs[:5],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("docx", type=Path)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = audit(args.docx)
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print("PASS" if report["passed"] else "FAIL", args.docx)
        for label in ("errors", "warnings"):
            for msg in report[label]:
                print(label.upper(), msg)
        print(f"{report['paragraph_count']} text paragraphs")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
