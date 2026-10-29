"""Record installed local setup and binary provenance without inference."""
import hashlib
import importlib.metadata
import json
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    sha = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            sha.update(chunk)
    return sha.hexdigest()


with sync_playwright() as playwright:
    chromium_path = Path(playwright.chromium.executable_path)
report = dict(utc=datetime.now(timezone.utc).isoformat(), python=platform.python_version(),
              python_executable=sys.executable,
              uv=subprocess.check_output([str(ROOT / '.tools/uv/uv.exe'), '--version'], text=True).strip(),
              uv_archive_sha256=digest(ROOT / '.tools/uv.zip'),
              uv_archive_url='https://github.com/astral-sh/uv/releases/download/0.13.6/uv-x86_64-pc-windows-msvc.zip',
              dependency_lock_sha256=digest(ROOT / 'requirements-pilot.lock'),
              chromium_executable=str(chromium_path), chromium_sha256=digest(chromium_path),
              packages={p.metadata['Name']: p.version for p in importlib.metadata.distributions()},
              live_model=False, paid_services_used=False)
(ROOT / 'data/setup/runtime-manifest.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
print('Saved local runtime, package and binary manifest.')
