#!/usr/bin/env python3
"""Fail-closed evidence gate for the Resume Architect skill (stdlib only).

This checks structural provenance, chronology and metrics. It cannot independently
establish that a candidate's statements are true; human verification is mandatory.
"""
from __future__ import annotations

import argparse
import calendar
import json
import re
import sys
from datetime import date
from pathlib import Path
from typing import Any

ALLOWED = {"verified", "candidate_confirmed", "source_reported",
           "research_context", "hypothesis", "contradicted"}
USABLE = {"verified", "candidate_confirmed"}
KINDS = {"employment", "implementation", "leadership", "technology", "education", "metric"}
MEASURED_TYPES = {"measurement", "report", "experiment", "operational_dashboard"}
NUMERIC_TEXT = re.compile(
    r"\b\d+(?:\.\d+)?\s*(?:%|percent|ms|milliseconds?|seconds?|hours?|days?|"
    r"million|billion|users|requests|records|documents|deployments|incidents|tickets)\b",
    re.IGNORECASE,
)
MONTH = re.compile(r"^(\d{4})-(0[1-9]|1[0-2])$")


def month_index(value: str | None, *, end: bool = False) -> int | None:
    if value is None:
        today = date.today()
        return today.year * 12 + today.month if end else None
    if not isinstance(value, str) or not MONTH.fullmatch(value):
        return None
    year, month = map(int, value.split("-"))
    return year * 12 + month


