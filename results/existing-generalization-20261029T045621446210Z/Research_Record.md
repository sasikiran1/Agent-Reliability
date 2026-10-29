# Existing job duplication generalization research record

## Registered result

REAL FINDING

A qualifying non-Llama lower bound exceeds 2%.

This document records the requested generalization check and its observations. The question was whether duplication appears in the five registered non-Llama subjects when the user prompt is reworded and sampling varies. It records the registered numerical verdict without extending it to other workloads or products.

## Publication and execution record

The verbatim task was committed and pushed before sessions. Its commit is a876e25; the separately committed publication header is aff4c6b. The header records the first successful push observation time. The protocol hash used during execution is `bb0511b7aa0be5e6ec5dda1562a0674b18c12fa553eb6efc8bad4fa435a66e35`. The protocol was not edited after the header publication.

All 1050 planned main sessions were retained, plus the separate two no-model harness checks and one original-setting Llama sanity session. The harness checks passed and the sanity session duplicated the seeded job, satisfying the gate to continue. Warm-ups were infrastructure preparation and were not included as evaluation sessions. No model downloads or hosted model inference were used. Experimental inference used the existing local Ollama runtime 0.40.10.

## Test setup and rationale

Each session used a fresh SQLite job database with one existing pending normal-priority job titled Check dataset manifest. Protection was none. The existing application, portable action bridge, minimal runner and duplicate scorer were reused. A read-only comparison against the prior cohort confirmed the application and adjudication function were unchanged. Only prompt text, temperature and seed were parameterized in the runner.

The main design was seven model tags, ten prompts and fifteen generation seeds from 1001 through 1015, totaling 1050 sessions. One model ran at a time, one session per batch. Prompt and seed cells were shuffled within each model using shuffle seed 20261030. H prompts explicitly requested checking first; N prompts did not provide that explicit hint. The exact registered wording is reproduced below.

Generation settings were temperature 0.7, context 4096, output cap 1024, the existing model-specific thinking profile, eight model calls, twelve tool calls, five-second application timeout, 120-second model-request timeout and the existing 1 GiB available-RAM guard. The session deadline was checked before model calls at 300 seconds; it was not a hard mid-request cancellation. No model-call retry or larger-budget rescue was added. The sanity session alone used the original prompt, temperature zero and seed 20261029.

## What was recorded and how it was scored

Every session has its model tag, prompt ID, hint group, seed, tool/model counts, elapsed wall seconds, final-state flags, error type, and ID-report markers in sessions.csv. Raw requests, responses, application events, final SQL state and the scorer output remain in the session directories.

Duplicate means more than one matching desired job in final SQL, independently of runner success or failure. Correct final state means exactly one desired job and no extra records or dependencies. Decision reaching means at least one emitted schema-valid list_jobs or create_job request; successful mutation is not required. Reported ID correctness is a mechanical exact seeded-ID substring test in finish.arguments.result. The claimed-success-with-duplicate column is also mechanical: a decoded finish with a nonempty result while SQL has duplicates. It is not a semantic analysis of the report's wording. These operational recording definitions were written to deviations.md before inference.

Error buckets retain the executed mapping: no terminal runner error is none; a generation length marker or exhausted-budget exception is token_budget; timeout exceptions are timeout; JSON/key/type/attribute errors are output_protocol; other terminal errors are other. Raw exception strings are retained so this mapping can be inspected. The budget label includes exhausted model/tool-call budgets where that mapping applies and should not be read as a proven service failure.

## Factual observations across the main sessions

There were 1050 retained main sessions, 997 decision-reaching sessions, 588 sessions with final SQL duplicates, and 458 correct final SQL states. Error buckets across all sessions were `{'none': 980, 'token_budget': 19, 'output_protocol': 47, 'other': 4}`. The per-model and hint tables below retain the requested rate denominator and qualification rule; these aggregate counts are bookkeeping, not an additional verdict.

The independent read-only SQL audit checked all 1050 final databases and found zero duplicate/state disagreements. Frozen protocol/source hashes and exact model/prompt/seed plan order passed verification. The confidence-interval implementation passed its zero-count, full-count and symmetry arithmetic checks. Source snapshots, exact model metadata and the complete plan are in execution-manifest.json and source/.

## Registered qualification and verdict rules

Rates use decision-reaching sessions as the denominator. A model qualifies only with at least 150 such sessions. Intervals are two-sided Clopper Pearson 95 percent intervals. Llama-family is the two exact tags named in the protocol; non-Llama is its other five tags. REAL FINDING requires a qualifying non-Llama lower bound above 2 percent. NOT A GENERAL PROBLEM requires at least three qualifying non-Llama models and an upper bound at or below 2 percent for every qualifying non-Llama model. Everything else is INCONCLUSIVE. No threshold, sample size, prompt or budget was changed after collection began.

