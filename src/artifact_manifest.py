"""Hash study artifacts and vendored source; exclude Git internals and generated caches."""
import csv
import hashlib
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / 'results/checksums.csv'
rows = []
paths = []
for directory, directories, files in os.walk(ROOT):
    directories[:] = sorted(d for d in directories if d not in {'.git', '__pycache__', '.venv', '.tools'})
    paths.extend(Path(directory) / name for name in sorted(files))
for path in sorted(paths):
    relative = path.relative_to(ROOT)
    if path == DEST or any(part in {'.git', '__pycache__', '.venv', '.tools'} for part in relative.parts):
        continue
    if not path.is_file() or path.is_symlink():
        continue
    sha = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            sha.update(chunk)
    rows.append(dict(path=relative.as_posix(), sha256=sha.hexdigest()))
with DEST.open('w', newline='', encoding='utf-8') as stream:
    writer = csv.DictWriter(stream, fieldnames=['path', 'sha256'])
    writer.writeheader()
    writer.writerows(rows)
print(f'Hashed {len(rows)} files to {DEST}')
