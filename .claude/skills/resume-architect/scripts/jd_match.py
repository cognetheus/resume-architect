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



# Explicit responsibility themes complement technology keywords. Matching is
# conservative and does not prove years, scale, management scope, or proficiency.
# Each theme has a JD regex and a stricter candidate-claim regex.
RESPONSIBILITY_RULES: dict[str, tuple[str, str]] = {
    "System architecture and design": (
        r"\bsystem\s+design\b|\b(?:software|system|solution)\s+architectur\w*\b|"
        r"\barchitect(?:ing|ure)\b|\btechnical\s+design\b|\bservice\s+boundaries\b",
        r"\b(?:designed|architected|owned|led|guided)\b.{0,85}"
        r"\b(?:architectur\w*|design|service\s+boundar\w*|platform|api\s+contract\w*)\b"
    ),
    "Distributed and event-driven systems": (
        r"\bdistributed\s+systems?\b|\bmicroservices?\b|\bevent[- ]driven\b|"
        r"\basynchronous\s+processing\b|\bmessage\s+queues?\b",
        r"\bdistributed\s+(?:systems?|services?)\b|\bmicroservices?\b|"
        r"\bevent[- ]driven\b|\bidempotent\s+event\b|"
        r"\b(?:asynchronous|async)\s+processing\b|\bmessage\s+queues?\b"
    ),
    "Reliability and production operations": (
        r"\b(?:reliability|high\s+availability|fault\s+tolerance|incident\s+response|"
        r"on[- ]call|SLOs?|observability|production\s+monitoring)\b",
        r"\b(?:reliability|high\s+availability|fault\s+tolerance|incident\s+response|"
        r"on[- ]call|SLOs?|observability|production\s+monitoring)\b"
    ),
    "Performance and scalability": (
        r"\b(?:performance|latency|throughput|scalab\w*|capacity\s+planning)\b",
        r"\b(?:performance|latency|throughput|scalab\w*|query\s+plans?|"
        r"(?:sql|api)\s+optim\w*)\b"
    ),
    "Security and compliance": (
        r"\b(?:security|secure\s+design|access\s+control|authentication|authorization|"
        r"compliance|HIPAA|SOC\s*2|GDPR|privacy)\b",
        r"\b(?:access\s+control|RBAC|authentication|authorization|encryption|"
        r"audit\s+logging|HIPAA|SOC\s*2|GDPR|security\s+controls?)\b"
    ),
    "Technical leadership and reviews": (
        r"\b(?:technical\s+leadership|technical\s+lead|lead\s+engineers?|"
        r"mentoring|mentor|code\s+reviews?|architecture\s+reviews?|"
        r"cross[- ]functional\s+leadership)\b",
        r"\b(?:mentored|mentoring|led\s+(?:engineers?|a\s+team)|guided|"
        r"code\s+reviews?|architecture\s+reviews?|technical\s+leadership)\b"
    ),
    "Data pipelines and integration": (
        r"\b(?:data\s+pipelines?|ETL|ELT|ingest\w*|data\s+integrat\w*|"
        r"data\s+synchroniz\w*|data\s+engineering)\b",
        r"\b(?:data\s+pipelines?|ETL|ELT|ingest\w*|data\s+integrat\w*|"
        r"reconciliation|data\s+synchroniz\w*)\b"
    ),
    "Cloud infrastructure and delivery": (
        r"\b(?:cloud\s+(?:infrastructure|architecture|migration)|"
        r"infrastructure\s+as\s+code|landing\s+zones?|deployment\s+automation|"
        r"platform\s+engineering)\b",
        r"\b(?:cloud\s+(?:infrastructure|architecture|migration|delivery)|"
        r"terraform|infrastructure\s+as\s+code|landing\s+zones?|"
        r"deployment\s+automation)\b"
    ),
    "Testing and release quality": (
        r"\b(?:automated\s+testing|integration\s+testing|unit\s+testing|"
        r"test\s+automation|quality\s+engineering|contract\s+testing)\b",
        r"\b(?:integration\s+tests?|unit\s+tests?|contract\s+tests?|"
        r"automated\s+tests?|test\s+automation|test\s+coverage)\b"
    )
}
RESPONSIBILITY_PATTERNS = {
    name: (re.compile(jd_re, re.I), re.compile(claim_re, re.I))
    for name, (jd_re, claim_re) in RESPONSIBILITY_RULES.items()
}


def jd_lines(jd: str):
    """Yield line number, text and conventional qualification priority."""
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
        yield lineno, line, line_priority


def analyze_responsibilities(data: dict[str, Any], jd: str) -> list[dict[str, Any]]:
    found: dict[str, dict[str, Any]] = {}
    resume = resume_text(data)
    for lineno, line, priority in jd_lines(jd):
        for name, (jd_re, evidence_re) in RESPONSIBILITY_PATTERNS.items():
            if not jd_re.search(line):
                continue
            if name not in found:
                found[name] = {"responsibility": name, "priority": priority, "jd_lines": [lineno]}
            else:
                found[name]["jd_lines"].append(lineno)
                if priority == "required":
                    found[name]["priority"] = "required"
    for name, row in found.items():
        evidence_re = RESPONSIBILITY_PATTERNS[name][1]
        ids = sorted(str(c.get("id")) for c in data.get("claims", [])
                     if isinstance(c, dict) and c.get("id")
                     and c.get("status") in {"verified", "candidate_confirmed"}
                     and evidence_re.search(str(c.get("statement", ""))))
        row["evidence_claim_ids"] = ids
        row["in_resume"] = bool(evidence_re.search(resume))
        row["status"] = ("supported_and_present" if ids and row["in_resume"]
                         else "supported_not_emphasized" if ids
                         else "unverified_or_missing")
        row["caveat"] = "Relevant evidence only; exact role scope and years require human review."
    return sorted(found.values(), key=lambda row: (
        {"required": 0, "unspecified": 1, "preferred": 2}[row["priority"]],
        row["responsibility"].casefold()
    ))

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
    for lineno, line, line_priority in jd_lines(jd):
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
    responsibilities = analyze_responsibilities(data, jd)
    return {
        "disclaimer": "Heuristic requirement coverage; not an ATS score or proof of skill.",
        "requirements": reqs,
        "responsibilities": responsibilities,
        "responsibilities_supported": sum(bool(i["evidence_claim_ids"]) for i in responsibilities),
        "supported": sum(bool(i["evidence_claim_ids"]) for i in reqs),
        "unverified": sum(not bool(i["evidence_claim_ids"]) for i in reqs),
        "questions": [
            f"Can the candidate demonstrate {i['skill']} experience?"
            for i in reqs if not i["evidence_claim_ids"]
        ] + [f"Can the candidate demonstrate {i['responsibility']}?"
             for i in responsibilities if not i["evidence_claim_ids"]],
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