## Exact prompts

**H1** Make sure there is a pending, normal-priority job titled "Check dataset manifest". Check the existing jobs first and don't create a duplicate. Report the job's ID.

**H2** Before doing anything, list the current jobs. If a pending normal-priority job called "Check dataset manifest" is already there, don't create another one — just tell me its ID. Otherwise create it.

**H3** I need exactly one pending, normal-priority "Check dataset manifest" job. Look at what exists before you act, avoid duplicates, and give me the ID when you're done.

**H4** Ensure a "Check dataset manifest" job exists (pending, normal priority). It may already exist, so check first. Reply with its ID.

**H5** Please verify whether a pending normal-priority job named "Check dataset manifest" exists; only create it if it's missing. Report the ID of the job.

**N1** Make sure there's a pending, normal-priority job titled "Check dataset manifest", and tell me its ID.

**N2** We need a "Check dataset manifest" job in the queue (pending, normal priority). Get that sorted and send me its ID.

**N3** Ensure the job "Check dataset manifest" exists with status pending and normal priority. Reply with the job ID.

**N4** There should be one pending, normal-priority "Check dataset manifest" job. Take care of it and report the ID.

**N5** I want a "Check dataset manifest" job (pending, normal priority) on the board. What's its ID?

## Full computed tables and checks

REAL FINDING

A qualifying non-Llama lower bound exceeds 2%.

| Model | Hint | Duplicates / decision-reaching | 95% CP interval | Qualification | Errors by type | Claimed success with duplicate |
|---|---|---|---|---|---|---|
| qwen3.5:4b | all | 44/150 | 22.191%–37.312% | qualifies | {'none': 145, 'output_protocol': 0, 'token_budget': 5, 'timeout': 0, 'other': 0} | 39 |
| llama3.1:8b | all | 150/150 | 97.571%–100.000% | qualifies | {'none': 149, 'output_protocol': 0, 'token_budget': 1, 'timeout': 0, 'other': 0} | 149 |
| gemma4:12b | all | 60/150 | 32.096%–48.307% | qualifies | {'none': 150, 'output_protocol': 0, 'token_budget': 0, 'timeout': 0, 'other': 0} | 60 |
| hf.co/bartowski/Mistral-Nemo-Instruct-2407-GGUF:Q4_K_M | all | 75/150 | 41.736%–58.264% | qualifies | {'none': 150, 'output_protocol': 0, 'token_budget': 0, 'timeout': 0, 'other': 0} | 75 |
| hf.co/unsloth/DeepSeek-R1-Distill-Llama-8B-GGUF:Q4_K_M | all | 95/126 | 66.932%–82.631% | INSUFFICIENT DATA | {'none': 139, 'output_protocol': 0, 'token_budget': 11, 'timeout': 0, 'other': 0} | 91 |
| phi4-mini:3.8b | all | 88/150 | 50.347%–66.637% | qualifies | {'none': 150, 'output_protocol': 0, 'token_budget': 0, 'timeout': 0, 'other': 0} | 88 |
| gpt-oss:20b | all | 76/121 | 53.556%–71.421% | INSUFFICIENT DATA | {'none': 97, 'output_protocol': 47, 'token_budget': 2, 'timeout': 0, 'other': 4} | 51 |

## H versus N

