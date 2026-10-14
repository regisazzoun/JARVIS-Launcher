#!/usr/bin/env python3
"""Build standalone Pages files and a reviewed source ZIP; no npm required."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
subprocess.run([sys.executable, str(ROOT / 'scripts/validate.py')], check=True)
files = ['index.html', 'guide.html', 'style.css', 'app.js', 'core.js', 'config.json', 'icon.svg']
config = json.loads((ROOT / 'site/config.json').read_text())
assert config['version'] == 1
out = ROOT / 'dist/pages'
out.mkdir(parents=True, exist_ok=True)
for name in files:
    shutil.copyfile(ROOT / 'site' / name, out / name)
(out / '.nojekyll').write_text('')
sources = []
for parent in ['site', 'macos', 'scripts', 'tests', 'docs']:
    sources.extend(p for p in (ROOT / parent).rglob('*') if p.is_file() and '__pycache__' not in p.parts)
sources.extend(ROOT / name for name in ['README.md', 'LICENSE', '.gitignore'])
archive = ROOT / 'dist/JARVIS-Launcher-JL-01.zip'
with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as bundle:
    for source in sorted(sources):
        bundle.write(source, 'JARVIS-Launcher/' + str(source.relative_to(ROOT)))
manifest = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}
manifest[str(archive.relative_to(ROOT))] = hashlib.sha256(archive.read_bytes()).hexdigest()
(ROOT / 'dist/SHA256.json').write_text(json.dumps(manifest, indent=2) + '\n')
print(f'Pages : {out}\nSources : {archive}\nSHA-256 : {ROOT / "dist/SHA256.json"}')
