# Related-work and novelty screen - 2026-10-28

This is an initial screen of primary abstracts/repositories, not a completed systematic literature review. Reported findings below belong to their authors and are not independently replicated. arXiv availability is not proof of peer review. Full methods, code, model configurations, artifact licenses and exact versions still need assessment.

| Source | Overlap with our question | Consequence |
|---|---|---|
| [Where Does Exactly-Once Live?](https://arxiv.org/abs/2609.29095), submitted 2026-09-24 | Separates model, harness and tool-contract contributions in a deterministic sandbox with committed-effect scoring | Layer attribution and idempotency comparison are already studied; do not claim them as new |
| [UndoBench](https://arxiv.org/abs/2610.05622), submitted 2026-10-04 | Paired nominal/recovery trials, effect-history/state oracles and explicit competence/recovery separation | Need to reproduce or distinguish this design; conditional recovery alone is not a novel metric |
| [Verified Tool Calls Improve LLM Agent Reliability Under Non-Atomic Failures](https://arxiv.org/abs/2608.02645), submitted 2026-07-31 | Controlled injected non-atomic failures; verification and idempotency wrapper | A new retry wrapper on toy tasks would not establish an original contribution |
| [IdempotencyBench repository](https://github.com/gssanjana4/idempotencybench) | Repository describes duplicate-effect evaluation under several retry/redelivery modes | Inspect reproducibility and claim scope before creating redundant workloads; publication status unverified |
| [An Executable Benchmarking Suite for Tool-Using Agents](https://arxiv.org/abs/2605.11030), revised 2026-06-30 | Benchmark execution and evidence admission | **Withdrawn**; authors state substantive errors affect results and conclusions. Exclude as supporting empirical evidence; preserve status in the ledger |

Candidate contribution to investigate, not an established gap: test whether duplicate-effect and service-impact findings transfer from simulators to existing application implementations under unmodified normal execution; quantify what remains after ordinary protections and distinguish client/inference contention from target-service harm. A focused replication with boundary conditions is also valid. Novelty remains unproven pending full-paper review and broader search.

Before claiming a contribution: compare task realism, actual application commits, backend metrics, natural/controlled separation, baseline protections, model sizes, framework coverage, and artifact availability against these studies. Negative or inconclusive findings remain admissible. Do not choose a paper title asserting agent-induced outages before observing one.
