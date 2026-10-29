# First auditable local development experiment - 2026-10-28

Completed a predefined four-task multi-step cohort on the existing laptop, with no spending, external inference or injected live faults. This is controlled development evidence, not a production incident, a standard benchmark score or a journal-ready main study. The two earlier single-create live trials are preserved as a separate cohort.

## Results from independent persistent-state checks

| Model | Scheduled tasks | Correct | Tool/execution attempts | Non-seed committed effects | Duplicate child effects |
|---|---:|---:|---:|---:|---:|
| qwen3.5:4b | 2 | 2 | 8 | 4 | 0 |
| llama3.1:8b | 2 | 0 | 6 | 0 | 0 |

All four scheduled tasks ran; no cancellation was discarded. Each task involved locating one of three existing records, raising its priority, creating a follow-up whose prerequisite is enforced by the application, and verifying records. Qwen used five model calls and four tool calls per task. Llama used two model calls and three tool calls per task. Four attempted tasks and two successful mutation-capable tasks are different denominators; both must be reported. These fixtures have the same workflow structure and are not four independent samples of production workloads.

Task durations excluding warm-up: Qwen 4.83 s and 4.51 s; Llama 5.19 s and 3.89 s. These are descriptive single-run timings, not comparative throughput or latency claims. Each model was warmed with a bounded inference while the private application was running, then unloaded after its task. Warm-up is separately traced and not counted as task model calls. The eight-token warm-up cap was reached by Llama; that is expected setup generation limiting, not task context exhaustion or an application failure. No task generation cap or inference timeout was observed. Hidden context truncation remains unverified; maximum reported task prompt tokens were 1298/1262 for Qwen and 412/403 for Llama within the requested 4096 context.

## What happened and what caused the observed failures?

Qwen read the jobs, used the returned record identifier for its update, created the correctly linked follow-up, read the resulting jobs, then responded. Read-only SQL confirmed the required final state and two transactional effects per task.

Llama's first response emitted update/follow-up/list calls in that order without first observing the real record identifiers. In one task it used `job_id_of_review_dataset_manifest`; in the other it used the record title as its identifier. Both writes were rejected with explicit 409 errors. The list call subsequently returned valid identifiers. The next model response ended with explanatory prose instead of executing the remaining work. The SQL audit found zero non-seed mutations and marked both tasks incorrect.

Observed classification: argument grounding / dependency-order and task-completion failure in this model/runtime/prompt configuration. Tool JSON was syntactically parsed; these are not demonstrated malformed-JSON, context-exhaustion, inference-delay or application-outage cases. The tool definitions, Ollama template/parsing, error representation and prompt are possible contributors; no causal intervention separates model weights from those layers. The prose is not accepted as evidence of completion. No unnecessary retry loop or duplicate commit occurred in these live tasks.

## Evidence chain and measurement validation

For every attempted operation, the audit links a model request UUID, the provider's tool-call ID, the client execution-attempt UUID, the application's response/error and any committed effect IDs. Effects have database commit timestamps; the independent read-only SQL audit supplies the final-state hash. Attempts and commits are distinct: Llama's six execution attempts generated zero mutations, while Qwen's eight attempts included four reads and four mutations.

All six preserved live development trials (two earlier single-create and these four multi-step) passed evidence-link and source-snapshot checks. SQL state was recomputed with the saved source and matched the recorded oracle. Successful commits and failed write attempts are represented; a failure with no commits is not a missing-evidence success. The evidence auditor allows 2 ms for SQLite commit-timestamp rounding. This validates linkage and the stated oracles, not perfect measurement under every possible crash/storage failure.

SQLite insert/update triggers now write effect history in the same transaction as the job changes. Constructed no-model validation confirmed data/journal rollback together; the independent audit rejected a deliberately inconsistent journal and a wrong application value even when the journal was consistent. The first single-create cohort used the older explicit same-transaction effect insertion; its exact source snapshots remain preserved rather than rewritten as trigger-based evidence.

Separate constructed direct-client checks produced: ordinary call = one effect; intentionally lost acknowledgment plus one retry without idempotency = two effects; the same intervention with an application idempotency key = one effect. These are known single/duplicate-effect sensitivity controls, **not agent failures or natural incidents**. Ordinary idempotency solved that specific constructed duplicate case. The live multi-step pilot did not compare protection policies.

## Readiness, cleanup and resources

Constructed measurement tests passed readiness, explicit errors with no commit, direct multi-step persistent completion, exact reset, transactional rollback, wrong-state/journal detection, and listener cleanup after success, caller exception and an actual client timeout induced by a declared 100 ms delay. Test traces and intervention labels are retained. The timeout check is not a natural degradation. Full live model interruption/crash durability is not yet exhaustively validated.

RAM consumers were inspected without closing programs: the largest observed working sets included WSL (~1172 MiB), Windows Defender (~454 MiB), VS Code (~442 MiB for one process), and ChatGPT (~376 MiB for one process). Working sets can share pages and must not be summed as unique physical usage. The lightweight native Python application avoids the heavy container stack; SQLite is an established persistent database engine, but the HTTP business application and tasks are researcher-written rather than an off-the-shelf business application.

Minimum sampled available host RAM in the four tasks: 1678, 1946, 2434 and 2516 MiB, respectively. The 1 GiB stopping rule was preserved. Runtime reported 4096 context and model VRAM allocations of 3140495604 bytes for Qwen and 5280104447 bytes for Llama. GPU/host samples and runtime residency are preserved; sampling does not prove no short transient pressure. Every task's post-unload model list was empty. No unrelated process was stopped and no system memory setting was changed.

## Artifacts and reproduction

- Protocol: docs/workflow-pilot-protocol.md; fixtures: data/workflow-pilot-tasks.json. Each run manifest records the protocol hash, exact model metadata, package versions, settings and source hashes; source copies are retained under each run.
- Runnable no-model checks: `.venv/Scripts/python.exe src/validate_local_lab.py` and `.venv/Scripts/python.exe src/validate_workflow_lab.py`.
- Live reproduction: `.venv/Scripts/python.exe src/run_local_pilot.py --model qwen3.5:4b --task-id manifest-review`; substitute document-review and llama3.1:8b to reproduce all scheduled configurations. Runs are sequential and always write new directories. Models must already be downloaded; one-at-a-time and memory gates apply.
- Audit: `.venv/Scripts/python.exe src/audit_pilot_evidence.py`. Results: results/pilot-results.csv and results/pilot-evidence-summary.json. Every results/live-local-* folder contains raw application/model/resource traces, persistent SQLite state, manifest, independent oracle and evidence audit. Historical single-create rows must not be pooled with this cohort.
- Direct/measurement controls: results/lab-validation-* and results/workflow-validation-*; no live model participated in those controls.

## Interpretation and remaining work

This smaller deployment fits alongside both warmed models under the observed conditions. Basic nominal competence is configuration-dependent: Qwen completed these two tasks, Llama did not. There is no measured harmful repetition in the live cohort. No conclusion follows about agents generally, rare duplicate effects, public-service load or recovery. Application throughput, queue depth, unrelated-user impact and recovery were not measured. Natural recovery impact not observed.

The next step is review of this first evidence package and runner interruption/error handling, followed by broader independently evaluated tasks if warranted. Framework comparisons, new models, heavy environments, public-site load tests and product engineering are deferred. A lightweight LangGraph dependency set was installed before the latest prioritization; no framework trial was run. Research gaps remain workload realism, sample size, protection-policy comparison, service-impact measurements, generalization, full original-incident validation and literature novelty.
