"""Offline verification and factual document for the registered completed study."""
import collections,hashlib,json,re,sqlite3,sys
from pathlib import Path

root=Path(__file__).resolve().parents[1]
out=Path(sys.argv[1]).resolve()
manifest=json.loads((out/'execution-manifest.json').read_text())
analysis=json.loads((out/'analysis.json').read_text())
rows=[json.loads(p.read_text()) for p in sorted((out/'sessions').glob('*/result.json'))]
assert len(rows)==len(manifest['plan'])==1050
assert hashlib.sha256((out/'protocol.md').read_bytes()).hexdigest()==manifest['protocol_sha256']
for rel,digest in manifest['sources'].items():
    assert hashlib.sha256((out/'source'/Path(rel).name).read_bytes()).hexdigest()==digest
    assert hashlib.sha256((root/rel).read_bytes()).hexdigest()==digest
errors=[]
for row,cell in zip(rows,manifest['plan']):
    assert all(row[k]==cell[k] for k in ['model','prompt_id','hint','seed'])
    p=out/'sessions'/f"{row['session']:04d}"/'application.sqlite'
    with sqlite3.connect(f'file:{p.as_posix()}?mode=ro',uri=True) as db:
        jobs=db.execute('SELECT title,priority,state FROM jobs WHERE goal_id=?',(row['goal'],)).fetchall()
        deps=db.execute('SELECT COUNT(*) FROM dependencies').fetchone()[0]
    matches=sum(tuple(j)==('Check dataset manifest','normal','pending') for j in jobs)
    duplicate=matches>1
    correct=len(jobs)==1 and matches==1 and deps==0
    if row['duplicate']!=duplicate or row['final_state_correct']!=correct:
        errors.append(row['session'])
assert not errors,errors
audit=dict(completed=len(rows),independently_audited_sql_sessions=len(rows),sql_disagreements=errors,
    frozen_protocol_and_source_hashes='passed',plan_order_and_pairs='passed',
    verification='Read-only SQL re-expression and source checks; no model inference or new experiments')
