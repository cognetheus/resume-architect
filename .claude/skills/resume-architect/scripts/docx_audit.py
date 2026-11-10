#!/usr/bin/env python3
"""Inspect DOCX integrity, ATS text extraction, and expected resume content.

The --ledger comparison detects missing names, roles, dates, metrics or bullets
in the final DOCX. It does not verify truthfulness or replace visual page QA.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
ENTITY = re.compile(r"&(?:#x[0-9a-fA-F]+|#\d+|[A-Za-z]+);")
XML_DOC = "word/document.xml"


def normalize(value: str) -> str:
    return re.sub(r"\s+", " ", unicodedata.normalize("NFKC", value)).strip().casefold()


def check_expected(paragraphs: list[str], ledger: dict) -> list[str]:
    """Check that final output contains fields from a validated private ledger.

    Deliberately exact enough to catch accidental truncation and missing bullets.
    The source renderer uses plain text in Word paragraphs.
    """
    missing: list[str] = []
    full = normalize("\n".join(paragraphs))

    def require(name: str, text: str) -> None:
        if text and normalize(str(text)) not in full:
            missing.append(f"{name} missing from extractable DOCX text")

    candidate = ledger.get("candidate", {})
    require("Candidate name", candidate.get("name", ""))
    for key in ("email", "phone", "linkedin"):
        require(f"Contact {key}", candidate.get(key, ""))
    for r in ledger.get("roles", []):
        rid = r.get("id", "?")
        require(f"{rid} employer", r.get("employer", ""))
        require(f"{rid} title", r.get("title", ""))
        require(f"{rid} start date", r.get("start", ""))
        require(f"{rid} end date", r.get("end", "") or "Present")
        for idx, b in enumerate(r.get("bullets", [])):
            require(f"{rid} bullet {idx+1}", b.get("text", ""))
    for ed in candidate.get("education", []):
        require("Education institution", ed.get("institution", ""))
        require("Education degree", ed.get("degree", ""))
    return missing


def audit(path: Path, ledger: dict | None = None) -> dict:
    errors: list[str] = []
    warnings: list[str] = []
    paragraphs: list[str] = []
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
                if "summary" not in full.casefold() and "professional" not in full.casefold():
                    warnings.append("No conventional summary or experience heading detected")
    except (OSError, zipfile.BadZipFile, ET.ParseError) as exc:
        errors.append(f"Unreadable DOCX: {exc}")
    if ledger is not None and paragraphs:
        errors.extend(check_expected(paragraphs, ledger))
    return {
        "passed": not errors,
        "errors": errors,
        "warnings": warnings,
        "paragraph_count": len(paragraphs),
        "extracted_characters": sum(len(p) for p in paragraphs),
        "first_paragraphs": paragraphs[:5],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("docx", type=Path)
    parser.add_argument("--ledger", type=Path, help="Private candidate ledger for content-preservation checks")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    try:
        expected = json.loads(args.ledger.read_text(encoding="utf-8")) if args.ledger else None
        result = audit(args.docx, expected)
    except (OSError, ValueError, TypeError) as exc:
        result = {"passed": False, "errors": [str(exc)], "warnings": []}
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print("PASS" if result["passed"] else "FAIL", args.docx)
        for label in ("errors", "warnings"):
            for msg in result[label]:
                print(label.upper(), msg)
        print(f"{result.get('paragraph_count', 0)} text paragraphs")
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
