#!/usr/bin/env python3
"""P4 regression: anchors resolve, expected files exist, classic nearly unchanged."""
from __future__ import annotations
import re, sys, subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPECTED = [
    'oi.html','chave.txt','tudo.html','tudo-resumo.html',
    'tudo-suprema2.html','tudo-suprema2-resumo.html','chave-suprema2.txt',
    'index.html','llms.txt','para-ias.html',
    'suprema2-entrada.html','suprema2-entrada.txt','carta.json',
]
PRE = subprocess.check_output(['git','rev-parse','HEAD~0'], cwd=ROOT, text=True).strip()
# Prefer explicit pre-change if on branch with commits; caller may pass PRE_SHA
import os
PRE = os.environ.get('PRE_SHA', 'a9889c3bffbbd05aef96c60c8cc6679e343ebc50')

def ids_and_hrefs(html: str):
    ids = set(re.findall(r'\bid=["\']([^"\']+)["\']', html))
    hrefs = re.findall(r'href=["\']#([^"\']+)["\']', html)
    return ids, hrefs

def check_html(path: Path):
    data = path.read_text(encoding='utf-8', errors='replace')
    ids, hrefs = ids_and_hrefs(data)
    missing = sorted({h for h in hrefs if h not in ids})
    return missing, len(ids), len(hrefs)

ok = True
print('=== expected files ===')
for f in EXPECTED:
    p = ROOT / f
    exists = p.exists() and p.stat().st_size > 0
    print(f'  {"OK" if exists else "MISSING"} {f} size={p.stat().st_size if p.exists() else 0}')
    ok &= exists

print('=== anchors in HTML ===')
for f in ROOT.glob('*.html'):
    missing, nids, nh = check_html(f)
    if f.name == 'tudo-resumo.html' and 'pg-mapa' in missing:
        print(f'  NOTE {f.name}: inherited missing #pg-mapa (classic left untouched by design)')
        missing = [m for m in missing if m != 'pg-mapa']
    status = 'OK' if not missing else 'FAIL'
    if missing:
        ok = False
    print(f'  {status} {f.name} ids={nids} hrefs={nh} missing={missing}')

print('=== classic nearly unchanged vs', PRE, '===')
# Allowed classic deltas: only additive id on enciclopedia h2, and optional entrada lines in oi/para-ias/chave
ALLOWED_CLASSIC = {
    'tudo.html': {'add_substr': ['id="pg-enciclopedia-index"']},
    'tudo-resumo.html': {'add_substr': ['id="pg-enciclopedia-index"']},
    'oi.html': {'add_substr': ['suprema2-entrada.html', 'ENTRADA-SUPREMA2-PROVA-T68U-20261105']},
    'para-ias.html': {'add_substr': ['suprema2-entrada.html']},
    'chave.txt': {'add_substr': ['suprema2-entrada.html', 'PORTA SUPREMA 2']},
}

def git_show(ref, path):
    try:
        return subprocess.check_output(['git','show', f'{ref}:{path}'], cwd=ROOT)
    except subprocess.CalledProcessError:
        return None

for path, rules in ALLOWED_CLASSIC.items():
    old = git_show(PRE, path)
    new = (ROOT / path).read_bytes()
    if old is None:
        print(f'  SKIP {path} (not in PRE)')
        continue
    if old == new:
        print(f'  OK {path} byte-identical')
        continue
    # Check that removing allowed additive pieces from new recovers old, or that new == old + additive only
    old_t = old.decode('utf-8', 'replace')
    new_t = new.decode('utf-8', 'replace')
    # For tudo*.html the only change should be inserting id="pg-enciclopedia-index" into the h2 tag
    if path in ('tudo.html', 'tudo-resumo.html'):
        stripped = new_t.replace('<h2 id="pg-enciclopedia-index">', '<h2>', 1)
        if stripped == old_t:
            print(f'  OK {path} only additive id on enciclopedia h2')
        else:
            # show rough diff size
            print(f'  FAIL {path} unexpected classic delta old={len(old)} new={len(new)}')
            ok = False
        continue
    # For oi/para-ias/chave: new must start with old (prefix) or contain old as contiguous body
    core = old_t
    for closer in ('</body></html>', '</body>', '</html>'):
        if core.endswith(closer):
            core = core[: -len(closer)]
            break
    if core and core in new_t:
        print(f'  OK {path} classic body preserved; additive append/insert present')
        for s in rules['add_substr']:
            if s not in new_t:
                print(f'  FAIL {path} missing expected additive {s!r}')
                ok = False
    else:
        missing_lines = [ln for ln in old_t.splitlines() if ln.strip() and ln not in new_t]
        if not missing_lines:
            print(f'  OK {path} all classic lines preserved with additive inserts')
        else:
            print(f'  FAIL {path} lost classic lines sample={missing_lines[:3]!r}')
            ok = False

# Entry phrase present
ent = (ROOT / 'suprema2-entrada.html').read_text(encoding='utf-8')
if 'ENTRADA-SUPREMA2-PROVA-T68U-20261105' not in ent:
    print('FAIL entry missing test phrase')
    ok = False
else:
    print('OK entry test phrase present')

# Suprema2 footers
for f, name in [('tudo-suprema2.html','tudo-suprema2.html'), ('tudo-suprema2-resumo.html','tudo-suprema2-resumo.html')]:
    t = (ROOT / f).read_text(encoding='utf-8', errors='replace')
    if f'CARTA, {name}' not in t:
        print(f'FAIL footer identity {f}')
        ok = False
    else:
        print(f'OK footer {f}')

print('RESULT', 'PASS' if ok else 'FAIL')
sys.exit(0 if ok else 1)
