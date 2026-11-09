#!/usr/bin/env python3
"""JD-tailoring diff and evidence gate.

Measures word-level edit budget on editable narrative fields, preserves career
metadata, bullet provenance and metric values, and checks newly added technical
terms against confirmed claims. This is NOT a semantic truth verifier or ATS score.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

from evidence_gate import check
from jd_match import analyze, confirmed_claim_ids, text_terms

WORD = re.compile(r"[\w+#./%-]+", re.UNICODE)
METRIC_TEXT = re.compile(
    r"(?<!\w)\d+(?:\.\d+)?\s*(?:%|percent|ms|milliseconds?|seconds?|hours?|"
    r"days?|million|billion|users|requests|records|documents|deployments|"
    r"incidents|tickets)\b", re.I
)
PROTECTED_CANDIDATE_FIELDS = ("name", "city", "email", "phone", "linkedin", "education")


def words(text: str) -> list[str]:
    return [w.casefold() for w in WORD.findall(text)]


def edit_units(before: str, after: str) -> int:
    a, b = words(before), words(after)
    matcher = SequenceMatcher(None, a, b, autojunk=False)
    total = 0
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag != "equal":
            total += max(i2 - i1, j2 - j1)
    return total


def flatten_editable(data: dict[str, Any]) -> dict[str, str]:
    candidate = data["candidate"]
    result = {
        "candidate.headline": str(candidate.get("headline", "")),
        "candidate.summary": str(candidate.get("summary", "")),
    }
    skills = candidate.get("skills", {})
    if not isinstance(skills, dict):
        skills = {}
    for key, value in skills.items():
        result[f"candidate.skills.{key}"] = str(value)
    for role in data.get("roles", []):
        for index, bullet in enumerate(role.get("bullets", [])):
            result[f"{role['id']}.bullets[{index}]"] = str(bullet.get("text", ""))
    return result


def metrics(text: str) -> list[str]:
    return sorted(" ".join(match.lower().split()) for match in METRIC_TEXT.findall(text))


def verify(base: dict[str, Any], tailored: dict[str, Any], jd: str,
           *, target: float = 0.20, max_change: float = 0.30) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    if not (0.10 <= target <= 0.30):
        errors.append("Target must be between 0.10 and 0.30")
    if not (0.10 <= max_change <= 0.30):
        errors.append("Maximum change must be between 0.10 and 0.30")
    if target > max_change:
        errors.append("Target cannot exceed maximum")
    if not jd.strip():
        errors.append("A nonempty job description is required")
    baseline_report = check(base)
    tailored_report = check(tailored)
    if not baseline_report["passed"]:
        errors.extend("baseline: " + e for e in baseline_report["errors"])
    if not tailored_report["passed"]:
        errors.extend("tailored: " + e for e in tailored_report["errors"])

    bc, tc = base.get("candidate", {}), tailored.get("candidate", {})
    for field in PROTECTED_CANDIDATE_FIELDS:
        if bc.get(field) != tc.get(field):
            errors.append(f"Protected candidate field changed: {field}")
    if base.get("claims") != tailored.get("claims"):
        errors.append("Claim ledger changed during tailoring: keep provenance immutable")
    if len(base.get("roles", [])) != len(tailored.get("roles", [])):
        errors.append("Role count changed during tailoring")
    for index, (original, revised) in enumerate(zip(
        base.get("roles", []), tailored.get("roles", []))):
        before_meta = {k: v for k, v in original.items() if k != "bullets"}
        after_meta = {k: v for k, v in revised.items() if k != "bullets"}
        if before_meta != after_meta:
            errors.append(f"Role {index}: employer/title/dates/contract metadata changed")
        old_bullets, new_bullets = original.get("bullets", []), revised.get("bullets", [])
        if len(old_bullets) != len(new_bullets):
            errors.append(f"Role {index}: bullet count changed")
        for j, (a, b) in enumerate(zip(old_bullets, new_bullets)):
            label = f"{original.get('id', index)}.bullets[{j}]"
            for field in ("claim_ids", "metric_claim_ids", "quantified"):
                if a.get(field) != b.get(field):
                    errors.append(f"{label}: provenance or metric attachment changed ({field})")
            if metrics(str(a.get("text", ""))) != metrics(str(b.get("text", ""))):
                errors.append(f"{label}: quantitative values/units changed")
            # A new technical keyword must be supported by the exact bullet's
            # existing claim references, not merely a different job's experience.
            introduced = text_terms(str(b.get("text", ""))) - text_terms(str(a.get("text", "")))
            allowed_claims = set(b.get("claim_ids", []))
            for term in sorted(introduced):
                supported = set(confirmed_claim_ids(base, term))
                if not (supported & allowed_claims):
                    errors.append(f"{label}: new term '{term}' lacks linked candidate evidence")

    prior = flatten_editable(base)
    later = flatten_editable(tailored)
    if list(prior) != list(later):
        errors.append("Editable field keys changed; keep skills groups and bullet positions stable")
    global_supported = {term for term in set().union(
        *[text_terms(v) for v in prior.values()])} if prior else set()
    for path in ("candidate.headline", "candidate.summary", *(
            p for p in prior if p.startswith("candidate.skills."))):
        introduced = text_terms(later.get(path, "")) - text_terms(prior.get(path, ""))
        for term in sorted(introduced):
            if not confirmed_claim_ids(base, term):
                errors.append(f"{path}: new technical term '{term}' lacks confirmed evidence")
    total_words = sum(len(words(v)) for v in prior.values())
    modified = sum(edit_units(v, later.get(k, "")) for k, v in prior.items())
    change_ratio = modified / total_words if total_words else 0.0
    if total_words == 0:
        errors.append("Baseline has no editable words")
    if change_ratio > max_change + 1e-9:
        errors.append(f"Edit budget exceeded: {change_ratio:.1%} > {max_change:.0%}")
    if change_ratio < 0.10:
        warnings.append(
            f"Only {change_ratio:.1%} wording changed (<10% preference). "
            "Do not invent filler to reach the minimum."
        )
    if change_ratio > target:
        warnings.append(f"Changes {change_ratio:.1%} exceed preferred target {target:.0%}")
    if not errors and not modified:
        warnings.append("No JD tailoring was applied")
    jd_report = analyze(tailored, jd) if jd.strip() else {}
    changed = [
        {"field": path, "before": original, "after": later.get(path, ""),
         "edit_units": edit_units(original, later.get(path, ""))}
        for path, original in prior.items()
        if original != later.get(path, "")
    ]
    return {
        "passed": not errors,
        "errors": errors,
        "warnings": warnings,
        "target_ratio": target,
        "maximum_ratio": max_change,
        "word_edit_ratio": round(change_ratio, 4),
        "baseline_words": total_words,
        "edit_units": modified,
        "changed_fields": changed,
        "jd_alignment": jd_report,
        "limitations": [
            "Edit ratio is a deterministic word-level heuristic, not a semantic similarity score.",
            "JD coverage is a conservative keyword inventory, not an ATS result.",
            "Evidence references and claim consistency require human verification."
        ],
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("baseline", type=Path, help="Verified baseline ledger JSON")
    p.add_argument("tailored", type=Path, help="Tailored ledger JSON")
    p.add_argument("--jd", type=Path, required=True, help="Plain-text or Markdown JD")
    p.add_argument("--target", type=float, default=0.20)
    p.add_argument("--max-change", type=float, default=0.30)
    p.add_argument("--report", type=Path, help="Write local JSON diff and alignment report")
    args = p.parse_args()
    try:
        before = json.loads(args.baseline.read_text(encoding="utf-8"))
        after = json.loads(args.tailored.read_text(encoding="utf-8"))
        jd = args.jd.read_text(encoding="utf-8")
        result = verify(before, after, jd, target=args.target, max_change=args.max_change)
        if args.report:
            args.report.parent.mkdir(parents=True, exist_ok=True)
            args.report.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(result, indent=2))
        return 0 if result["passed"] else 1
    except (OSError, ValueError, TypeError, KeyError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
