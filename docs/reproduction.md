# Reproduction and limitations

The original model smoke check below is historical setup evidence, not the current benchmark protocol. For benchmark feasibility and subsequent gates see benchmark-feasibility.md. The user has no genuine repository task; none is pending.

Inventory and source pins can be regenerated using `src/benchmark_inventory.py` under the installed Ubuntu Python. Run `python3 -m unittest discover -s src -p test_benchmark_inventory.py` from the project root to validate dataset coverage and template isolation. No benchmark dependency installation or inference is involved. Candidate pilot task selection is not a capability score.

Run `src/environment_feasibility.ps1` in PowerShell for the bounded private application check. First install the exact image digest recorded in the feasibility assessment. It refuses to start below 2 GiB free host RAM; if launched, it uses loopback-only ports, a 1536 MiB container cap and stops afterward. A stopped container is retained for audit. Resource caps are setup interventions, not demonstrated production settings. The original preflight result is preserved in data/feasibility/environment; later attempts use unique timestamp directories. No model runs in this check. Do not launch it during downloads or model inference.

`src/artifact_manifest.py` regenerates results/checksums.csv under WSL Python, including vendored source but excluding Git internals, caches and the manifest itself. Source commit pins and local dataset checksum are recorded separately. The data inventory can be reproduced by cloning each named source repository and checking out its recorded commit before running the script; mutable main branches may contain different tasks or evaluators.

Use Windows PowerShell 5.1 and installed Ollama 0.40.10. The runner has no package dependencies. Model digests are in status.md and raw API metadata. Pulling mutable tags later can obtain different artifacts: compare full digests before replication. Do not reuse results across changed versions without recording the change.

Start from project root. Ensure no other model is loaded and no download is running; confirm at least 1 GiB free physical RAM (more headroom is desirable). The first run operated near the RAM limit; free memory through your normal app management before another attempt. Do not run two or four sessions yet.

Run `powershell -NoProfile -File src/pilot.ps1 -Model qwen3.5:4b`. If local execution policy disallows scripts, obtain permission before using a process-only `-ExecutionPolicy Bypass`; do not change persistent policy. The saved first attempt was cancelled and is not a validated end-to-end reproduction. Subsequent attempts create unique timestamp directories. Keep raw files unchanged.

`src/checksums.ps1` hashes workspace files except its output CSV and .git internals. Regenerate after additions; compare hashes before analysis. Windows download logs contain terminal control sequences and are kept raw.

Raw trace includes the study protocol, not private user documents. Before genuine repository work, specify allowed tools/paths and redact secrets from arguments and outputs. Current allowlisted runner cannot repair repositories; a constrained repository adapter and independent failing/passing tests are still required.
