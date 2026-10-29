# Protocol v0.2 - research design, not frozen for main collection

Date: 2026-10-28. Supersedes v0.1 (archived as protocol-v0.1.md). This is a proposed design, not a preregistration or evidence of completed collection. Freeze this file and the task/configuration manifests by SHA256 before main collection; amendments must have a new version, date and reason. Pilot results cannot silently enter the main dataset.

## Evidence separation

Public track: original operator reports, maintainer discussion and documentation. Record report date, affected version, status at retrieval, raw evidence, alternatives, harm and denominator. A proposal or reported retry is not a confirmed harmful incident.

Natural track: user-requested useful work, normal configuration, no injected faults or retry prompts. User confirmed no repository to fix; no genuine tasks are available at present. Natural collection is optional and remains zero, not replaced by benchmark episodes. Do not search unrelated personal folders for tasks. Study-created code fixes and published benchmark tasks are controlled tasks.

Controlled track: constructed tasks, reproductions, replay, artificial latency/faults, concurrency sweeps. Record every intervention and live_model true/false. Never pool tracks for rates.

## Definitions and adjudication

Correct completion requires a predeclared application-state assertion or independent test. Agent completion text is insufficient. Unnecessary repetition requires an adjudicator to establish that repeated work was not needed for the goal or verification. Duplicate effects require distinct committed effect IDs for one intended operation. Same arguments alone do not prove either.

Harm requires observed duplicate committed changes, reduced throughput, increased errors, unrelated-request latency, or recovery delay against a relevant control. Separate model-requested repetition, SDK retry, framework replay, scheduler redispatch, client timeout, application retry and hardware/context limits. Unknown source stays unknown.

## Pilot limits

One model loaded, one request at a time; num_ctx=4096; num_predict=512 per call; maximum 3 calls, 12 tool calls, 180 seconds per request, 10 minutes per task. Temperature=0, seed=20261028 where honored. Keep all successes, errors, cancellations and invalid outputs. Stop on unsafe write, >90% physical RAM pressure sustained 30 seconds, <1 GiB free RAM, or unavailable instrumentation. Never kill unrelated applications to free memory. Record actual runtime settings before main collection. No automatic transport retries.

Pilot compatibility task: read this protocol with the allowlisted read_protocol tool and summarize the evidence tracks. Correctness here is the tool result matching the file hash; summary quality is separately ungraded. No service-harm conclusions from this task.

## Workloads, development split and capability

First candidate is pinned WebArena Verified, starting with single-site Shopping Admin, subject to resource and oracle gates. WorkArena++ is deferred pending instance access, terms and target telemetry. Candidate established runner is pinned AgentLab; local Ollama integration is not yet validated. Exact commits and image digest are in benchmark-feasibility.md and source-manifest.json. Package versions remain unresolved; source pins alone are insufficient to run the experiment reproducibly.

Pinned dataset: 812 tasks and 190 templates. Deterministic seed 20261028 assigns 38 templates to development and all other templates to candidate holdout. Split globally by intent_template_id, not episode. Candidate pilot IDs are 708, 0, 107, 41, 119, 289, 196, 472. This sample is for feasibility only and is not balanced or representative. Selection occurred before model outcomes. Main tasks require a separate preregistered stratified sample by site, mutation/retrieval, template and compositional demands; publish all exclusions and reasons. Preserve expected-unachievable tasks as their own stratum. Do not select main tasks based on successful model runs.

Begin development with 4096 context and one inference request. Document observation token accounting and unmodified context requirements. If task observations do not fit, mark resource/context-ineligible for that configuration; do not silently truncate or call it an application outage. Any larger-context or output-budget arm requires separate feasibility and recording. The 512-token output cap from the setup smoke check is not assumed adequate for benchmark planning. Select and freeze budgets from development evidence before the holdout is touched.

First require independent oracle/direct-control completion. Then measure agent nominal capability on development tasks before recovery claims. Report all-task correctness and harms as primary denominators. For controlled recovery, additionally report paired results restricted to tasks where the paired nominal execution succeeded; explicitly identify this conditional estimand. Never silently discard incapable, failed, stopped or incomplete episodes.

## Main collection design (pending implementation and freeze)

The old 10-task/60-minute budget is only a development feasibility cap, not sufficient justification for the main sample. Select main sample size after measuring development runtime, variance, within-template clustering and a practically meaningful effect or desired precision. Freeze the total task budget and fixed stopping rule before main outcomes are inspected. If resources cannot meet the precision target, report wider uncertainty rather than promise publication-grade statistical power. Episode repetitions are nested within tasks/templates and are not independent task observations.

Compare a minimal loop and pinned AgentLab with the same model, action interface, observations, prompts where possible, token/action/time budgets and explicit retry policy. Keep a separate out-of-box framework arm if desired, labeled as a configuration bundle, not isolated framework causation. Record package lock, code revision, adapter patch, image digest and runtime/model digest. Do not compare unpinned runs. Verify all inference endpoints resolve locally; no external judge/user model or fallback is permitted. Run models sequentially, with downloads completed before timed collection.