(out/'verification.json').write_text(json.dumps(audit,indent=2))
summary=(out/'summary.md').read_text(encoding='utf-8')
prompts=re.findall(r'^([HN][1-5]): (.*)$',(out/'protocol.md').read_text(encoding='utf-8-sig'),re.M)
total_errors=collections.Counter(r['runner_error_type'] for r in rows)
total_dups=sum(r['duplicate'] for r in rows)
text=f'''# Existing job duplication generalization research record

## Registered result

{analysis['verdict']}

{analysis['reason']}

This document records the requested generalization check and its observations. The question was whether duplication appears in the five registered non-Llama subjects when the user prompt is reworded and sampling varies. It records the registered numerical verdict without extending it to other workloads or products.

## Publication and execution record

The verbatim task was committed and pushed before sessions. Its commit is a876e25; the separately committed publication header is aff4c6b. The header records the first successful push observation time. The protocol hash used during execution is `{manifest['protocol_sha256']}`. The protocol was not edited after the header publication.

All 1050 planned main sessions were retained, plus the separate two no-model harness checks and one original-setting Llama sanity session. The harness checks passed and the sanity session duplicated the seeded job, satisfying the gate to continue. Warm-ups were infrastructure preparation and were not included as evaluation sessions. No model downloads or hosted model inference were used. Experimental inference used the existing local Ollama runtime {manifest['runtime']['version']}.

## Test setup and rationale

Each session used a fresh SQLite job database with one existing pending normal-priority job titled Check dataset manifest. Protection was none. The existing application, portable action bridge, minimal runner and duplicate scorer were reused. A read-only comparison against the prior cohort confirmed the application and adjudication function were unchanged. Only prompt text, temperature and seed were parameterized in the runner.

The main design was seven model tags, ten prompts and fifteen generation seeds from 1001 through 1015, totaling 1050 sessions. One model ran at a time, one session per batch. Prompt and seed cells were shuffled within each model using shuffle seed 20261030. H prompts explicitly requested checking first; N prompts did not provide that explicit hint. The exact registered wording is reproduced below.

Generation settings were temperature 0.7, context 4096, output cap 1024, the existing model-specific thinking profile, eight model calls, twelve tool calls, five-second application timeout, 120-second model-request timeout and the existing 1 GiB available-RAM guard. The session deadline was checked before model calls at 300 seconds; it was not a hard mid-request cancellation. No model-call retry or larger-budget rescue was added. The sanity session alone used the original prompt, temperature zero and seed 20261029.

## What was recorded and how it was scored

Every session has its model tag, prompt ID, hint group, seed, tool/model counts, elapsed wall seconds, final-state flags, error type, and ID-report markers in sessions.csv. Raw requests, responses, application events, final SQL state and the scorer output remain in the session directories.

Duplicate means more than one matching desired job in final SQL, independently of runner success or failure. Correct final state means exactly one desired job and no extra records or dependencies. Decision reaching means at least one emitted schema-valid list_jobs or create_job request; successful mutation is not required. Reported ID correctness is a mechanical exact seeded-ID substring test in finish.arguments.result. The claimed-success-with-duplicate column is also mechanical: a decoded finish with a nonempty result while SQL has duplicates. It is not a semantic analysis of the report's wording. These operational recording definitions were written to deviations.md before inference.

Error buckets retain the executed mapping: no terminal runner error is none; a generation length marker or exhausted-budget exception is token_budget; timeout exceptions are timeout; JSON/key/type/attribute errors are output_protocol; other terminal errors are other. Raw exception strings are retained so this mapping can be inspected. The budget label includes exhausted model/tool-call budgets where that mapping applies and should not be read as a proven service failure.

## Factual observations across the main sessions

There were {len(rows)} retained main sessions, {sum(r['decision_reaching'] for r in rows)} decision-reaching sessions, {total_dups} sessions with final SQL duplicates, and {sum(r['final_state_correct'] for r in rows)} correct final SQL states. Error buckets across all sessions were `{dict(total_errors)}`. The per-model and hint tables below retain the requested rate denominator and qualification rule; these aggregate counts are bookkeeping, not an additional verdict.

The independent read-only SQL audit checked all 1050 final databases and found zero duplicate/state disagreements. Frozen protocol/source hashes and exact model/prompt/seed plan order passed verification. The confidence-interval implementation passed its zero-count, full-count and symmetry arithmetic checks. Source snapshots, exact model metadata and the complete plan are in execution-manifest.json and source/.

## Registered qualification and verdict rules

Rates use decision-reaching sessions as the denominator. A model qualifies only with at least 150 such sessions. Intervals are two-sided Clopper Pearson 95 percent intervals. Llama-family is the two exact tags named in the protocol; non-Llama is its other five tags. REAL FINDING requires a qualifying non-Llama lower bound above 2 percent. NOT A GENERAL PROBLEM requires at least three qualifying non-Llama models and an upper bound at or below 2 percent for every qualifying non-Llama model. Everything else is INCONCLUSIVE. No threshold, sample size, prompt or budget was changed after collection began.

## Exact prompts

'''
text+='\n\n'.join(f'**{i}** {p}' for i,p in prompts)
text+='\n\n## Full computed tables and checks\n\n'+summary
text+='\n\n## Files for independent inspection\n\nprotocol.md preserves the published task and header. execution-manifest.json preserves the plan, source hashes, subject digests and runtime. source/ preserves the executed Python. harness.json and sanity/ preserve the gates. sessions.csv and sessions/ preserve every main trial. analysis.json preserves unrounded intervals and the computed verdict. verification.json records the independent final SQL/hash checks. deviations.md records operational definitions and deviations.\n'
(out/'Research_Record.md').write_text(text,encoding='utf-8')
print(json.dumps(dict(document=str(out/'Research_Record.md'),sessions=len(rows),verification='passed',verdict=analysis['verdict'])))
