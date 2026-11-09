---
name: resume-architect
description: "Evidence-first senior engineering resume audit, ATS review, company research, engineering interview, credibility verification and resume rewriting. Use when screening technical resumes, rebuilding a CV, validating technical achievements, tailoring to a job description, or creating an ATS-friendly senior software, cloud, DevOps, data, or AI resume."
argument-hint: "[audit|research|interview|rewrite|tailor|validate|deliver] [resume-path] [--jd job-description.txt] [--target 0.20]"
---

# Resume Architect

Treat resumes as technical claims requiring evidence, not creative-writing prompts. Build a coherent engineering career narrative from actual systems, individual ownership, architecture decisions and defensible impact. Never silently turn plausible scenarios into candidate accomplishments.

## Invocation and scope

Parse the first argument as the mode: `audit`, `research`, `interview`, `rewrite`, `tailor`, `validate`, or `deliver`. If omitted, infer the smallest useful stage from the request. Honor read-only/audit-only instructions. Do not rewrite files in audit mode. Use user-supplied resume and job description as sources, and explicitly identify missing artifacts.

**Command examples**
- `/resume-architect audit ./input/resume.pdf`
- `/resume-architect research ./input/resume.docx`
- `/resume-architect interview`
- `/resume-architect rewrite ./input/resume.pdf`
- `/resume-architect tailor ./work/candidate.json --jd ./input/job-description.txt --target 0.20`
- `/resume-architect validate ./work/candidate.json`
- `/resume-architect deliver ./work/candidate.json`

## Non-negotiable policy

1. **No invented claims:** Never fabricate employers, dates, products, clients, systems, cloud infrastructure, certifications, team size, metrics or technical ownership. Avoid attributing employer case studies to the candidate.
2. **Provenance:** Maintain a local evidence ledger; link every output bullet to candidate-confirmed or document-verifiable claims. Public company information is contextual, not employment proof.
3. **Chronology:** Check overlapping dates, career length, period-appropriate technology availability, title progression and concurrent contracts; flag ambiguities. A plausible technology is not evidence that it was used.
4. **Numbers:** Use only confirmed, defensible metrics with a baseline or direct production measurement. Target ~20–30% quantified bullets and never exceed 30% in a role. No number quota justifies invented values.
5. **Technical seniority:** Prefer system ownership, service/data boundaries, cloud design, consistency and failure modes, production reliability, security, performance, CI/CD and mentoring scope over task inventories.
6. **Concise writing:** Each bullet should say what was engineered, a salient approach or constraint, and a short technical result if verified. Do not append long explanations of nontechnical users' benefits.
7. **Privacy:** Keep original resumes, interview transcripts and candidate ledgers local. Do not push them to public repos or external services without explicit authorization. Redact when demonstrating.
8. **JD tailoring:** If a JD is supplied, selectively adapt verified summary, skills, and accomplishment wording to its requirements. Measure and cap the narrative edit budget at 30%; target 10–30% but never invent content to hit a quota. Keep titles, employers, dates, metrics and evidence links unchanged.
9. **No fake ATS scores:** Treat scores as editorial heuristics; actual ATS ranking depends on a target role and system. Do not promise ranking, job eligibility, or fraud-proof verification.

Read `references/evidence-policy.md` before writing or approving claims.

## Six-stage controlled workflow

### Gate A — Source forensics
- Read the entire original document, tables and page images if available. Preserve exact employer names, dates, role titles, contact details and stated skill evidence.
- Distinguish a resume's claims from independently validated facts. Capture contradictions, chronology issues, tokenized buzzwords, unsupported scale and oddly modern tools in older jobs.
- Audit ATS extraction, heading hierarchy, columns/tables, formatting artifacts, chronology order and text density.
- Output a factual audit and a list of what still needs verification. For audit mode stop here; do not create a rewritten document.

### Gate B — Employer and timeline research
- Research the actual employer and its business during **the candidate's stated dates**. Prefer official company pages, dated customer stories, annual reports and credible contemporary records; cite dated URLs.
- Identify likely engineering problem spaces only as **hypotheses** and write focused verification questions.
- Never change a hypothesis into an accomplishment because the employer has a published case study.
- Apply `references/company-research.md` and keep research notes separate from the candidate's own claims.

### Gate C — Engineering evidence interview
- For each major job, recover one or two real systems and identify users/actors, domain, architectural boundaries, data flows, integrations, runtime, hosting, scaling, security, testing, operations, constraints, tradeoffs and candidate contributions.
- Ask for concrete metrics with sources: before/after, unit, measurement window and method; distinguish baseline from target.
- Recover technical leadership with specific decision ownership, review scope and team size. Do not imply people management from mentoring.
- Use `references/engineering-interview.md`. Keep an evidence ledger using `templates/evidence-ledger.example.json` as a schema illustration (synthetic only).
- Unresolved critical facts block a submission-ready final; a conservative working draft is permitted if **explicitly labeled** and doesn't assert unverified architecture/metrics.

