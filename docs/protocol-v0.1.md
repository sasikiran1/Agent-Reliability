# Protocol v0.1 — pilot only

Date: 2026-10-28. Freeze this file by SHA256 before main collection; amendments must have a new version and date. Pilot results cannot silently enter the main dataset.

## Evidence separation

Public track: original operator reports, maintainer discussion and documentation. Record report date, affected version, status at retrieval, raw evidence, alternatives, harm and denominator. A proposal or reported retry is not a confirmed harmful incident.

Natural track: user-requested useful work, normal configuration, no injected faults or retry prompts. Inventory: empty study workspace; local Ollama has two Gemma variants but requested Qwen/Llama were absent initially; user requested a repository fix, path/bug pending. Do not search unrelated personal folders for tasks. Study-created code fixes are constructed tasks.

Controlled track: constructed tasks, reproductions, replay, artificial latency/faults, concurrency sweeps. Record every intervention and live_model true/false. Never pool tracks for rates.

## Definitions and adjudication

Correct completion requires a predeclared application-state assertion or independent test. Agent completion text is insufficient. Unnecessary repetition requires an adjudicator to establish that repeated work was not needed for the goal or verification. Duplicate effects require distinct committed effect IDs for one intended operation. Same arguments alone do not prove either.

Harm requires observed duplicate committed changes, reduced throughput, increased errors, unrelated-request latency, or recovery delay against a relevant control. Separate model-requested repetition, SDK retry, framework replay, scheduler redispatch, client timeout, application retry and hardware/context limits. Unknown source stays unknown.

## Pilot limits

One model loaded, one request at a time; num_ctx=4096; num_predict=512 per call; maximum 3 calls, 12 tool calls, 180 seconds per request, 10 minutes per task. Temperature=0, seed=20261028 where honored. Keep all successes, errors, cancellations and invalid outputs. Stop on unsafe write, >90% physical RAM pressure sustained 30 seconds, <1 GiB free RAM, or unavailable instrumentation. Never kill unrelated applications to free memory. Record actual runtime settings before main collection. No automatic transport retries.

Pilot compatibility task: read this protocol with the allowlisted read_protocol tool and summarize the evidence tracks. Correctness here is the tool result matching the file hash; summary quality is separately ungraded. No service-harm conclusions from this task.

## Main collection design (pending implementation and freeze)

For each approved workflow/model/runner configuration: initially 10 tasks or 60 minutes, whichever occurs first. Preserve cancellations and setup errors with separate counts. Natural task availability determines achievable denominator; do not replace missing natural work with synthetic examples. Compare minimal loop and a pinned established framework with retry settings exposed. Record package lock, code revision and runtime/model digest. Do not compare unpinned runs.

Controlled comparison: equivalent direct tool operations, minimal loop, framework; unprotected baseline first saved immutably. Then idempotency, bounded retries (maximum 2 additional attempts), exponential backoff with jitter, and concurrency/rate limits as separate recorded arms. Randomize within blocks using seed 20261028; reset disposable application state from the same snapshot. Include repository, document and job workflows. Sessions 1, then 2, then 4 only if resource gate passes. Multiple queued sessions are not multiple inference workers. Measure request enqueue/start/end and runtime scheduling evidence; absent server start timestamps, actual overlap is unknown.

Collect target service warm-up 60 seconds and baseline 5 minutes. For relevant degradation define recovery as five consecutive 1-second windows meeting baseline p95 latency +20%, throughput >=90% baseline and no excess errors. These are provisional experimental thresholds, not product requirements; use workload SLOs if supplied and freeze before treatment. Observe up to 5 minutes after fault removal; censored recovery is not successful recovery. Do not introduce degradation in natural tasks. If none occurs, report: natural recovery impact not observed.

## Trace and analysis requirements

JSONL events: task_id, track, live_model, session_id, event_id, parent_attempt, retry_source, UTC timestamp, monotonic elapsed, model/tool request IDs, sanitized arguments, error, committed_effect_ids, final_state_hash. Capture model input/output, prompt/eval token counts, done_reason, duration breakdown, explicit output cap, context settings. Truncation remains unknown unless runtime/token evidence establishes it; capped output is separate. Raw private inputs remain local; record redaction policy before genuine tasks.

Sample CPU/RAM/GPU/VRAM and process metrics at 1-second intervals; runtime loaded model/context/VRAM before and during calls. Distinguish inference queueing/load/prefill/decode from application queue/service time. Target service must expose throughput, queue depth, p50/p95/p99, errors and independent unrelated-request probes. No target telemetry means harm not assessed, not zero.

Report completed/attempted, affected/observed and tool calls/successful goal per cell, medians and tails, Wilson 95% intervals for proportions, paired differences for controlled arms. Missing data remains missing. A 0/n result does not prove absence. Reconstruct important timelines and test competing causal explanations with direct controls.

Future intervention evaluation must preserve correctness, bound duplicate effects and unrelated-user regression, and show repeatable benefit beyond standard protections. Set numerical benefit thresholds from measured baseline and actual user SLOs; none can be justified yet.
