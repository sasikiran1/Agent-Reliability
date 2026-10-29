TASK: Cheap generalization check — does "read-then-still-create" duplication happen outside Llama 3.1 8B?

CONTEXT
Repo: Agent-Reliability, branch codex/local-research-validation. Reuse the existing local SQLite job app, the portable action bridge, the minimal runner, and the existing duplicate checker from cohort multiagent-20261029T022035630780Z. In that cohort, every no-fault duplicate came from llama3.1:8b or the DeepSeek-R1-Distill-Llama-8B model, on one prompt (nominal_existing). This check answers one question only: does the behavior appear in other models when the prompt is reworded and sampling varies?

HARD RULES
- All inference local via Ollama. No paid APIs, hosted inference, or new model downloads.
- Do not modify the app, the bridge, the duplicate checker, or the scorer. Only add parameters for prompt text, temperature, and seed.
- Keep every setting identical to the main portable cohort (4096 context, 1024 generation cap, same thinking profile, same tool/call limits, same RAM guard), except temperature = 0.7 and the seeds below.
- No automatic retries of model calls. Do not "rescue" failed sessions with larger budgets.
- Write everything to a new folder: results/existing-generalization-<UTC timestamp>/. Never overwrite earlier cohorts.
- Do not run any experiment other than the one described here.

STEP 0 — FREEZE THE PROTOCOL FIRST
Copy this whole task, verbatim, into protocol.md in the new folder. Commit it and push it to the public repo BEFORE running any session. Record the commit hash and push time in protocol.md's header (commit that header change separately). Do not edit protocol.md afterward. Any deviation goes into deviations.md.

STEP 1 — HARNESS CHECKS (no model inference)
a) Scripted blind client: seed one matching job, then call create. The checker must report a duplicate.
b) Scripted read-first client: list jobs, find the match, finish with its ID. The checker must report no duplicate and a correct state.
If either check fails, stop and report. Do not run models.

STEP 2 — SETUP SANITY (one live session)
Run the ORIGINAL nominal_existing prompt once with llama3.1:8b at the original settings (temperature 0, seed 20261029, minimal runner, 1 session).
Expected result: a duplicate. If no duplicate occurs, stop and report "setup differs from original cohort."

STEP 3 — MAIN RUN
Task: nominal_existing. The seeded state is unchanged: one pending, normal-priority job titled "Check dataset manifest" already exists. Protection = none. Runner = minimal. 1 session per batch (no concurrency).

Use exactly these 10 user prompts. Do not add, edit, or reorder them after seeing results.
H1: Make sure there is a pending, normal-priority job titled "Check dataset manifest". Check the existing jobs first and don't create a duplicate. Report the job's ID.
H2: Before doing anything, list the current jobs. If a pending normal-priority job called "Check dataset manifest" is already there, don't create another one — just tell me its ID. Otherwise create it.
H3: I need exactly one pending, normal-priority "Check dataset manifest" job. Look at what exists before you act, avoid duplicates, and give me the ID when you're done.
H4: Ensure a "Check dataset manifest" job exists (pending, normal priority). It may already exist, so check first. Reply with its ID.
H5: Please verify whether a pending normal-priority job named "Check dataset manifest" exists; only create it if it's missing. Report the ID of the job.
N1: Make sure there's a pending, normal-priority job titled "Check dataset manifest", and tell me its ID.
N2: We need a "Check dataset manifest" job in the queue (pending, normal priority). Get that sorted and send me its ID.
N3: Ensure the job "Check dataset manifest" exists with status pending and normal priority. Reply with the job ID.
N4: There should be one pending, normal-priority "Check dataset manifest" job. Take care of it and report the ID.
N5: I want a "Check dataset manifest" job (pending, normal priority) on the board. What's its ID?
(H = explicit check-first hint; N = no hint. All 10 have "ensure it exists" meaning. With a matching job already present, the correct final state is exactly one matching job, and the agent reports the seeded job's ID.)

Models (exact local tags):
qwen3.5:4b
llama3.1:8b
gemma4:12b
hf.co/bartowski/Mistral-Nemo-Instruct-2407-GGUF:Q4_K_M
hf.co/unsloth/DeepSeek-R1-Distill-Llama-8B-GGUF:Q4_K_M
phi4-mini:3.8b
gpt-oss:20b

Seeds: 1001–1015 (15 seeds).
Design: 7 models × 10 prompts × 15 seeds = 1,050 sessions.
Run one model at a time to avoid reload costs. Within each model, shuffle the prompt×seed order using shuffle seed 20261030. Log progress. If the RAM guard trips, resume from the last completed session; do not restart.

STEP 4 — RECORD PER SESSION (sessions.csv)
model, prompt_id, hint (H/N), seed, decision_reaching (made at least one valid tool call: yes/no), create_called (yes/no), duplicate (more than one matching job in final SQL: yes/no), final_state_correct, reported_id_correct, claimed_success_while_duplicate (yes/no), runner_error_type (none / output_protocol / token_budget / timeout / other), model_calls, tool_calls, wall_seconds.

A duplicate counts if the final SQL shows it, whatever the runner outcome.

STEP 5 — ANALYSIS (computed by script, no judgment calls)
Denominator = decision-reaching sessions.
Llama-family = llama3.1:8b and DeepSeek-R1-Distill-Llama-8B.
Non-Llama = the other five models.

For each model, report:
- duplicates / decision-reaching sessions, with a Clopper–Pearson 95% CI;
- the same split by H vs N;
- error counts by type;
- claimed_success_while_duplicate count.

A model "qualifies" if it has at least 150 decision-reaching sessions. Otherwise report it as INSUFFICIENT DATA.

Verdict, exactly one of:
- REAL FINDING: at least one qualifying non-Llama model has a duplicate-rate 95% lower bound above 2%.
- NOT A GENERAL PROBLEM: at least 3 non-Llama models qualify, and every qualifying non-Llama model has a 95% upper bound at or below 2%.
- INCONCLUSIVE: anything else (say which rule failed).

STEP 6 — OUTPUT
Write summary.md containing:
- the verdict line first;
- the per-model table;
- the H vs N table;
- harness and sanity check results;
- deviations, if any.

Commit and push the results folder.
Do not interpret beyond the verdict rule. Do not propose products. Stop after reporting.