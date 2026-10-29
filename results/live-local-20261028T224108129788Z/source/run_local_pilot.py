"""Low-memory supervisor: local application, isolated worker, telemetry, SQL oracle."""
import argparse
import csv
import hashlib
import json
import subprocess
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

import psutil
from local_lab import JobStore, Trace, audit, serve

ROOT = Path(__file__).resolve().parents[1]


def api(endpoint, body=None, timeout=5):
    req = Request('http://127.0.0.1:11434/api/' + endpoint,
                  None if body is None else json.dumps(body).encode(), {'Content-Type': 'application/json'})
    with urlopen(req, timeout=timeout) as response:
        return json.load(response)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--model', choices=['qwen3.5:4b', 'llama3.1:8b'], required=True)
    parser.add_argument('--runner', choices=['minimal', 'langgraph'], default='minimal')
    args = parser.parse_args()
    run = ROOT / 'results' / ('live-local-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
    run.mkdir()
    goal = str(uuid.uuid4())
    store = JobStore(run / 'application.sqlite')
    trace, resources = Trace(run / 'application.jsonl'), Trace(run / 'resources.jsonl')
    status, error, worker, owned = 'setup_error', None, None, False
    start = time.perf_counter()
    manifest = dict(model=args.model, runner=args.runner, task_id=goal, track='controlled_development', live_model=True,
                    protocol_sha256=hashlib.sha256((ROOT / 'docs/lightweight-pilot-protocol.md').read_bytes()).hexdigest(),
                    source_sha256={p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in
                                   [Path(__file__), ROOT/'src/pilot_worker.py', ROOT/'src/local_lab.py']},
                    interventions=['researcher_created_task_and_application', 'thinking_disabled_for_qwen'],
                    retry_settings=dict(transport_retries=0, framework_node_retry=None, max_model_calls=4, max_tool_calls=8),
                    context_tokens=4096, output_cap=512, natural_recovery='not observed')
    try:
        if psutil.virtual_memory().available < 1024**3:
            raise RuntimeError('Preflight RAM below 1 GiB')
        loaded = api('ps')
        if loaded['models']:
            raise RuntimeError('An existing model is loaded; leave it untouched')
        manifest['runtime'] = api('version')
        manifest['model_metadata'] = next(m for m in api('tags')['models'] if m['name'] == args.model)
        (run/'manifest.json').write_text(json.dumps(manifest, indent=2))
        with serve(store, trace) as url, (run/'worker.log').open('w') as log:
            worker = subprocess.Popen([sys.executable, str(ROOT/'src/pilot_worker.py'), '--model', args.model,
                '--runner', args.runner, '--service', url, '--goal', goal, '--output', str(run)], stdout=log, stderr=log)
            owned = True
            status = 'running'
            tick = 0
            while worker.poll() is None:
                memory = psutil.virtual_memory()
                sample = dict(free_ram_bytes=memory.available, cpu_percent=psutil.cpu_percent(),
                              supervisor_rss=psutil.Process().memory_info().rss)
                try:
                    sample['worker_rss'] = psutil.Process(worker.pid).memory_info().rss
                except psutil.NoSuchProcess:
                    pass
                if tick % 3 == 0:
                    try:
                        sample['gpu'] = subprocess.check_output(['nvidia-smi', '--query-gpu=memory.used,utilization.gpu',
                            '--format=csv,noheader,nounits'], timeout=2, text=True).strip()
                        sample['loaded'] = api('ps', timeout=2)
                    except Exception as exc:
                        sample['telemetry_error'] = repr(exc)
                resources.emit('resource_sample', **sample)
                if memory.available < 1024**3:
                    status = 'cancelled_ram_threshold'
                    worker.terminate(); worker.wait(timeout=10); break
                if time.perf_counter() - start > 300:
                    status = 'cancelled_task_deadline'
                    worker.terminate(); worker.wait(timeout=10); break
                time.sleep(1)
                tick += 1
            if status == 'running':
                status = 'worker_exited'
    except Exception as exc:
        error = repr(exc)
    finally:
        if worker and worker.poll() is None:
            worker.terminate(); worker.wait(timeout=10)
        if owned:
            try:
                manifest['loaded_before_unload'] = api('ps')
                manifest['unload_response'] = api('generate', dict(model=args.model, keep_alive=0), timeout=20)
                manifest['loaded_after_unload'] = api('ps')
            except Exception as exc:
                manifest['unload_error'] = repr(exc)
        (run/'manifest.json').write_text(json.dumps(manifest, indent=2))
        state = audit(store.path, goal, 'Check dataset manifest')
        (run/'oracle.json').write_text(json.dumps(state, indent=2))
        worker_result = json.loads((run/'worker-result.json').read_text()) if (run/'worker-result.json').exists() else {}
        row = dict(task_id=goal, track='controlled_development', model=args.model, runner=args.runner,
                   supervisor_status=status, error=error, worker_status=worker_result.get('status'),
                   worker_error=worker_result.get('error'), state_correct=state['correct'],
                   committed_effects=len(state['effects']), duplicate_effects=state['duplicate_committed_effects'],
                   model_calls=worker_result.get('model_calls'), tool_calls=worker_result.get('tool_calls'),
                   duration_s=round(time.perf_counter()-start, 3), harm_assessed='duplicate_effects_only',
                   application_load_harm='not_measured', natural_recovery='not observed', output=str(run))
        (run/'result.json').write_text(json.dumps(row, indent=2))
        with (run/'result.csv').open('w', newline='') as f:
            w=csv.DictWriter(f, fieldnames=list(row));w.writeheader();w.writerow(row)
        print(json.dumps(row, indent=2), flush=True)


if __name__ == '__main__':
    main()
