#!/usr/bin/env python3
"""Post-export PDF layout heuristics for engineering resumes.

Flags excess pages, sparse continuation pages, and likely orphan headings.
This uses selectable PDF text, not visual rendering. Final visual inspection
is still required; warnings are advisory unless --strict is supplied.
"""
from __future__ import annotations

import argparse
import json
import re
import statistics
import sys
from pathlib import Path
from typing import Any

HEADING_NAMES = {
    "summary", "professional summary", "technical skills", "core skills",
    "skills", "professional experience", "work experience",
    "experience", "education", "certifications", "projects",
    "selected projects", "technical expertise", "professional profile",
}
WORD_RE = re.compile(r"\b[\w+#./%-]+\b", re.UNICODE)
PAGE_NUMBER = re.compile(r"^(?:page\s+)?\d+(?:\s+(?:of|/)\s+\d+)?$", re.I)
MAX_PDF_BYTES = 20 * 1024 * 1024


def clean_lines(text: str) -> list[str]:
    lines = [re.sub(r"\s+", " ", s).strip() for s in text.splitlines()]
    return [s for s in lines if s and not PAGE_NUMBER.fullmatch(s)]


def is_heading(line: str, ledger: dict | None) -> bool:
    cleaned = line.strip().strip(":").casefold()
    if cleaned in HEADING_NAMES:
        return True
    if not ledger:
        return False
    for role in ledger.get("roles", []):
        title = str(role.get("title", "")).strip().casefold()
        employer = str(role.get("employer", "")).strip().casefold()
        if title and employer and title in cleaned and employer in cleaned:
            return True
    return False


def assess_text_pages(pages: list[str], ledger: dict | None = None,
                      max_pages: int = 2, sparse_threshold: int = 85,
                      sparse_ratio: float = 0.40) -> dict[str, Any]:
    if max_pages < 1:
        raise ValueError("max_pages must be positive")
    if sparse_threshold < 0 or not (0 < sparse_ratio <= 1):
        raise ValueError("Invalid sparse-page thresholds")

    issues: list[dict[str, Any]] = []
    lengths = [len(WORD_RE.findall(text)) for text in pages]
    if not pages:
        issues.append({"severity": "error", "code": "empty_pdf",
                       "page": None, "detail": "PDF has no pages"})
    if len(pages) > max_pages:
        issues.append({
            "severity": "warning", "code": "page_limit", "page": None,
            "detail": f"{len(pages)} pages exceeds preferred maximum {max_pages}; review content fit"
        })
    for index, count in enumerate(lengths):
        if count == 0:
            issues.append({
                "severity": "error", "code": "no_selectable_text", "page": index + 1,
                "detail": "No extractable text on page; page may be blank or image-only"
            })

    for index in range(1, len(pages)):
        prior = lengths[:index]
        typical = statistics.median(prior) if prior else 0
        if typical >= 100 and 0 < lengths[index] < min(
                sparse_threshold, typical * sparse_ratio):
            issues.append({
                "severity": "warning", "code": "sparse_continuation",
                "page": index + 1,
                "detail": f"Page {index+1} has {lengths[index]} words versus "
                          f"median {typical:g} on preceding pages"
            })

    # End-of-page line checks work even if a PDF extractor cannot provide
    # dependable coordinates. Check last two lines to catch role title + date.
    for index in range(len(pages) - 1):
        if not lengths[index + 1]:
            continue
        lines = clean_lines(pages[index])
        for line in lines[-2:]:
            if is_heading(line, ledger):
                issues.append({
                    "severity": "warning", "code": "orphan_heading",
                    "page": index + 1,
                    "detail": f"Heading '{line[:110]}' appears at end of page {index+1}"
                })
                break
    return {
        "passed": not any(i["severity"] == "error" for i in issues),
        "page_count": len(pages),
        "page_word_counts": lengths,
        "issues": issues,
        "limitations": [
            "Line-order heuristics may miss headings in complex PDFs or generate false positives.",
            "Text-only analysis cannot detect clipping, font size problems, or awkward visual spacing.",
            "Render and visually inspect every PDF page before final delivery."
        ],
    }


def audit_pdf(path: Path, *, ledger: dict | None = None,
              max_pages: int = 2, sparse_threshold: int = 85) -> dict:
    from pypdf import PdfReader

    if not path.is_file():
        raise ValueError(f"PDF not found: {path}")
    if path.stat().st_size > MAX_PDF_BYTES:
        raise ValueError("PDF exceeds 20MB audit limit")
    if path.suffix.casefold() != ".pdf":
        raise ValueError("Expected a PDF file")
    try:
        reader = PdfReader(str(path))
        if reader.is_encrypted:
            raise ValueError("Encrypted PDF cannot be audited without decryption")
        if len(reader.pages) > 30:
            raise ValueError("PDF exceeds 30-page safety limit")
        pages = [p.extract_text() or "" for p in reader.pages]
        return assess_text_pages(pages, ledger=ledger, max_pages=max_pages,
                                 sparse_threshold=sparse_threshold)
    except (OSError, ValueError) as exc:
        raise ValueError(f"Cannot inspect PDF: {exc}") from exc


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf", type=Path)
    parser.add_argument("--ledger", type=Path, help="Private candidate evidence JSON for role headings")
    parser.add_argument("--max-pages", type=int, default=2)
    parser.add_argument("--sparse-words", type=int, default=85)
    parser.add_argument("--strict", action="store_true",
                        help="Fail if warnings were found; default warnings are advisory")
    parser.add_argument("--output", type=Path, help="Private JSON QA report")
    args = parser.parse_args()
    try:
        ledger = json.loads(args.ledger.read_text(encoding="utf-8")) if args.ledger else None
        report = audit_pdf(args.pdf, ledger=ledger, max_pages=args.max_pages,
                           sparse_threshold=args.sparse_words)
        if args.strict and report["passed"] and report["issues"]:
            report["passed"] = False
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(report, indent=2))
        return 0 if report["passed"] else 1
    except (OSError, ValueError, TypeError, ImportError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
