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
                  attempt_id TEXT NOT NULL, committed_utc TEXT NOT NULL,
                  action TEXT NOT NULL, before_json TEXT, after_json TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS dependencies (child_id TEXT PRIMARY KEY, parent_id TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS idempotency (
                  key TEXT PRIMARY KEY, payload TEXT NOT NULL, response TEXT NOT NULL);
                CREATE TRIGGER IF NOT EXISTS record_job_insert AFTER INSERT ON jobs BEGIN
                  INSERT INTO effects VALUES(lower(hex(randomblob(16))),new.goal_id,new.job_id,ars_attempt(),
                    strftime('%Y-%m-%dT%H:%M:%fZ','now'),'create_job',NULL,
                    json_object('title',new.title,'priority',new.priority,'state',new.state)); END;
                CREATE TRIGGER IF NOT EXISTS record_job_update AFTER UPDATE ON jobs BEGIN
                  INSERT INTO effects VALUES(lower(hex(randomblob(16))),new.goal_id,new.job_id,ars_attempt(),
                    strftime('%Y-%m-%dT%H:%M:%fZ','now'),'update_job',
                    json_object('title',old.title,'priority',old.priority,'state',old.state),
                    json_object('title',new.title,'priority',new.priority,'state',new.state)); END;
            ''')

    @contextmanager
    def connect(self, attempt='administrative'):
        db = sqlite3.connect(self.path, timeout=5)
        db.row_factory = sqlite3.Row
        db.create_function('ars_attempt', 0, lambda: attempt)
        try:
            with db:
                yield db
        finally:
            db.close()

    def create(self, goal, args, attempt, key=None):
        if set(args) != {'title', 'priority'}:
            raise ValueError('create_job requires exactly title and priority')
        if not isinstance(args['title'], str) or not 1 <= len(args['title']) <= 200:
            raise ValueError('Invalid title')
        if args['priority'] not in ('normal', 'high'):
            raise ValueError('Invalid priority')
        payload = canonical(dict(goal_id=goal, **args))
        with self.connect(attempt) as db:
            db.execute('BEGIN IMMEDIATE')
            if key:
                old = db.execute('SELECT * FROM idempotency WHERE key=?', (key,)).fetchone()
                if old:
                    if old['payload'] != payload:
                        raise ValueError('Idempotency key reused with different payload')
                    return dict(json.loads(old['response']), deduplicated=True)
            job_id = str(uuid.uuid4())
            db.execute('INSERT INTO jobs VALUES (?,?,?,?,?)',
                       (job_id, goal, args['title'], args['priority'], 'pending'))
            effect_id = db.execute('SELECT effect_id FROM effects WHERE job_id=? ORDER BY rowid DESC LIMIT 1', (job_id,)).fetchone()[0]
            result = dict(job_id=job_id, effect_id=effect_id, **args, state='pending', deduplicated=False)
            if key:
                db.execute('INSERT INTO idempotency VALUES (?,?,?)', (key, payload, canonical(result)))
            return result

    def jobs(self, goal):
        with self.connect() as db:
            return [dict(r) for r in db.execute('SELECT * FROM jobs WHERE goal_id=? ORDER BY job_id', (goal,))]

    def seed(self, goal, fixture):
        with self.connect('seed') as db:
            for i, title in enumerate(fixture['records']):
                db.execute('INSERT INTO jobs VALUES (?,?,?,?,?)', (f'record-{i+1}', goal, title, 'normal', 'pending'))

    def update(self, goal, args, attempt):
        if set(args) != {'job_id', 'priority'} or args['priority'] not in ('normal', 'high'):
            raise ValueError('update_job requires job_id and valid priority')
        with self.connect(attempt) as db:
            db.execute('BEGIN IMMEDIATE')
            if not db.execute('SELECT 1 FROM jobs WHERE job_id=? AND goal_id=?', (args['job_id'], goal)).fetchone():
                raise ValueError('Job not found')
            db.execute('UPDATE jobs SET priority=? WHERE job_id=?', (args['priority'], args['job_id']))
            effect = db.execute('SELECT effect_id FROM effects WHERE job_id=? ORDER BY rowid DESC LIMIT 1', (args['job_id'],)).fetchone()[0]
        return dict(job_id=args['job_id'], priority=args['priority'], effect_id=effect)

    def followup(self, goal, args, attempt):
        if set(args) != {'parent_job_id', 'title'} or not isinstance(args['title'], str) or not 1 <= len(args['title']) <= 200:
            raise ValueError('create_followup requires parent_job_id and title')
        with self.connect(attempt) as db:
            db.execute('BEGIN IMMEDIATE')
            parent = db.execute('SELECT * FROM jobs WHERE job_id=? AND goal_id=?', (args['parent_job_id'], goal)).fetchone()
            if not parent or parent['priority'] != 'high':
                raise ValueError('Parent must exist and have high priority first')
            job_id = str(uuid.uuid4())
            db.execute('INSERT INTO jobs VALUES (?,?,?,?,?)', (job_id, goal, args['title'], 'normal', 'pending'))
            db.execute('INSERT INTO dependencies VALUES (?,?)', (job_id, args['parent_job_id']))
            effect = db.execute('SELECT effect_id FROM effects WHERE job_id=?', (job_id,)).fetchone()[0]
        return dict(job_id=job_id, parent_job_id=args['parent_job_id'], effect_id=effect)

    def reset(self):
        # Administrative operation on disposable data. Agent cannot call this.
        with self.connect() as db:
            for table in ('dependencies', 'jobs', 'effects', 'idempotency'):
                db.execute(f'DELETE FROM {table}')


def audit(path, goal, expected_title, expected_priority='normal'):
    """Independent read-only SQL connection; never trust tool/agent completion text."""
    with sqlite3.connect(f'file:{Path(path).resolve().as_posix()}?mode=ro', uri=True) as db:
        db.row_factory = sqlite3.Row
        jobs = [dict(r) for r in db.execute('SELECT * FROM jobs WHERE goal_id=? ORDER BY job_id', (goal,))]
        effects = [dict(r) for r in db.execute('SELECT * FROM effects WHERE goal_id=? ORDER BY effect_id', (goal,))]
        state = {table: [tuple(r) for r in db.execute(f'SELECT * FROM {table} ORDER BY 1')]
                 for table in ('jobs', 'effects', 'idempotency', 'dependencies')}
    correct = (len(jobs) == len(effects) == 1 and jobs[0]['title'] == expected_title
               and jobs[0]['priority'] == expected_priority and jobs[0]['state'] == 'pending'
               and effects[0]['job_id'] == jobs[0]['job_id'])
    return dict(correct=correct, jobs=jobs, effects=effects, duplicate_committed_effects=max(0, len(effects)-1),
                final_state_sha256=hashlib.sha256(canonical(state).encode()).hexdigest())


def workflow_audit(path, goal, fixture):
    with sqlite3.connect(f'file:{Path(path).resolve().as_posix()}?mode=ro', uri=True) as db:
        db.row_factory = sqlite3.Row
        jobs = [dict(r) for r in db.execute('SELECT * FROM jobs WHERE goal_id=? ORDER BY job_id', (goal,))]
        effects = [dict(r) for r in db.execute("SELECT * FROM effects WHERE goal_id=? AND attempt_id!='seed' ORDER BY rowid", (goal,))]
        all_effects = [dict(r) for r in db.execute('SELECT * FROM effects WHERE goal_id=? ORDER BY rowid', (goal,))]
        deps = [dict(r) for r in db.execute('SELECT * FROM dependencies ORDER BY child_id')]
    originals = {f'record-{i+1}': title for i, title in enumerate(fixture['records'])}
    target = next(k for k, v in originals.items() if v == fixture['target'])
    children = [j for j in jobs if j['job_id'] not in originals]
    originals_ok = all(any(j['job_id']==k and j['title']==title and j['priority']==('high' if k==target else 'normal')
                          and j['state']=='pending' for j in jobs) for k,title in originals.items())
    correct = (originals_ok and len(jobs)==len(originals)+1 and len(children)==1
               and children[0]['title']==fixture['followup'] and children[0]['priority']=='normal'
               and deps==[dict(child_id=children[0]['job_id'], parent_id=target)]
               and len(effects)==2 and [e['action'] for e in effects]==['update_job','create_job']
               and effects[0]['job_id']==target and effects[1]['job_id']==children[0]['job_id'])
    # Verify journal tail agrees with actual rows; a missing/extra record is a measurement failure.
    tail = {e['job_id']: json.loads(e['after_json']) for e in all_effects}
    consistent = (set(tail)=={j['job_id'] for j in jobs} and
                  all(any(j['job_id']==key and all(j[field]==expected for field,expected in values.items()) for j in jobs)
                      for key,values in tail.items()))
    return dict(correct=bool(correct and consistent), journal_consistent=consistent, jobs=jobs, effects=effects, dependencies=deps,
                duplicate_committed_effects=max(0, len(children)-1),
                extra_update_effects=max(0, sum(e['action']=='update_job' for e in effects)-1),
                final_state_sha256=hashlib.sha256(canonical(dict(jobs=jobs,effects=effects,dependencies=deps)).encode()).hexdigest())


@contextmanager
def serve(store, trace):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_GET(self):
            encoded = canonical(dict(ready=True, storage='sqlite', journal='transactional_database_triggers')).encode()
            self.send_response(200 if self.path=='/ready' else 404)
            self.send_header('Content-Length',str(len(encoded)))
            self.end_headers()
            self.wfile.write(encoded)

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
                if body.get('intervention')=='delay_before_execution_100ms':
                    time.sleep(0.1)
                goal, attempt = body['goal_id'], body['attempt_id']
                if body['tool'] == 'create_job':
                    result = store.create(goal, body['arguments'], attempt, body.get('idempotency_key'))
                elif body['tool'] == 'list_jobs':
                    if body['arguments']:
                        raise ValueError('list_jobs takes no arguments')
                    result = dict(jobs=store.jobs(goal))
                elif body['tool'] == 'update_job':
                    result = store.update(goal, body['arguments'], attempt)
                elif body['tool'] == 'create_followup':
                    result = store.followup(goal, body['arguments'], attempt)
                else:
                    raise ValueError('Unknown tool')
                if body.get('intervention') == 'drop_reply_after_commit':
                    trace.emit('application_request', request=body, response=result, http_status=None,
                               committed_effect_ids=[result['effect_id']] if 'effect_id' in result and not result.get('deduplicated') else [],
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
                       committed_effect_ids=[result['effect_id']] if result and 'effect_id' in result and not result.get('deduplicated') else [],
                       error=error, service_ms=(time.perf_counter()-start)*1000)
            encoded = canonical(result).encode()
            self.send_response(status)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(encoded)))
            self.end_headers()
            try:
                self.wfile.write(encoded)
            except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
                trace.emit('client_disconnected_before_reply', attempt_id=body.get('attempt_id'))

    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    server.daemon_threads = False
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f'http://127.0.0.1:{server.server_port}'
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