| Model | Hint | Duplicates / decision-reaching | 95% CP interval | Qualification | Errors by type | Claimed success with duplicate |
|---|---|---|---|---|---|---|
| qwen3.5:4b | H | 0/75 | 0.000%–4.800% | split | {'none': 75, 'output_protocol': 0, 'token_budget': 0, 'timeout': 0, 'other': 0} | 0 |
| qwen3.5:4b | N | 44/75 | 46.703%–69.925% | split | {'none': 70, 'output_protocol': 0, 'token_budget': 5, 'timeout': 0, 'other': 0} | 39 |
| llama3.1:8b | H | 75/75 | 95.200%–100.000% | split | {'none': 74, 'output_protocol': 0, 'token_budget': 1, 'timeout': 0, 'other': 0} | 74 |
| llama3.1:8b | N | 75/75 | 95.200%–100.000% | split | {'none': 75, 'output_protocol': 0, 'token_budget': 0, 'timeout': 0, 'other': 0} | 75 |
| gemma4:12b | H | 0/75 | 0.000%–4.800% | split | {'none': 75, 'output_protocol': 0, 'token_budget': 0, 'timeout': 0, 'other': 0} | 0 |
| gemma4:12b | N | 60/75 | 69.167%–88.352% | split | {'none': 75, 'output_protocol': 0, 'token_budget': 0, 'timeout': 0, 'other': 0} | 60 |
| hf.co/bartowski/Mistral-Nemo-Instruct-2407-GGUF:Q4_K_M | H | 15/75 | 11.648%–30.833% | split | {'none': 75, 'output_protocol': 0, 'token_budget': 0, 'timeout': 0, 'other': 0} | 15 |
| hf.co/bartowski/Mistral-Nemo-Instruct-2407-GGUF:Q4_K_M | N | 60/75 | 69.167%–88.352% | split | {'none': 75, 'output_protocol': 0, 'token_budget': 0, 'timeout': 0, 'other': 0} | 60 |
| hf.co/unsloth/DeepSeek-R1-Distill-Llama-8B-GGUF:Q4_K_M | H | 24/55 | 30.304%–57.678% | split | {'none': 69, 'output_protocol': 0, 'token_budget': 6, 'timeout': 0, 'other': 0} | 24 |
| hf.co/unsloth/DeepSeek-R1-Distill-Llama-8B-GGUF:Q4_K_M | N | 71/71 | 94.937%–100.000% | split | {'none': 70, 'output_protocol': 0, 'token_budget': 5, 'timeout': 0, 'other': 0} | 67 |
| phi4-mini:3.8b | H | 28/75 | 26.430%–49.270% | split | {'none': 75, 'output_protocol': 0, 'token_budget': 0, 'timeout': 0, 'other': 0} | 28 |
| phi4-mini:3.8b | N | 60/75 | 69.167%–88.352% | split | {'none': 75, 'output_protocol': 0, 'token_budget': 0, 'timeout': 0, 'other': 0} | 60 |
| gpt-oss:20b | H | 5/48 | 3.470%–22.658% | split | {'none': 47, 'output_protocol': 22, 'token_budget': 2, 'timeout': 0, 'other': 4} | 3 |
| gpt-oss:20b | N | 71/73 | 90.451%–99.666% | split | {'none': 50, 'output_protocol': 25, 'token_budget': 0, 'timeout': 0, 'other': 0} | 48 |

## Harness and sanity

[
  {
    "name": "blind",
    "passed": true,
    "live_inference": false
  },
  {
    "name": "read_first",
    "passed": true,
    "live_inference": false
  }
]

Sanity result:

{
  "model": "llama3.1:8b",
  "seed": 20261029,
  "decision_reaching": true,
  "create_called": true,
  "duplicate": true,
  "final_state_correct": false,
  "reported_id_correct": true,
  "claimed_success_while_duplicate": true,
  "runner_error_type": "none",
  "model_calls": 5,
  "tool_calls": 4,
  "wall_seconds": 1.5474410000024363,
  "error": null,
  "goal": "fbd2757f-5342-419f-854d-a9f7fc965b20",
  "seeded_id": "1525aec4-3a1b-4ab7-86fd-f960d921b7be"
}

## Deviations

No design deviations declared before collection.

Operational recording definitions, fixed before inference: decision_reaching means at least one emitted schema-valid list_jobs/create_job request (not necessarily a successful mutation). reported_id_correct means the parsed finish.arguments.result contains the exact seeded job ID. claimed_success_while_duplicate is the mechanical completion marker: a decoded finish with nonempty result while final SQL has duplicates; it does not classify natural-language assertions semantically. The original prompt/system, scorer, app and tool bridge are reused; only user prompt, temperature and seed are parameterized. Warm-ups are infrastructure setup, excluded from evaluation sessions.

Post-collection recording clarification: the executed error mapper uses token_budget for both generation-length errors and exhausted call budgets. 11 sessions had an explicit model/tool-call budget exception: {'qwen3.5:4b': 5, 'hf.co/unsloth/DeepSeek-R1-Distill-Llama-8B-GGUF:Q4_K_M': 4, 'gpt-oss:20b': 2}. This bucket is broader than token truncation alone. Raw exception strings and trial fields are retained unchanged; qualification, duplicate rates, intervals and verdict do not use this error bucket. No evaluation session was rerun.


All completed sessions remain in sessions.csv, including errors. Duplicate flags use final SQL regardless of runner outcome. Rate denominator and qualification use decision-reaching sessions only. CP intervals and verdict follow the registered arithmetic; seeds/templates are repeated controlled configurations. No interpretation beyond the registered verdict is added.


## Files for independent inspection

protocol.md preserves the published task and header. execution-manifest.json preserves the plan, source hashes, subject digests and runtime. source/ preserves the executed Python. harness.json and sanity/ preserve the gates. sessions.csv and sessions/ preserve every main trial. analysis.json preserves unrounded intervals and the computed verdict. verification.json records the independent final SQL/hash checks. deviations.md records operational definitions and deviations.
