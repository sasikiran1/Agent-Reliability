# Benchmark feasibility assessment - 2026-10-28

Update: the later [continuation record](continuation-2026-10-28.md) supersedes installation and application-launch status below. Python 3.12 and offline evaluator/browser dependencies are installed; one real application startup subsequently crossed the RAM threshold and was explicitly stopped. Its revised cleanup safety check passed with mocks. No new agent benchmark task has run. The original assessment below is preserved as a dated record.

Decision: prioritize WebArena Verified as the first candidate workload. Do not start main collection. WorkArena++ is deferred for access and telemetry reasons. A full deployment alongside inference has not passed the resource gate. Publication feasibility also requires distinguishing this study from closely related work.

## Verified sources and host

Downloaded source checkouts, not installed Python packages:

| Project | Commit |
|---|---|
| WebArena Verified | 6473f72db5dcefc97b5725b59e734504edc28a21 |
| WorkArena | e885130962f61fb64ac305497996a46cfc7d18f0 |
| AgentLab | 8488c564eea0525aaff5dea189bb03a9b529546e |

Docker Engine 29.9.2 and Desktop 4.96.3 respond; WSL2 Ubuntu is available. Existing Ubuntu Python is 3.14.4. AgentLab declares Python >=3.11,<3.13, so that interpreter is incompatible with its declared support. WebArena Verified requires >=3.11. A separate Python 3.12 environment and fully resolved package lock are needed before installing the combined runner. No paid inference or external model endpoint is needed or authorized.

Host free physical RAM at inventory: 2390932 KiB (2.28 GiB); after image download: 1395860 KiB (1.33 GiB), with no models loaded and no containers running. WSL reports its own virtual memory pool; this must not be added to physical host RAM. Full raw host data is in data/feasibility/host.json and post-download-host.json. Available storage remains ample; RAM is the immediate gate.

## WebArena Verified

The pinned dataset has 812 tasks, 190 distinct intent-template IDs. Single-site task counts: Shopping Admin 182, Shopping 187, Reddit 106, GitLab 180, Map 109; 48 tasks use multiple sites. These are inventory counts, not executed tasks. The study's reproducible inventory and candidate split are in data/feasibility/task-inventory.csv and task-summary.json.

First candidate: Shopping Admin, because its documented image is the smallest of the state-changing applications considered. The downloaded image actually reports 4488579565 bytes (~4.18 GiB); the documentation table reports 2.9 GB. Preserve this discrepancy rather than equating documented sizes with local measurements. Immutable image:

`am1n3e/webarena-verified-shopping_admin@sha256:d0531dd27ed98d0c459ff9e88118bf2ed8b660b0ed99c38837db46c065a5be13`

The readiness script attempted a host-memory preflight and refused to launch because available RAM was below its 2 GiB start threshold. Raw outcome is in data/feasibility/environment/. There were zero container launches, model calls and benchmark tasks in this check. A launch failure cannot be attributed to the application because it was never started. The script now uses unique run directories for subsequent attempts. Its prospective 1536 MiB memory cap and 2 CPU cap are experimental interventions; if reached, an OOM/latency result under that cap is not normal application behavior. Do not weaken the gate to obtain a run.

Important validity issues in upstream source:

- Network-event and structured-answer evaluators assess defined benchmark outcomes, not a complete history of database commits. Retain official scores and add independent SQL/API state oracles, immutable effect-history capture, and checks for extra effects. An HTTP success is not sufficient proof of commit or absence of duplicates.
- The optimized forum image removes submission rate limits. It cannot represent an ordinarily protected service without explicitly restoring/measuring a comparable protection arm. Shopping Admin disables some mass-delete operations. Header-based auto-login also changes the interaction path. Record all these changes as workload conditions.
- Reset/cleanup names must not be assumed to restore database state. Implement and validate a named baseline database snapshot/restore and compare semantic state hashes before each trial. Caches, sessions and clocks require a separate declared policy. Controlled benchmark dates in task text are task data, not the real calendar date.
- Full deployment of all sites is unnecessary for the first feasibility check and unvalidated on this host. GitLab documents a 4 GB minimum recommendation; Map recommends >=4 GB and substantial external data. Do not launch the full suite simply because Docker works.

Original sources: [project](https://github.com/ServiceNow/webarena-verified), [environments](https://github.com/ServiceNow/webarena-verified/blob/6473f72db5dcefc97b5725b59e734504edc28a21/docs/environments/index.md), [evaluation](https://github.com/ServiceNow/webarena-verified/blob/6473f72db5dcefc97b5725b59e734504edc28a21/docs/evaluation/network_event_based_evaluation.md). Local checkouts preserve exact source text.

## WorkArena++

The current upstream README requires a gated ServiceNow instance dataset: submit a form, accept terms and await approval. Do not create an account or accept terms on the user's behalf. Source availability is not instance access. The README describes 682 compositional tasks; those are task classes/configurations, not 682 independent production incidents. Local inference is compatible in principle with a remote application, but we currently lack instance access, backend commit/queue telemetry and authorization for stress. Therefore defer this environment; no service-load or recovery claims can be supported from UI access alone.

Source: [pinned README](https://github.com/ServiceNow/WorkArena/blob/e885130962f61fb64ac305497996a46cfc7d18f0/README.md).

## Framework comparison

AgentLab is the candidate established browser-agent runner. Source pin is above. Its LiteLLM adapter accepts a base URL, but local Ollama behavior has not been executed or validated. In the pinned src/agentlab/llm/litellm_api.py, `_call_api` explicitly passes `num_retries=5`. Other adapters and parser helpers have separate retry loops. These are potential retry layers, not evidence they caused duplicate writes. Expose and log every active layer; do not label default framework versus no-retry minimal loop a causal framework comparison. First match actions, observations, prompts, model settings, retry policy and budgets; separately report the out-of-box configuration. An adapter patch changes the framework condition and needs its own code hash and diff.

## Next executable gates

1. Obtain stable memory headroom through the user's normal application management; do not kill unrelated processes or change system settings. Repeat the private readiness script with no concurrent downloads/inference. Measure idle and action-time application memory before proposing combined inference.
2. Prepare an isolated supported Python environment and lock dependencies. Validate official evaluators on included fixtures, then independently audit representative state-changing tasks with a direct-operation oracle. Neither fixture evaluation nor oracle execution counts as agent success.
3. Implement continuous cancellation/resource enforcement, bounded browser observations, target commit/queue instrumentation and durable traces. Validate these using a controlled known-effect harness, separate from empirical agent results.
4. Run the preselected development tasks; retain every failure and audit before expanding. Freeze the main task set and protocol only after feasibility, capability, runtime cost and sample-size assessment. If small models mostly fail, report that result; do not quietly choose only tasks they passed.

No benchmark capability, application harm, recovery delay or publication novelty has yet been demonstrated.
