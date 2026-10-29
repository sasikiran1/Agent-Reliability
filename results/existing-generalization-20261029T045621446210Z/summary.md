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
