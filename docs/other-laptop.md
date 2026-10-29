# Run the first experiment on another laptop

This path needs Python 3.12, Git and local Ollama. It does not need Docker, WSL, a browser, WebArena, AgentLab or LangGraph. Use local inference only; do not configure cloud models or paid endpoints. Existing results belong to the original laptop; each new run writes a new timestamped directory and records its own runtime/model metadata.

## Obtain and install

Clone `https://github.com/sasikiran1/Agent-Reliability.git`, check out `main`, and open a terminal in its root. The repository is private, so use your GitHub account on the other laptop. Keep the original results unchanged.

Windows PowerShell, with Python 3.12 installed:

```powershell
py -3.12 -m venv .venv
.venv/Scripts/python.exe -m pip install --require-hashes -r requirements-local.lock
.venv/Scripts/python.exe src/validate_local_lab.py
.venv/Scripts/python.exe src/validate_workflow_lab.py
```

Linux/macOS equivalent:

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install --require-hashes -r requirements-local.lock
.venv/bin/python src/validate_local_lab.py
.venv/bin/python src/validate_workflow_lab.py
```

The two validations use constructed operations/faults with no model, bind only to loopback, and write disposable SQLite data plus trace files under results/. Failure should stop progression to live runs. GPU telemetry uses nvidia-smi when available; on other hardware its absence is recorded as a telemetry limitation and does not imply a model/service failure.

## Prepare local models

Start the installed Ollama service on `127.0.0.1:11434`. Download the two explicitly local model tags:

```text
ollama pull qwen3.5:4b
ollama pull llama3.1:8b
```

Downloads are network transfers; inference must remain local. Record the Ollama version. The original experiment used 0.40.10 and full digests:

- Qwen: d8b0f5e9760cd1682034f292d7ef72ec46f432149be0df7574bf2d6e92e38c04
- Llama: 46e0c10c039e019119339687c3c1757cc81b9da49709a3b3924863ba87ca666e

Tags can change. Inspect `http://127.0.0.1:11434/api/tags` or the run manifest and compare full digests. A different artifact/runtime is a new experimental configuration, not an exact reproduction. Finish downloads before running. The runner refuses to start with another model already loaded; finish that session normally first. Keep the 1 GiB memory stopping rule.

## Run the predefined cohort

On Windows, run sequentially:

```powershell
.venv/Scripts/python.exe src/run_local_pilot.py --model qwen3.5:4b --task-id manifest-review
.venv/Scripts/python.exe src/run_local_pilot.py --model qwen3.5:4b --task-id document-review
.venv/Scripts/python.exe src/run_local_pilot.py --model llama3.1:8b --task-id manifest-review
.venv/Scripts/python.exe src/run_local_pilot.py --model llama3.1:8b --task-id document-review
.venv/Scripts/python.exe src/audit_pilot_evidence.py
```

On Linux/macOS replace `.venv/Scripts/python.exe` with `.venv/bin/python`. The runner warms each model alongside the application, records warm-up separately, attempts the task, audits persistent state and unloads its model. Review result.json, oracle.json and evidence-audit.json in each new results/live-local-* directory. Check errors/cancellations even if the command process itself exits successfully. `results/pilot-results.csv` is a regenerated summary of all present live runs, so keep machine cohorts distinct using each run's manifest and directory.

The model's completion text is not a correctness test. Preserve incorrect results and failures. The original multi-step cohort had Qwen 2/2 correct and Llama 0/2 correct, with no duplicate committed child effects. Those outcomes need not repeat on a different configuration. This remains a tiny controlled development pilot, not a production failure-rate estimate.

## Optional benchmark source restoration

The minimal experiment does not import vendored benchmark code. The larger evaluator lockfiles and historical inventory checks require source checkouts excluded from Git. Restore the exact repository/commit pairs in data/feasibility/source-manifest.json under vendor/<name>. Do not use mutable main branches as substitutes. Existing checksums include those source files and will only all resolve after restoration; models, virtual environments and tools are intentionally excluded. Install requirements-pilot.lock or requirements-framework.lock only if you later choose to reproduce those separate setup tracks.
