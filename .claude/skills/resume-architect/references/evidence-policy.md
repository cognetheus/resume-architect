# Claim provenance and submission gates

## Evidence classes

| Status | Meaning | Resume usage |
| --- | --- | --- |
| `verified` | Verifiable work sample, employment record, metric report, or dated primary evidence | Allowed with matching scope |
| `candidate_confirmed` | Candidate directly and specifically attests to role, implementation, or contribution | Allowed, but not independently proven |
| `source_reported` | Only appears in an old resume or other unverified draft | Interview prompt; do not use for specific new architecture/impact claims |
| `research_context` | Public employer/product information, job ad, industry facts | Context only; cannot attribute to candidate |
| `hypothesis` | Plausible architecture, role or timeline guess | Interview prompt only |
| `contradicted` | Conflicting dates/evidence or refuted detail | Exclude and resolve |

A claim cannot be elevated by polishing its wording. An unverified project name remains a hypothesis even if it matches employer services.

## Evidence capture

Record for every relevant claim:
- `id`, `kind` (employment, implementation, leadership, technology, education, metric), `status`, `statement`.
- `evidence` entries with `type` and `ref`; primary documents, dated candidate interview notes, links to artifacts, sanitized architecture diagrams, or operations reports.
- `role_id` where applicable to constrain attribution and chronology.
- For a `metric`: `before`, `after`, `unit`, `period`, `method`, and what the numbers actually measure. A bounded production total can use `observed` instead of a baseline comparison, but must still include unit, period, method and a traceable source.

## Submission rules

- Every employment bullet references supporting claim IDs. All referenced claims must be verified or candidate_confirmed and apply to that employer.
- Quantified bullets must cite one or more metric claims and have evidentiary measurement context.
- Unexplained job overlaps and false experience-duration assertions require resolution.
- Directly supported, non-numeric facts may appear without impact statistics; no pressure to populate 30%.
- If original resumes disagree on identity, employer, degree or dates, don't silently pick one.
- Maintain a *private* candidate record. Do not include confidential client identifiers or protected information in a resume without permission.
- No blind substitution of current technologies into historical roles (e.g., contemporary model products in years before release).

## Evidence vs. inference example

Employer website: "We build a clinical trial platform." This is **research_context**. Candidate says: "I designed a validated ingestion service for protocol amendments using ASP.NET Core and SQL Server." This is **candidate_confirmed**, provided it matches the dates and personal contribution. Internal performance dashboard shows p95 420ms → 240ms during a specific release: metric can be **verified** with measurement method and period.

Do not assert the ingestion service or measured improvement unless the candidate confirms it and the supporting data exists.
