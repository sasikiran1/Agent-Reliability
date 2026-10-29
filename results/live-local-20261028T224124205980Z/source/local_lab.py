"""Private persistent job application and independent SQL oracle. Stdlib only."""
import hashlib
import json
import sqlite3
import threading
import time
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


def utc():
    return datetime.now(timezone.utc).isoformat()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'))


class Trace:
    def __init__(self, path):
        self.path = Path(path)
        self.lock = threading.Lock()
        self.start = time.perf_counter()

    def emit(self, kind, **fields):
        row = dict(utc=utc(), monotonic_ns=time.perf_counter_ns(),
                   elapsed_ms=(time.perf_counter() - self.start) * 1000,
                   event_id=str(uuid.uuid4()), kind=kind, **fields)
        with self.lock, self.path.open('a', encoding='utf-8') as stream:
            stream.write(canonical(row) + '\n')
            stream.flush()
        return row['event_id']


class JobStore:
    def __init__(self, path):
        self.path = Path(path).resolve()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.executescript('''
                CREATE TABLE IF NOT EXISTS jobs (
                  job_id TEXT PRIMARY KEY, goal_id TEXT NOT NULL, title TEXT NOT NULL,
                  priority TEXT NOT NULL, state TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS effects (
                  effect_id TEXT PRIMARY KEY, goal_id TEXT NOT NULL, job_id TEXT NOT NULL,
                  attempt_id TEXT NOT NULL, committed_utc TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS idempotency (
                  key TEXT PRIMARY KEY, payload TEXT NOT NULL, response TEXT NOT NULL);
            ''')

    def connect(self):
        db = sqlite3.connect(self.path, timeout=5)
        db.row_factory = sqlite3.Row
        return db

    def create(self, goal, args, attempt, key=None):
        if set(args) != {'title', 'priority'}:
            raise ValueError('create_job requires exactly title and priority')
        if not isinstance(args['title'], str) or not 1 <= len(args['title']) <= 200:
            raise ValueError('Invalid title')
        if args['priority'] not in ('normal', 'high'):
            raise ValueError('Invalid priority')
        payload = canonical(dict(goal_id=goal, **args))
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            if key:
                old = db.execute('SELECT * FROM idempotency WHERE key=?', (key,)).fetchone()
                if old:
                    if old['payload'] != payload:
                        raise ValueError('Idempotency key reused with different payload')
                    return dict(json.loads(old['response']), deduplicated=True)
            job_id, effect_id = str(uuid.uuid4()), str(uuid.uuid4())
            db.execute('INSERT INTO jobs VALUES (?,?,?,?,?)',
                       (job_id, goal, args['title'], args['priority'], 'pending'))
            db.execute('INSERT INTO effects VALUES (?,?,?,?,?)',
                       (effect_id, goal, job_id, attempt, utc()))
            result = dict(job_id=job_id, effect_id=effect_id, **args, state='pending', deduplicated=False)
            if key:
                db.execute('INSERT INTO idempotency VALUES (?,?,?)', (key, payload, canonical(result)))
            return result

    def jobs(self, goal):
        with self.connect() as db:
            return [dict(r) for r in db.execute('SELECT * FROM jobs WHERE goal_id=? ORDER BY job_id', (goal,))]

    def reset(self):
        # Administrative operation on disposable data. Agent cannot call this.
        with self.connect() as db:
            for table in ('jobs', 'effects', 'idempotency'):
                db.execute(f'DELETE FROM {table}')


def audit(path, goal, expected_title, expected_priority='normal'):
    """Independent read-only SQL connection; never trust tool/agent completion text."""
    with sqlite3.connect(f'file:{Path(path).resolve().as_posix()}?mode=ro', uri=True) as db:
        db.row_factory = sqlite3.Row
        jobs = [dict(r) for r in db.execute('SELECT * FROM jobs WHERE goal_id=? ORDER BY job_id', (goal,))]
        effects = [dict(r) for r in db.execute('SELECT * FROM effects WHERE goal_id=? ORDER BY effect_id', (goal,))]
        state = {table: [tuple(r) for r in db.execute(f'SELECT * FROM {table} ORDER BY 1')]
                 for table in ('jobs', 'effects', 'idempotency')}
    correct = (len(jobs) == len(effects) == 1 and jobs[0]['title'] == expected_title
               and jobs[0]['priority'] == expected_priority and jobs[0]['state'] == 'pending'
               and effects[0]['job_id'] == jobs[0]['job_id'])
    return dict(correct=correct, jobs=jobs, effects=effects, duplicate_committed_effects=max(0, len(effects)-1),
                final_state_sha256=hashlib.sha256(canonical(state).encode()).hexdigest())


@contextmanager
def serve(store, trace):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_POST(self):
            start = time.perf_counter()
            body = {}
            result, error, status = None, None, 200
            try:
                if self.path != '/tools':
                    raise ValueError('Unknown path')
                size = int(self.headers.get('Content-Length', '0'))
                if not 0 < size < 65536:
                    raise ValueError('Invalid request size')
                body = json.loads(self.rfile.read(size))
                goal, attempt = body['goal_id'], body['attempt_id']
                if body['tool'] == 'create_job':
                    result = store.create(goal, body['arguments'], attempt, body.get('idempotency_key'))
                elif body['tool'] == 'list_jobs':
                    if body['arguments']:
                        raise ValueError('list_jobs takes no arguments')
                    result = dict(jobs=store.jobs(goal))
                else:
                    raise ValueError('Unknown tool')
                if body.get('intervention') == 'drop_reply_after_commit':
                    trace.emit('application_request', request=body, response=result, http_status=None,
                               committed_effect_ids=[result['effect_id']] if 'effect_id' in result else [],
                               response_intentionally_lost=True, service_ms=(time.perf_counter()-start)*1000)
                    self.close_connection = True
                    return
            except (ValueError, KeyError, json.JSONDecodeError) as exc:
                status, error = 409, str(exc)
                result = dict(error=error)
            except Exception as exc:
                status, error = 500, repr(exc)
                result = dict(error=error)
            trace.emit('application_request', request=body, response=result, http_status=status,
                       committed_effect_ids=[result['effect_id']] if result and 'effect_id' in result else [],
                       error=error, service_ms=(time.perf_counter()-start)*1000)
            encoded = canonical(result).encode()
            self.send_response(status)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(encoded)))
            self.end_headers()
            self.wfile.write(encoded)

    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    server.daemon_threads = True
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f'http://127.0.0.1:{server.server_port}'
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
