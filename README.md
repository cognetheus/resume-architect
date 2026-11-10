# Resume Architect

An evidence-first Claude Code skill for senior technical resume auditing, company research, engineering interviews, credibility checks, ATS-friendly writing, and deliverable QA.

The project skill is at `.claude/skills/resume-architect/SKILL.md`. Claude Code loads it when you open this repository. Invoke `/resume-architect intake path/to/resume.pdf`, `/resume-architect audit path/to/resume.pdf`, `/resume-architect research`, `/resume-architect interview`, `/resume-architect rewrite`, `/resume-architect tailor`, or `/resume-architect validate`.

## Why this exists

A senior resume should explain **systems engineered, decisions owned, difficult constraints, and verified impact**, not enumerate tools or invent achievements. Public employer case studies are research context, **never proof** that a candidate worked on a project. Unconfirmed metrics, AI chronology errors, unexplained overlapping roles, and speculative implementation details block submission.

## Working method

1. **Intake a raw PDF/DOCX/TXT resume** into a local, explicitly unverified source report; no manual JSON preparation to begin auditing.
2. Audit the source document and record dated employment/technical claims.
3. Research company history during the candidate's employment period.
4. Interview for real architecture, individual ownership, scale and failure modes.
5. Record candidate-confirmed claims and measurement evidence in a local ledger.
6. Write cohesive job bullets; aim for 5–7 for major roles and at most 30% quantified.
7. Optionally tailor 10–30% of narrative wording to a supplied JD using only evidence-backed qualifications (20% default target; hard 30% cap).
8. Validate the evidence ledger and optional JD diff, author DOCX/PDF, inspect extracted text, and perform a final hiring-manager review.

See `.claude/skills/resume-architect/references/` for policy, research, interview and writing guidance.

## Quick start: resume file to audit

```text
/resume-architect intake ./input/resume.pdf
/resume-architect audit ./input/resume.pdf
```

A source resume is **not** a verified evidence ledger. The skill extracts the original text, identifies suspect timelines and claim gaps, and conducts confirmation before submitting an evidence-backed rewrite. No invented employment details or default "AI resume" technologies.

```bash
python .claude/skills/resume-architect/scripts/resume_intake.py \
  input/resume.pdf --output work/intake.md

python .claude/skills/resume-architect/scripts/docx_audit.py \
  work/final-resume.docx --ledger work/candidate.json
```

PDF reading requires the small `pypdf` dependency; scanned PDFs lacking selectable text need manual review or a separate approved OCR path.

## Tools

Python 3.10+ is sufficient for the evidence gate and unit tests:

```bash
python -m unittest discover -s tests -v
python .claude/skills/resume-architect/scripts/evidence_gate.py examples/candidate_verified.json
python .claude/skills/resume-architect/scripts/evidence_gate.py examples/candidate_blocked.json  # expected failure
```

Optional rendering utilities require `pip install -r requirements.txt`. A document generator must never be used to bypass the evidence gate.


## Optional JD-tailored variants (new)

Supply a **plain-text or Markdown** job description. The default process still works without one. The JD mode identifies requirements supported by the candidate's verified claims, then rewrites **about 10–30% of narrative wording**, aiming for 20% by default. The 30% ceiling is enforced on the word-level edit budget; if fewer than 10% useful changes are substantiated, the tool reports that and does not pad the resume.

Claude Code usage:

```text
/resume-architect tailor ./work/candidate.json --jd ./work/job-description.txt --target 0.20
```

Local validation tools (source and tailored ledgers remain private):

```bash
python .claude/skills/resume-architect/scripts/jd_match.py \
  work/candidate.json work/job-description.txt --output work/jd-match.json

python .claude/skills/resume-architect/scripts/jd_report.py \
  work/candidate.json work/job-description.txt --output work/jd-alignment.md

python .claude/skills/resume-architect/scripts/tailor_gate.py \
  work/candidate.json work/candidate-tailored.json \
  --jd work/job-description.txt --target 0.20 \
  --report work/jd-tailor-report.json

python .claude/skills/resume-architect/scripts/render_resume.py \
  work/candidate-tailored.json work/targeted-resume.docx
```

The JD report is human-readable Markdown: it highlights evidenced requirements, underemphasized skills, and required gaps. The gate protects employer names, titles, career dates, education, contact details, metric values, evidence/claim links, and bullet counts. Newly introduced technical terms must be supported by candidate-confirmed or verified claims, with role-specific evidence for work bullets. It produces a field-by-field diff and job-requirement coverage inventory.

**This does not guarantee ATS acceptance or job fit.** Truthful evidence and real system-design depth take priority over keyword quotas.

## Installation

- **Project scoped:** clone the repository and open it in Claude Code; the skill is available as `/resume-architect`.
- **Personal:** copy `.claude/skills/resume-architect` to `~/.claude/skills/resume-architect`.
- No API keys are required for the bundled validators. Employer research requires a configured browsing tool and citations.

## Privacy and integrity

Do not commit actual candidate resumes, contact information, evidence ledgers, or employer research notes to this repository. Use local ignored work directories. Never fabricate performance metrics, project assignment, credentials, work authorization or technical ownership.

This skill is guidance plus deterministic checks, **not a guarantee of ATS ranking, job eligibility, or independently verified employment history**.
