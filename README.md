# Agent Reliability Study

Independent, local-inference research project begun 2026-10-28. Research question: when useful agent work repeats, what caused it and what measurable harm followed?

**Testing on another laptop:** follow [minimal installation and reproduction instructions](docs/other-laptop.md). Use requirements-local.lock for the first experiment; the larger benchmark/framework lockfiles are optional and require restoring their pinned vendor source.

**Latest result:** the [first auditable multi-step experiment](docs/first-auditable-experiment.md) is complete: Qwen 2/2 correct, Llama 0/2 correct, zero duplicate committed effects in four predefined controlled tasks. Both earlier single-create round trips succeeded. These are development observations, not a main-study or industry failure rate. See [results CSV](results/pilot-results.csv), protocol, raw traces and SQLite state in results/live-local-*.

Current phase: benchmark feasibility and protocol development, **not main collection**. The user has no genuine repository task and requested a study suitable for research publication. No natural task has been observed. No industry frequency, publication novelty or product need is established. Natural recovery impact not observed.

See [protocol](docs/protocol.md), [source ledger](docs/public-evidence.csv), [status](docs/status.md), and the verified [hardware inventory](data/hardware-initial.json).

The [benchmark feasibility assessment](docs/benchmark-feasibility.md) recommends WebArena Verified as the first candidate. Its pinned dataset contains 812 tasks; none have been executed by our agents. Python 3.12, locked evaluator/browser dependencies and Chromium are now installed. Offline checks reproduced supplied success/failure scores and rejected a corrupted answer. A private application startup crossed the RAM stop threshold and was stopped; combined application/inference feasibility is still unproven. See the [latest continuation record](docs/continuation-2026-10-28.md). WorkArena++ remains deferred. The [related-work screen](docs/related-work.md) identifies close prior work; novelty remains unproven.

**Budget: spend no money.** Experimental inference stays local. No paid APIs, subscriptions, hosted inference, rented GPUs, purchases or automatic paid fallback.

Run from this directory in PowerShell:

```powershell
powershell -NoProfile -File src/pilot.ps1 -Model qwen3.5:4b
powershell -NoProfile -File src/pilot.ps1 -Model llama3.1:8b
powershell -NoProfile -File src/checksums.ps1
```

Benchmark preparation (installed Ubuntu/WSL Python; no Python dependencies needed for inventory):

```powershell
wsl -d Ubuntu -- python3 /mnt/c/Users/kiran/Downloads/Agent-Reliability/src/benchmark_inventory.py
wsl -d Ubuntu -- python3 -m unittest discover -s /mnt/c/Users/kiran/Downloads/Agent-Reliability/src -p test_benchmark_inventory.py
powershell -NoProfile -File src/environment_feasibility.ps1
```

The environment script only attempts a bounded, private application readiness check and stops the study container afterward. Its preflight requires 2 GiB free host RAM. Use a process-only execution-policy bypass only when authorized. Do not rerun the model smoke test while memory is constrained or while downloading images.

Installed Windows evaluator check: `.venv/Scripts/python.exe src/validate_evaluator.py`. This evaluates supplied traces offline, not new agent runs. Dependency inputs and resolved hashes are in requirements-pilot.in and requirements-pilot.lock. `src/test_environment_cleanup.ps1` validates cleanup with mocked operations; it launches no real container.

The pilot is a constructed read-only tool-calling compatibility check, not a natural incident. It reads the project's real protocol through an allowlisted tool. It cannot execute arbitrary commands or write to another repository. Downloads use the network; inference only uses 127.0.0.1. No hosted inference credentials are used.

Required next steps: stable resource headroom; supported isolated Python environment and package lock; independent state/effect oracles; instrumented target service; matched minimal/framework comparison; direct-operation controls; randomized protected/unprotected trials; resource/queue sampling and actual overlap measurement. The benchmark template split is reproducible and validated; candidate tasks have not been evaluated. Do not run main collection until the protocol and task manifest are frozen. Neither the small setup runner nor the inventory is a finished research experiment.
