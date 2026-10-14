#!/usr/bin/env python3
"""Static release checks; no secrets, dependencies, remote or production writes."""
from pathlib import Path
import json
import re
import subprocess
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
folders = ['site', 'macos', 'scripts', 'tests', 'docs']
failures = []
files = [p for folder in folders for p in (ROOT / folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts]
files += [ROOT / 'README.md', ROOT / 'LICENSE', ROOT / '.gitignore']
secret_pattern = re.compile(rb'-----BEGIN (?:OPENSSH|RSA|EC|DSA|PRIVATE).*PRIVATE KEY|\bgh[pousr]_[A-Za-z0-9_]{20,}|\bgithub_pat_[A-Za-z0-9_]{20,}|\bsk-[A-Za-z0-9_-]{20,}')
for p in files:
    relative = str(p.relative_to(ROOT))
    if p.stat().st_size > 50 * 1024 * 1024:
        failures.append('oversize ' + relative)
    data = p.read_bytes()
    if secret_pattern.search(data):
        failures.append('secret-format ' + relative)
    if p.suffix == '.json':
        json.loads(data)
    if p.suffix == '.sh':
        result = subprocess.run(['bash', '-n', str(p)], capture_output=True, text=True)
        if result.returncode:
            failures.append('shell-syntax ' + relative)
    if p.suffix == '.md':
        for target in re.findall(r'\[[^\]]*\]\(([^)]+)\)', data.decode()):
            target = target.split('#')[0]
            if target and not re.match(r'\w+://|mailto:', target) and not (p.parent / unquote(target)).exists():
                failures.append('broken-link ' + relative + ' -> ' + target)
    if p.suffix == '.html':
        text = data.decode()
        for target in re.findall(r'(?:src|href)="([^"#]+)"', text):
            if re.match(r'\w+://', target):
                continue
            if not (p.parent / target.split('#')[0]).exists():
                failures.append('broken-html-asset ' + relative + ' -> ' + target)
        if 'http-equiv="Content-Security-Policy"' not in text:
            failures.append('missing-csp ' + relative)
print(json.dumps({'files_checked': len(files), 'failures': failures}, ensure_ascii=False, indent=2))
raise SystemExit(bool(failures))
