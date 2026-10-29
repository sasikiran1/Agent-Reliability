# Continuation - 2026-10-28

Current phase: setup and application feasibility, not benchmark collection. Budget is explicitly zero: no paid APIs, hosted inference, rented GPUs, subscriptions or purchases. Routine authorized setup proceeds autonomously. No unrelated applications were stopped or system memory settings changed.

## Supported local runtime

Installed project-local uv 0.13.6 and CPython 3.12.16, created .venv, resolved hash-locked evaluator/browser dependencies, installed the pinned WebArena Verified source (package metadata version 1.2.3), Playwright and Chromium. AgentLab remains source-only; its separate environment and dependency lock are outstanding. Exact package versions are in data/setup/evaluator-validation/summary.json and requirements-pilot.lock. Source commits remain unchanged. uv reported Python shims outside PATH; no shell-profile/PATH change was made. Chromium was downloaded into Playwright's normal per-user browser cache.

Source for uv installation options: https://docs.astral.sh/uv/getting-started/installation/ . The official Windows binary archive at release 0.13.6 was downloaded directly; no remote installer script was executed. Installation/download logs are retained in data/setup. No inference API was called in this continuation.

## Offline evaluator checks

All three checks passed: supplied fixture 107 reproduced failure, fixture 108 reproduced success, and fixture 108 with deliberately corrupted counts failed. These are upstream provided traces plus a researcher-created negative control, not new agent tasks. Template 270 is in the development partition; no holdout execution occurred. This validates the answer evaluator on these examples, not application commits, general evaluator correctness or our agents' capability. Run `.venv/Scripts/python.exe src/validate_evaluator.py` to reproduce; raw result JSONs and package manifest are preserved under data/setup/evaluator-validation.

## Private application attempt

A fresh preflight at 19:23Z refused launch with 1983660 KiB free RAM. After downloads/installations completed, another preflight at 19:25Z passed with 2606224 KiB and launched Shopping Admin on loopback with the declared 1536 MiB/2 CPU limits. At 22.5 seconds, free host RAM sampled 1003976 KiB, below the 1 GiB stop threshold. No model participated. Sampled container memory reached 1.359 GiB; this is a sampled maximum, not a continuous peak. Raw artifacts: data/feasibility/environment-20261028-192548-468/.

Health requests returned 404. Source inspection shows the control endpoint is `/status`, while an example documentation page suggested `/health`. No application-readiness conclusion can be drawn from these responses, and no site operation or benchmark task completed.

The old cleanup block hit a native stderr warning during log collection and skipped automatic stop. The study container was explicitly stopped at 19:26:19Z; subsequent Docker inspection reported Running=false, OOMKilled=false and exit code 0. An after-stop inspection is preserved separately. This is a study-harness error, not agent repetition or application outage. No attempt is made to impute a successful application readiness result.

The runner now uses `/status`, unique container names, and nested finally blocks so log errors cannot skip the stop attempt or outcome record. A mocked low-memory/log-exception test confirms that stop is attempted and outcome JSON is preserved despite the injected exception. The first mock test's observer used incorrect script scope and falsely reported the stop flag; that artifact is retained. The observer was corrected and the rerun passed. These tests launch no real containers and must remain outside application-performance datasets. The revised runner has not been validated in a new real application run.

## Where the study stands

| Stage | Status |
|---|---|
| Hardware/model/source pins | Recorded |
| Dataset inventory/template split | Validated: 812 tasks, 190 templates |
| Supported Python/evaluator/browser environment | Installed; dependency hashes recorded |
| Offline provided-fixture checks | 3/3 matched; no live model |
| Application startup with resource monitoring | Attempted; RAM threshold crossed; stopped |
| Correct application readiness and state/effect oracles | Outstanding |
| Minimal versus framework live benchmark runs | Not started |
| Main study, service-harm/recovery results | Not started |
| Natural observations | No genuine tasks available |
| Literature novelty | Unproven; close prior work identified |

Next gates: stable additional memory headroom, application readiness through the correct endpoint, independent commit/effect oracles and validated reset, then matched minimal/framework development runs before holdout collection. Do not weaken the RAM threshold, label setup errors as benchmark failures, or substitute supplied traces for live agent results.
