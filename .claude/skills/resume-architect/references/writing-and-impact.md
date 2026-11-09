# Senior resume writing standard

## Narrative

Use one targeted professional title. Summary: seniority, actual strongest languages/frameworks, systems/industry domain, cloud/data/AI depth, and leadership (only if true). Avoid generic adjectives and "passionate about" filler.

Write reverse-chronological experience. Each job is a coherent *engineering arc*, not a product catalog or an IT ticket list. Systems may influence bullets naturally without subheadings.

## Bullet formula

Strong structure:
**Action + concrete system/constraint + implementation decision + compact result (optional).**

Examples below are illustrative, never candidate facts:

- "Partitioned ingestion workloads by source and introduced idempotent upserts in PostgreSQL to prevent duplicate events during connector retries."
- "Reworked p95 API latency from 480 ms to 290 ms by reducing N+1 GraphQL resolution and optimizing a hot SQL path." [Only with validated measurements.]
- "Designed Azure landing-zone Terraform modules with remote state, guarded environment promotion and least-privilege deployment identities."

Avoid:
- "Developed scalable and robust applications using X, Y, Z to support business objectives."
- 50-word bullets ending in lengthy descriptions of how a department could do 4 extra activities.
- Eight project subheadings inside three jobs.
- Claiming architecture ownership for ordinary implementation tickets.

## Balance and specificity

- Most major jobs: 5–7 bullets; early roles can be 3–5. Follow explicit user constraints if reasonable.
- ~20–30% numeric if validated; zero is better than fabricated. Give units, baseline or data-set scale when informative.
- One or two technologies per bullet are usually enough; do not list every library.
- Show leadership/architecture through real decisions and production constraints, not labels.
- Favor measured engineering outcomes (p95 latency, RTO/RPO, dollars, query costs, incident frequency, throughput) over vague "efficiency."
- Balance architecture, delivery, operations, testing and collaboration according to target role.
- For concurrent consulting roles, explicitly label them and verify dates; don't disguise overlaps.
- Use real project names only when candidate confirms attribution and sharing is permitted.
- Role progression should be plausible for the period and seniority. Avoid "architected enterprise strategy" in an unverified junior role.

## ATS targeting

Parse the supplied JD into hard requirements, important capabilities and bonus skills. Map each to **verified claims** and note gaps. Include common synonyms naturally: "ASP.NET Core (.NET)" once; "AWS ECS" rather than a 20-service list. Do not claim every keyword to artificially pass a filter.

## Quality test

Read each bullet aloud: Can an interviewer ask "why that architecture," "what broke," "how did you measure," and "what did **you** do" and receive a factual answer? If not, mark it for revision or verification.
