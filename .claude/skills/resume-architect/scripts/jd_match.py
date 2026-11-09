#!/usr/bin/env python3
"""Conservative, evidence-aware JD keyword coverage report.

This is a heuristic extractor, not an ATS simulation. It never upgrades a
resume-only or public-company claim into candidate-confirmed experience.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

# Bounded canonical term vocabulary. Extend through reviewed, tested changes.
# Backed by explicit candidate claims; matching a self-described skills list
# by itself does not count as evidence.
TERMS: dict[str, str] = {
    "Python": r"python",
    "TypeScript": r"typescript",
    "JavaScript": r"javascript",
    "Node.js": r"node\.?js",
    ".NET": r"(?:\.net|dotnet)",
    "ASP.NET Core": r"asp\.net(?:\s+core)?",
    "C#": r"c#",
    "Java": r"java",
    "Go": r"golang|\bgo\b",
    "React": r"react(?:\.js)?",
    "Angular": r"angular",
    "FastAPI": r"fastapi",
    "Django": r"django",
    "Spring Boot": r"spring\s+boot",
    "SQL Server": r"(?:sql\s+server|mssql)",
    "PostgreSQL": r"(?:postgresql|postgres)",
    "MySQL": r"mysql",
    "MongoDB": r"mongodb",
    "Redis": r"redis",
    "GraphQL": r"graphql",
    "REST APIs": r"(?:rest(?:ful)?\s+apis?|rest(?:ful)?)",
    "gRPC": r"grpc",
    "WebSockets": r"websockets?",
    "Kafka": r"kafka",
    "RabbitMQ": r"rabbitmq",
    "Kubernetes": r"kubernetes|\bk8s\b",
    "Docker": r"docker",
    "Terraform": r"terraform",
    "AWS": r"\baws\b|amazon\s+web\s+services",
    "Azure": r"\bazure\b",
    "GCP": r"\bgcp\b|google\s+cloud",
    "Azure DevOps": r"azure\s+devops",
    "GitHub Actions": r"github\s+actions",
    "CI/CD": r"ci\s*/\s*cd|continuous\s+(?:integration|delivery|deployment)",
    "RAG": r"\brag\b|retrieval.augmented\s+generation",
    "LangGraph": r"langgraph",
    "Vertex AI": r"vertex\s+ai",
    "BigQuery": r"bigquery",
    "Snowflake": r"snowflake",
    "Databricks": r"databricks",
    "OAuth": r"oauth(?:\s*2(?:\.0)?)?",
    "RBAC": r"\brbac\b|role.based\s+access\s+control",
    "HIPAA": r"hipaa",
    "SOC 2": r"soc\s*2",
}
PATTERNS = {
    name: re.compile(r"(?<!\w)(?:" + pat + r")(?!\w)", re.IGNORECASE)
    for name, pat in TERMS.items()
}
REQUIRED_HEAD = re.compile(
    r"^(?:required|minimum|must.have|essential|basic)\s*"
    r"(?:skills|qualifications|requirements|experience)?\s*:?\s*$", re.I
)
PREFERRED_HEAD = re.compile(
    r"^(?:preferred|nice.to.have|bonus|desired)\s*"
    r"(?:skills|qualifications|experience)?\s*:?\s*$", re.I
)


def text_terms(text: str) -> set[str]:
    return {name for name, pattern in PATTERNS.items() if pattern.search(text)}


def confirmed_claim_ids(data: dict[str, Any], term: str) -> list[str]:
    pattern = PATTERNS[term]
    return sorted(str(c["id"]) for c in data.get("claims", [])
                  if isinstance(c, dict) and c.get("status") in
                  {"verified", "candidate_confirmed"}
                  and pattern.search(str(c.get("statement", "")))
                  and c.get("id"))


def resume_text(data: dict[str, Any]) -> str:
    candidate = data.get("candidate", {})
    chunks = [str(candidate.get(k, "")) for k in ("headline", "summary")]
    skills = candidate.get("skills", {})
    if isinstance(skills, dict):
        chunks.extend(str(k) + " " + str(v) for k, v in skills.items())
    for role in data.get("roles", []):
        chunks.extend(str(b.get("text", "")) for b in role.get("bullets", [])
                      if isinstance(b, dict))
    return "\n".join(chunks)


def analyze(data: dict[str, Any], jd: str) -> dict[str, Any]:
    if not jd.strip():
        raise ValueError("Job description must contain text")
    found: dict[str, dict[str, Any]] = {}
    priority = "unspecified"
    for lineno, raw in enumerate(jd.splitlines(), 1):
        line = raw.strip().lstrip("#*- •\t").strip()
        if not line:
            continue
        if REQUIRED_HEAD.fullmatch(line):
            priority = "required"
            continue
        if PREFERRED_HEAD.fullmatch(line):
            priority = "preferred"
            continue
        inline_required = bool(re.search(r"\b(?:must\s+have|required|minimum)\b", line, re.I))
        inline_preferred = bool(re.search(r"\b(?:preferred|nice\s+to\s+have|bonus)\b", line, re.I))
        line_priority = "required" if inline_required else "preferred" if inline_preferred else priority
        for term in text_terms(line):
            if term not in found:
                found[term] = {"skill": term, "priority": line_priority, "jd_lines": [lineno]}
            else:
                found[term]["jd_lines"].append(lineno)
                if line_priority == "required":
                    found[term]["priority"] = "required"
    present = text_terms(resume_text(data))
    for term, item in found.items():
        claims = confirmed_claim_ids(data, term)
        item["evidence_claim_ids"] = claims
        item["in_resume"] = term in present
        item["status"] = ("supported_and_present" if claims and term in present
                          else "supported_not_emphasized" if claims
                          else "unverified_or_missing")
    reqs = sorted(found.values(), key=lambda i: (
        {"required": 0, "unspecified": 1, "preferred": 2}[i["priority"]],
        i["skill"].casefold()
    ))
    return {
        "disclaimer": "Heuristic requirement coverage; not an ATS score or proof of skill.",
        "requirements": reqs,
        "supported": sum(bool(i["evidence_claim_ids"]) for i in reqs),
        "unverified": sum(not bool(i["evidence_claim_ids"]) for i in reqs),
        "questions": [
            f"Can the candidate demonstrate {i['skill']} experience?"
            for i in reqs if not i["evidence_claim_ids"]
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("ledger", type=Path)
    parser.add_argument("jd", type=Path, help="Plain text or Markdown job description")
    parser.add_argument("--output", type=Path, help="Write local JSON report")
    args = parser.parse_args()
    try:
        data = json.loads(args.ledger.read_text(encoding="utf-8"))
        jd = args.jd.read_text(encoding="utf-8")
        result = analyze(data, jd)
        output = json.dumps(result, indent=2)
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(output + "\n", encoding="utf-8")
        print(output)
        return 0
    except (OSError, ValueError, TypeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
