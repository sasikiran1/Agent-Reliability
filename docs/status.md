# Initial status

## Newest evidence - first auditable experiment

See [first auditable experiment](first-auditable-experiment.md). Four predefined multi-step live development trials completed: Qwen 2/2 correct, Llama 0/2 correct (invalid identifiers/dependency order, then prose instead of tool completion); no duplicate committed effects. Two separate earlier single-create live trials succeeded. All six live-trial evidence chains and saved SQL state passed audit. Ten multi-step no-model readiness/measurement/cleanup checks passed; constructed single/duplicate/idempotency controls passed separately. Both warmed models fit alongside the lightweight native application while sampled free RAM stayed above the unchanged threshold. No framework run, public load test, service-harm measurement or main-study trial occurred. Earlier entries are historical and their zero-live-task counts are superseded.

## Latest continuation

See [2026-10-28 continuation](continuation-2026-10-28.md) for newer evidence: supported Python and evaluator/browser installation, three passing offline evaluator checks, an actual private application startup stopped at the RAM threshold, and a corrected/tested cleanup harness. Earlier chronological entries below remain as historical records. Zero new benchmark-agent tasks and zero main-study trials have run. Budget is explicitly zero; all experimental inference stays local.

## Current phase update - benchmark feasibility

The user confirmed no repository is available to fix and selected a publication-oriented empirical study. The pending repository request is closed; no natural tasks are currently available. See benchmark-feasibility.md and protocol v0.2 for the revised plan. Prior setup observations below remain unchanged.

Downloaded and pinned WebArena Verified, WorkArena and AgentLab source; inventoried all 812 WebArena Verified tasks across 190 templates; generated a pre-outcome template split and eight candidate development tasks. These counts are dataset inventory, not experimental observations. WorkArena++ requires approved instance access and remains deferred. AgentLab requires a supported Python 3.11/3.12 environment; installed Ubuntu Python is 3.14.4. No framework packages have been installed.

Downloaded and pinned Shopping Admin application image. The readiness attempt refused to start because host RAM was below 2 GiB; post-download free RAM measured 1395860 KiB. No container was launched and no benchmark task ran. Zero current benchmark results is not evidence of either harm or safety. Model inference remains unloaded. Do not run concurrency tests or weaken the resource gate.

Related-work screen found directly overlapping studies; novelty remains unproven. The executable benchmarking-suite paper arXiv:2605.11030 is withdrawn and is excluded as empirical support. Full literature review remains outstanding.

Three automated inventory checks passed: exact dataset coverage/checksum, template-level development/holdout isolation, and candidate pilot eligibility. PowerShell readiness-script syntax was checked without launching it. These validate preparation only; they do not validate benchmark success or reliability findings. Checksums cover the study and downloaded source checkouts, excluding Git metadata and generated caches.

Verified local Ollama 0.40.10; upstream latest resolved to 0.40.12 on 2026-10-28. Preserve installed version for the pilot; an upgrade would be a new condition. Windows 11 Home, Ultra 9 185H, 16 cores/22 logical processors, 15.42 GiB usable RAM. Initial free RAM approximately 2.29 GiB. C: free 785226891264 bytes (731.3 GiB); capacity 992040972288 bytes. RTX 4070 Laptop GPU 8188 MiB, driver 621.01; initial VRAM use 1123 MiB. See raw inventory for exact collection time.

Initial sandbox hardware checks were denied; retried with approval and preserved verified output. Python aliases were found, but a functioning Python installation has not been established. PowerShell is used for dependency-free pilot instrumentation.

Public evidence so far supports plausible mechanisms and operator reports, not a measured population rate. No confirmed operator postmortem with independently measured unrelated-user harm has yet been established in this search. No solution/product recommendation is justified.

Natural tasks attempted: 0. Controlled main-study tasks attempted: 0. Setup smoke checks are stored separately. Framework comparison, service harm, recovery, concurrency, three-workflow coverage and genuine repository pilot remain outstanding. This is an honest project start, not a completed study.

## Setup smoke outcome

One live Qwen setup attempt, cancelled after sampled free RAM fell below 1 GiB (955416 KiB). The first response requested read_protocol correctly, but the round trip did not finish. Last model event: 2026-10-28T18:57:33Z; total model duration 29.27 s, load 13.39 s, prompt evaluation 14.87 s, decode 1.00 s, 272 input and 58 output tokens, done_reason=stop. Model advertised tools; runtime reported 4096 context and 3140495604 VRAM bytes. GPU utilization and memory samples are in the raw resource JSONL. The driver reports total device memory, which also includes other applications.

The runner stalled after recording the first model response and before recording the tool result; the exact blocking operation is unproven. Cancellation was manual after reviewing telemetry; the original sampler did not automatically enforce the mid-request RAM threshold. The runner was amended to bound the loaded-model query to 10 seconds and recheck RAM after inference, but this revision has not been rerun. This is a harness/resource limitation, not evidence of target-service degradation. Llama inference was deferred. Qwen was explicitly unloaded; free RAM afterward was 3255476 KiB. Model downloads overlapped setup and are a confound for setup performance; exclude this run from performance comparisons.

Initial script launch was blocked by Windows execution policy before inference. A process-only bypass was approved for the smoke run; no persistent policy was changed. Preserve this setup error separately from the model attempt. Main collection requires a cancellable request plus continuous automatic resource enforcement, durable cancellation records, parent-attempt linkage and target telemetry; the current runner is for setup only.

Exact local model digests (both Q4_K_M; both advertise tools in saved /api/show responses):

- qwen3.5:4b: d8b0f5e9760cd1682034f292d7ef72ec46f432149be0df7574bf2d6e92e38c04
- llama3.1:8b: 46e0c10c039e019119339687c3c1757cc81b9da49709a3b3924863ba87ca666e

Catalog short hashes are not substituted for these local full digests. Full local metadata is in data/models-final.json and data/show-*.json.