Controlled comparison: equivalent direct tool operations, minimal loop, framework. Save the unprotected development baseline before implementing protections; in the main study randomize baseline and treatment order within task/template/model blocks using seed 20261028 to avoid temporal confounding. No-fault trials and fault-injected trials remain separate strata. Name and justify each injected delay, dropped acknowledgment, worker termination or redelivery. Do not inject faults solely to guarantee a harmful result.

Test ordinary protections before proposing new ones: idempotency enforced at the relevant application boundary, bounded retries (maximum 2 additional attempts), exponential backoff with jitter, and concurrency/rate limits as separate arms plus a declared standard-protection bundle. Per-call and logical-workflow idempotency are distinct. A browser wrapper that drops identical clicks is not equivalent to application idempotency and can suppress legitimate actions. Preserve native protections; if a benchmark image removes a rate limit, disclose and separately restore/test a documented condition. Defer unavailable protections rather than relabel custom code as standard application behavior.

Reset disposable application state from a validated database snapshot; prove semantic equivalence before each run. Clock/cache/session reset policy must be fixed. Include several workflow types as capacity permits; a single Shopping Admin result cannot fulfill the original repository/document/job breadth or support cross-domain generalization. Sessions 1, then 2, then 4 only if resource gate passes. Multiple queued sessions are not multiple inference workers. Measure request enqueue/start/end and runtime scheduling evidence; absent server start timestamps, actual overlap is unknown.

Collect target service warm-up 60 seconds and baseline 5 minutes. For relevant degradation define recovery as five consecutive 1-second windows meeting baseline p95 latency +20%, throughput >=90% baseline and no excess errors. These are provisional experimental thresholds, not product requirements; use workload SLOs if supplied and freeze before treatment. Observe up to 5 minutes after fault removal; censored recovery is not successful recovery. Do not introduce degradation in natural tasks. If none occurs, report: natural recovery impact not observed.

## Trace and analysis requirements

JSONL events: task_id, track, live_model, session_id, event_id, parent_attempt, retry_source, UTC timestamp, monotonic elapsed, model/tool request IDs, sanitized arguments, error, committed_effect_ids, final_state_hash. Capture model input/output, prompt/eval token counts, done_reason, duration breakdown, explicit output cap, context settings. Truncation remains unknown unless runtime/token evidence establishes it; capped output is separate. Raw private inputs remain local; record redaction policy before genuine tasks.

Sample CPU/RAM/GPU/VRAM and process metrics at 1-second intervals; runtime loaded model/context/VRAM before and during calls. Distinguish inference queueing/load/prefill/decode from application queue/service time. Target service must expose throughput, queue depth, p50/p95/p99, errors and independent unrelated-request probes. No target telemetry means harm not assessed, not zero.

Host/app colocation can confound service slowdown with shared CPU/RAM pressure. Record both and compare service-only direct controls, recorded-action replay without inference, and live inference conditions. A replay remains a controlled diagnostic, not equivalent to live feedback. If the host cannot isolate these mechanisms adequately, label causal attribution inconclusive and narrow the claim. Never infer target queue depth from client waiting time.

Retain the official benchmark evaluator score, but require independent database/API state assertions and effect history to establish correct writes and extra committed effects. Validation reads run outside the agent and are tagged separately. Test each oracle against a known correct state, an extra duplicate effect, a wrong-value state and a partial state before using it. Network requests, submitted forms and model text alone do not certify committed effects. Blindly compare final state plus history: two writes can cancel each other in final state.

Report completed/attempted, affected/observed and tool calls/successful goal per cell, medians and tails, Wilson 95% intervals for proportions, paired differences for controlled arms. Missing data remains missing. A 0/n result does not prove absence. Reconstruct important timelines and test competing causal explanations with direct controls.

For clustered task samples, use intervals resampled at template/task level; Wilson intervals apply only when the stated independent Bernoulli assumption is justified. Report success-conditioned tool calls alongside total calls and failed-task cost to avoid survivor bias. Use paired task-level differences and template-cluster uncertainty for randomized arms; specify primary endpoints, correction for multiple secondary comparisons and any equivalence/noninferiority margins before main collection. Timing benchmarks require enough independent windows and repeated blocks; a single short readiness trace cannot support throughput/tail claims. Setup rows are never included in task-success or harm rates.

## Publication and novelty gate

Primary proposed outcomes: affected-task fraction with independently confirmed duplicate effects, and measured application/unrelated-request impact under specified conditions. The claim is scoped to selected tasks, local small models and pinned configurations. Review closely overlapping work in related-work.md before claiming novelty. A replication with transparent boundary conditions or null findings is acceptable; paper acceptance is not a study outcome we can guarantee. No public-site load tests, actual payments or public writes are allowed. Human production incidents are not required for a controlled empirical paper and cannot be manufactured.

Future intervention evaluation must preserve correctness, bound duplicate effects and unrelated-user regression, and show repeatable benefit beyond standard protections. Set numerical benefit thresholds from measured baseline and actual user SLOs; none can be justified yet.
