# Technical evidence interview (senior profiles)

Use brief, high-signal questions and adapt by discipline. Avoid forcing all questions when candidate already provided evidence.

## System identity
- What was the product or internal system, who owned it, and what period did you work on it?
- What was your scope: design, build, migration, production on-call, platform lead, mentoring, formal management?
- Which 2–3 components did you personally implement or change?

## Architecture and operations
- Draw the request/data path and name the source of truth. Which boundaries were synchronous vs asynchronous, and why?
- How were consistency, idempotency, retries, ordering, backfills and concurrency handled where relevant?
- What failed in production, and what was changed? Ask for a concrete incident or difficult migration.
- What was deployed where, and how were secrets, networking, identity, scaling, backup and observability managed?
- What was the security/compliance requirement and which specific control did you implement?
- Which tests and release gates actually ran? What did they catch?
- Which technology was primary vs limited exposure? What alternatives did you reject?

## Discipline lenses

**Backend/full stack:** request contract, GraphQL/REST decisions, caching invalidation, DB transactions, query plans, frontend rendering/performance, auth.

**Cloud/DevOps:** AWS/Azure resources actually configured; networking, IAM, Terraform state/modules, disaster recovery, deployment gates, budget and SLOs.

**AI/data:** source connectors, ingestion/delta indexing, chunking, vector/keyword/hybrid retrieval, tool use, prompts, grounding, evals, access control, tokens, latency and cost.

**Security:** data classification, authorization, tenant isolation, audit evidence, vulnerability fixes, incident investigation.

## Outcomes
- Ask "before vs after" for latency, cost, provision time, release frequency, incidents, data throughput, job success rate, manual time and customer impact.
- Ask measurement window, unit, baseline, observed result, tooling and how much change can be attributed to their work.
- If the person cannot supply measurements, describe an actual architectural result without numbers. Never estimate "reasonable" improvements.

## Leadership
- How many engineers, which roles, reporting relationship, which technical decisions, which reviews, what delegation, which cross-team dependency?
- Do not convert informal peer guidance into "managed a team."

## Exit criterion
Enough evidence exists when each primary job can support at least 5 strong truthful bullets, two substantial engineering constraints, one clear ownership decision and any included metrics are backed by observations. If not, publish a Working draft and targeted missing-evidence checklist.
