#!/usr/bin/env python3
"""Human-readable JD alignment report (no ATS ranking claims)."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from jd_match import analyze

CATEGORIES = ("required", "unspecified", "preferred")
STATUS = {
    "supported_and_present": "Supported & visible",
    "supported_not_emphasized": "Supported; underemphasized",
    "unverified_or_missing": "Unverified or missing",
}


def markdown(result: dict) -> str:
    rows = result.get("requirements", [])
    supported = sum(bool(r.get("evidence_claim_ids")) for r in rows)
    req_missing = [r["skill"] for r in rows if r["priority"] == "required"
                   and r["status"] == "unverified_or_missing"]
    lines = [
        "# Job Description Alignment — Evidence-Based",
        "",
        "**Not an ATS score.** Skills are matched heuristically; work history and",
        "evidence must be reviewed by a human before using any claim.",
        "",
        f"**Explicit terms found:** {len(rows)} | **Evidence-backed:** {supported} | "
        f"**Not evidenced:** {len(rows)-supported}",
        "",
        "## Requirement matrix",
        "",
        "| JD priority | Technical term | Resume status | Supporting claim IDs |",
        "| --- | --- | --- | --- |",
    ]
    for cat in CATEGORIES:
        for r in rows:
            if r["priority"] != cat:
                continue
            evidence = ", ".join(r["evidence_claim_ids"]) or "—"
            lines.append(f"| {cat.capitalize()} | {r['skill']} | "
                         f"{STATUS[r['status']]} | {evidence} |")
    if not rows:
        lines.append("| — | No recognized terms | Human JD review required | — |")
    lines.extend(["", "## Required qualifications needing confirmation", ""])
    if req_missing:
        lines.extend(f"- {name}: ask for an actual, dated implementation before claiming it."
                     for name in req_missing)
    else:
        lines.append("- No unsupported *recognized* required technical terms; "
                     "review seniority, domain and behavioral requirements manually.")
    lines.extend([
        "", "## Recommendations", "",
        "- Emphasize evidence-backed requirements currently absent from resume prose.",
        "- Do not insert qualifications that have no candidate-confirmed evidence.",
        "- Review non-keyword JD requirements manually (scope, leadership, compliance, domain).",
        "- Run the bounded tailoring gate against the original evidence ledger before exporting.",
        "",
    ])
    return "\n".join(lines)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("ledger", type=Path)
    p.add_argument("jd", type=Path)
    p.add_argument("--output", type=Path,
                   help="Local Markdown file (default: work/jd-alignment.md)")
    args = p.parse_args()
    try:
        candidate = json.loads(args.ledger.read_text(encoding="utf-8"))
        jd = args.jd.read_text(encoding="utf-8")
        text = markdown(analyze(candidate, jd))
        out = args.output or Path("work/jd-alignment.md")
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")
        print(f"JD evidence report: {out}")
        return 0
    except (OSError, ValueError, TypeError, KeyError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