### Gate D — Evidence and accuracy review
- Classify claims as `verified` (objective evidence), `candidate_confirmed` (direct candidate confirmation), `source_reported` (original document only), `research_context`, `hypothesis` or `contradicted`.
- For output bullets, use only `verified` or `candidate_confirmed` evidence. Avoid using `source_reported` until confirmed when it implies concrete ownership or metrics. Clearly identify residual candidate-confirmed-but-not-independently-verified claims.
- Execute: `python .claude/skills/resume-architect/scripts/evidence_gate.py path/to/candidate.json` from repository root (or use the installed skill directory when copied to a personal skills folder). Do not override failing checks; correct the ledger and wording instead.
- Respect distinct roles and concurrent 1099 contracts. Treat unexplained overlap as a warning requiring validation before submission.

### Gate E — Author the resume
- Choose one target title per vacancy. Anchor the resume in the candidate's strongest real stack, not every technology they have seen.
- Create concise summary (3–4 lines), focused skills, reverse-chronological jobs, verified education, and optional selected projects only when employment attribution is clear.
- Aim for 5–7 substantive bullets for major roles; scale older roles down where warranted. Integrate different systems into cohesive accomplishment bullets **without project subheadings** unless the user requests them.
- Ensure seniority progression: early career implementation → mid-career system ownership → senior architecture, production operations and leadership.
- Use `references/writing-and-impact.md`; validate every bullet against ledger IDs. Keep 20–30% quantified only if actual evidence permits.
- Tailor to the JD by matching **verified experience** to responsibilities and vocabulary; never keyword-stuff skills unsupported in experience.

### Optional Gate E2 — JD alignment and bounded tailoring
- This is **opt-in**. If the user supplies no JD, execute normal rewrite/delivery unchanged. If the user provides a JD, confirm the target vacancy and read `references/jd-tailoring.md`.
- Run `python .claude/skills/resume-architect/scripts/jd_match.py work/candidate.json input/job-description.txt --output work/jd-match.json` (relative to repository root).
- Distinguish required/preferred JD terms, evidence-backed matches, real gaps, and unverified claims. Don't portray a keyword inventory as an ATS score.
- Copy verified baseline ledger to a new **private** tailored JSON; never overwrite baseline. Revise 10–30% of **editable narrative wording** by default, preferring a ~20% target. Some candidates may have <10% truthful room to change: report that rather than padding.
- Allowed: reorder sentence emphasis within a bullet, replace verified synonyms, highlight relevant proven technologies, focus the summary and skills on the JD, tighten unrelated detail. Do not alter employers, titles, dates, role count, bullet count, claim references, education, metric values, certifications, or work eligibility.
- Validate with `python .claude/skills/resume-architect/scripts/tailor_gate.py work/candidate.json work/candidate-tailored.json --jd input/job-description.txt --target 0.20 --report work/jd-tailor-report.json`. If validation fails, correct edits; do not relax the gate to hide unsupported claims.
- Preserve original resume and provide original-vs-tailored comparison, evidenced match gaps, change percentage, and a human review disclaimer. No promise of clearing or beating ATS.

### Gate F — Deliver and final QA
- Render ATS-friendly single-column DOCX and PDF when appropriate tools are available. Use semantic headings, plain-text contacts, standard bullets and consistent dates; generally target 2 pages for senior profiles but never sacrifice substance merely for the count.
- Optionally use `python .claude/skills/resume-architect/scripts/render_resume.py candidate.json output.docx` after the evidence gate. PDF conversion is optional and requires an installed converter; never claim a PDF exists until verified.
- Run `python .claude/skills/resume-architect/scripts/docx_audit.py output.docx` and visually inspect **every** page plus a plain-text PDF extraction. Look for orphan headings, broken glyphs, encoding entities, unusual whitespace, hidden tables and contact-data loss.
- Present a change summary, verified deliverables, outstanding verification questions, and a **clear readiness label**: Audit only, Working draft, Candidate-confirmed draft, or Submission-ready.
- Read `references/ats-and-delivery.md` before handoff.

## Output contract by mode

| Mode | Minimum output |
| --- | --- |
| audit | Findings with priority, evidence, exact changes, uncertain claims; no edited file |
| research | Dated employer context + cited sources + possible system hypotheses clearly separated |
| interview | Focused questions per system and metric; evidence gaps and source requests |
| rewrite | Coherent text draft + claim traceability + outstanding blockers |
| tailor | Optional JD coverage report, 10–30% bounded evidence-based revisions, diff and remaining gaps |
| validate | Pass/fail gate results + chronology/metric/bullet coverage issues |
| deliver | Validated DOCX/PDF if supported + QA report + limitations + readiness label |

Do not stop after generic advice if a source document and sufficient confirmed facts are present; complete the requested mode. If critical information is unavailable, deliver a labeled conservative draft and a precise verification checklist rather than inventing it.