def check(data: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    if not isinstance(data, dict):
        return {"passed": False, "errors": ["Root must be an object"], "warnings": []}

    candidate = data.get("candidate")
    if not isinstance(candidate, dict) or not str(candidate.get("name", "")).strip():
        errors.append("candidate.name is required")
    roles = data.get("roles", [])
    claims = data.get("claims", [])
    if not isinstance(roles, list) or not roles:
        errors.append("roles must be a nonempty array")
        roles = []
    if not isinstance(claims, list):
        errors.append("claims must be an array")
        claims = []

    by_id: dict[str, dict] = {}
    for idx, c in enumerate(claims):
        if not isinstance(c, dict):
            errors.append(f"claims[{idx}]: expected an object")
            continue
        cid = str(c.get("id", ""))
        if not cid or cid in by_id:
            errors.append(f"claims[{idx}]: missing or duplicate claim id '{cid}'")
            continue
        by_id[cid] = c
        if c.get("status") not in ALLOWED:
            errors.append(f"{cid}: invalid evidence status")
        if c.get("kind") not in KINDS:
            errors.append(f"{cid}: invalid claim kind")
        if not str(c.get("statement", "")).strip():
            errors.append(f"{cid}: statement required")
        ev = c.get("evidence")
        if c.get("status") in USABLE:
            if not isinstance(ev, list) or not ev or not all(
                isinstance(item, dict) and str(item.get("type", "")).strip()
                and str(item.get("ref", "")).strip() for item in ev
            ):
                errors.append(f"{cid}: usable claim needs evidence type and reference")
        if c.get("kind") == "metric":
            m = c.get("metric", {})
            if not isinstance(m, dict):
                m = {}
            has_comparison = all(isinstance(m.get(k), (int, float)) and
                                 not isinstance(m.get(k), bool) for k in ("before", "after"))
            has_observed = isinstance(m.get("observed"), (int, float)) and \
                not isinstance(m.get("observed"), bool)
            if c.get("status") in USABLE:
                if c.get("status") != "verified":
                    errors.append(f"{cid}: quantitative claim requires verified status")
                if not (has_comparison or has_observed):
                    errors.append(f"{cid}: metric requires numeric before/after or observed")
                for k in ("unit", "period", "method"):
                    if not str(m.get(k, "")).strip():
                        errors.append(f"{cid}: metric missing {k}")
                if not isinstance(ev, list) or not any(
                    isinstance(x, dict) and x.get("type") in MEASURED_TYPES for x in ev
                ):
                    errors.append(f"{cid}: metric requires measurement/report evidence")

    spans = []
    total_bullets = 0
    metric_bullets = 0
    role_ids: set[str] = set()
    for i, role in enumerate(roles):
        if not isinstance(role, dict):
            errors.append(f"roles[{i}]: expected object")
            continue
        rid = str(role.get("id", ""))
        if not rid or rid in role_ids:
            errors.append(f"roles[{i}]: missing or duplicate role id '{rid}'")
        role_ids.add(rid)
        for k in ("employer", "title", "start"):
            if not str(role.get(k, "")).strip():
                errors.append(f"{rid or i}: missing {k}")
        start = month_index(role.get("start"))
        finish = month_index(role.get("end"), end=True)
        if start is None or finish is None:
            errors.append(f"{rid or i}: dates must be YYYY-MM; end may be null")
        elif finish < start:
            errors.append(f"{rid or i}: end precedes start")
        else:
            spans.append((start, finish, role))
        bullets = role.get("bullets", [])
        if not isinstance(bullets, list):
            errors.append(f"{rid}: bullets must be an array")
            continue
        if len(bullets) < 3:
            warnings.append(f"{rid}: fewer than 3 bullets; check role depth")
        if len(bullets) > 8:
            warnings.append(f"{rid}: more than 8 bullets; consider editing")
        role_metrics = 0
        for j, b in enumerate(bullets):
            label = f"{rid}.bullets[{j}]"
            if not isinstance(b, dict) or not str(b.get("text", "")).strip():
                errors.append(f"{label}: bullet text is required")
                continue
            refs = b.get("claim_ids")
            if not isinstance(refs, list) or not refs:
                errors.append(f"{label}: claim_ids must be nonempty")
                refs = []
            for cid in refs:
                c = by_id.get(cid)
                if c is None:
                    errors.append(f"{label}: unknown claim '{cid}'")
                else:
                    if c.get("status") not in USABLE:
                        errors.append(f"{label}: claim '{cid}' not cleared for resume")
                    if c.get("role_id") and c.get("role_id") != rid:
                        errors.append(f"{label}: claim '{cid}' belongs to another role")
            is_metric = b.get("quantified", False)
            if not isinstance(is_metric, bool):
                errors.append(f"{label}: quantified must be true/false")
                is_metric = False
            mrefs = b.get("metric_claim_ids", [])
            if not isinstance(mrefs, list):
                errors.append(f"{label}: metric_claim_ids must be array")
                mrefs = []
            if bool(NUMERIC_TEXT.search(b["text"])) and not is_metric:
                errors.append(f"{label}: numeric outcome not marked quantified")
            if is_metric and not mrefs:
                errors.append(f"{label}: quantified bullet requires metric_claim_ids")
            if mrefs and not is_metric:
                errors.append(f"{label}: metric IDs present but quantified=false")
            for mid in mrefs:
                if mid not in refs:
                    errors.append(f"{label}: metric claim '{mid}' absent from claim_ids")
                c = by_id.get(mid)
                if c is None or c.get("kind") != "metric" or c.get("status") != "verified":
                    errors.append(f"{label}: metric '{mid}' is not verified")
            if is_metric:
                role_metrics += 1
            if len(b["text"]) > 350:
                warnings.append(f"{label}: long bullet (>350 characters)")
        if bullets and role_metrics / len(bullets) > 0.30:
            errors.append(f"{rid}: quantified bullet ratio exceeds 30% ({role_metrics}/{len(bullets)})")
        total_bullets += len(bullets)
        metric_bullets += role_metrics

    # Overlap is fine for explicitly identified consulting, not unexplained parallel full-time jobs.
    for i, (s1, e1, a) in enumerate(spans):
        for s2, e2, b in spans[i + 1:]:
            if s1 <= e2 and s2 <= e1:
                approved = any(
                    bool(r.get("concurrent")) and
                    r.get("employment_type") in {"contract", "consulting", "part_time"} and
                    str(r.get("overlap_explanation", "")).strip()
                    for r in (a, b)
                )
                if not approved:
                    errors.append(f"overlapping roles require a documented concurrent contract: {a.get('id')} / {b.get('id')}")
                else:
                    warnings.append(f"concurrent engagement identified: {a.get('id')} / {b.get('id')}; verify dates")

    if total_bullets and metric_bullets / total_bullets > 0.30:
        errors.append("overall quantified bullet ratio exceeds 30%")
    return {
        "passed": not errors,
        "errors": errors,
        "warnings": warnings,
        "claims": len(by_id),
        "roles": len(roles),
        "bullets": total_bullets,
        "quantified_bullets": metric_bullets,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("ledger", type=Path, help="Private candidate evidence ledger JSON")
    parser.add_argument("--json", action="store_true", help="Print machine-readable report")
    args = parser.parse_args()
    try:
        data = json.loads(args.ledger.read_text(encoding="utf-8"))
        report = check(data)
    except (OSError, ValueError) as exc:
        report = {"passed": False, "errors": [str(exc)], "warnings": []}
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print("PASS" if report["passed"] else "FAIL", "-", args.ledger)
        for issue in report.get("errors", []):
            print("ERROR:", issue)
        for item in report.get("warnings", []):
            print("WARN:", item)
        print(f"roles={report.get('roles', 0)} claims={report.get('claims', 0)} "
              f"bullets={report.get('bullets', 0)} quantified={report.get('quantified_bullets', 0)}")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
