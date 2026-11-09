# Resume Architect

An evidence-first Claude Code skill for senior technical resume auditing, company research, engineering interviews, credibility checks, ATS-friendly writing, and deliverable QA.

The project skill is at `.claude/skills/resume-architect/SKILL.md`. Claude Code loads it when you open this repository. Invoke `/resume-architect audit path/to/resume.pdf`, `/resume-architect research`, `/resume-architect interview`, `/resume-architect rewrite`, or `/resume-architect validate`.

## Why this exists

A senior resume should explain **systems engineered, decisions owned, difficult constraints, and verified impact**, not enumerate tools or invent achievements. Public employer case studies are research context, **never proof** that a candidate worked on a project. Unconfirmed metrics, AI chronology errors, unexplained overlapping roles, and speculative implementation details block submission.

## Working method

1. Audit the source document and record dated employment/technical claims.
2. Research company history during the candidate's employment period.
3. Interview for real architecture, individual ownership, scale and failure modes.
4. Record candidate-confirmed claims and measurement evidence in a local ledger.
5. Write cohesive job bullets; aim for 5–7 for major roles and at most 30% quantified.
6. Validate the evidence ledger, author DOCX/PDF, inspect extracted text, and perform a final hiring-manager review.

See `.claude/skills/resume-architect/references/` for policy, research, interview and writing guidance.

## Tools

Python 3.10+ is sufficient for the evidence gate and unit tests:

```bash
python -m unittest discover -s tests -v
python .claude/skills/resume-architect/scripts/evidence_gate.py examples/candidate_verified.json
python .claude/skills/resume-architect/scripts/evidence_gate.py examples/candidate_blocked.json  # expected failure
```

Optional rendering utilities require `pip install -r requirements.txt`. A document generator must never be used to bypass the evidence gate.

## Installation

- **Project scoped:** clone the repository and open it in Claude Code; the skill is available as `/resume-architect`.
- **Personal:** copy `.claude/skills/resume-architect` to `~/.claude/skills/resume-architect`.
- No API keys are required for the bundled validators. Employer research requires a configured browsing tool and citations.

## Privacy and integrity

Do not commit actual candidate resumes, contact information, evidence ledgers, or employer research notes to this repository. Use local ignored work directories. Never fabricate performance metrics, project assignment, credentials, work authorization or technical ownership.

This skill is guidance plus deterministic checks, **not a guarantee of ATS ranking, job eligibility, or independently verified employment history**.
