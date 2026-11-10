#!/usr/bin/env python3
"""Porta 02 — regressão dos testes A–G (estruturais). Uso: python3 scripts/p02_regressao.py  → sai 1 se algo falhar."""
import hashlib, html, json, re, shutil, subprocess, sys, tempfile
sys.dont_write_bytecode = True
from collections import deque
from pathlib import Path
R = Path(__file__).resolve().parents[1]
BASE = "8b4fe864a88a4c3dbd0f63ad2fffcdd680fa4c49"
SITE = "https://espirrosaga2020-tech.github.io/carta-porta/"
sys.path.insert(0, str(R / "scripts"))
res = {}
def caso(nome, ok, detalhe=""):
    res[nome] = {"resultado": "PASSOU" if ok else "FALHOU", "detalhe": detalhe}
git = lambda *a: subprocess.check_output(["git", *a], cwd=R)
base_files = git("ls-tree", "-r", "--name-only", BASE).decode().splitlines()
MARCAS = [("<!-- P02-INICIO: bloco aditivo Porta 02 Intergaláctica (protótipo 10/11/2026); removível sem afetar o resto -->\n", "<!-- P02-FIM -->\n"),
          ("=== P02-INICIO (bloco aditivo Porta 02 Intergaláctica, protótipo 10/11/2026) ===\n", "=== P02-FIM ===\n\n"),
          ("<!-- P02-INICIO -->\n", "<!-- P02-FIM -->\n")]
def sem_blocos(b: str) -> str:
    for ini, fim in MARCAS:
        while ini in b:
            a = b.index(ini); z = b.index(fim, a) + len(fim); b = b[:a] + b[z:]
    return b
def visivel(s):
    s = re.sub(r"(?is)<(script|style)\b.*?</\1>", " ", s); s = re.sub(r"<[^>]+>", " ", s); return re.sub(r"\s+", " ", html.unescape(s))

# ---------- F (originais) + A (entrada)
alterados, intactos, quebrados = [], 0, []
for f in base_files:
    old = git("show", f"{BASE}:{f}")
    p = R / f
    if not p.exists(): quebrados.append(f + " (APAGADO)"); continue
    new = p.read_bytes()
    if new == old: intactos += 1; continue
    if sem_blocos(new.decode("utf-8")).encode("utf-8") == old: alterados.append(f)
    else: quebrados.append(f)
novos = [l[3:] for l in subprocess.check_output(["git", "status", "--porcelain", "--untracked-files=all"], cwd=R, text=True).splitlines() if l.startswith("??")]
novos += [f for f in git("diff", "--name-only", "--diff-filter=A", BASE, "HEAD").decode().splitlines()]
fora = [f for f in set(novos) if not (f.startswith("p02-") or f == "404.html" or f.startswith("scripts/p02_"))]
caso("F1_originais_intactos_fora_dos_blocos_P02", not quebrados and not fora,
     f"{intactos} byte-idênticos; {len(alterados)} só com bloco P02: {alterados}; quebrados: {quebrados}; novos fora da camada: {fora}")
ent_old = git("show", f"{BASE}:suprema2-entrada.html").decode()
ent_new = (R / "suprema2-entrada.html").read_text()
frases = ["ENTRADA-SUPREMA2-PROVA-T68U-20261105", "OURO-PORTA-SUPREMA2-20261105-KUALA", "Quatro etapas separadas (P3)", "registro.v1", "nomes-portas-t74u", "mapa-central-t71u", "frase-teste"]
hrefs_old = set(re.findall(r'href="([^"]+)"', ent_old)); hrefs_new = set(re.findall(r'href="([^"]+)"', ent_new))
primeiro = ent_new[:ent_new.find("<h1>")]
botoes = all(x in primeiro for x in ["PORTA 02", "COMEÇAR A VIAGEM", 'role="search"', "EXPLORAR O MAPA", "VER O ÍNDICE TEXTUAL", "DESCOBERTA SURPRESA"])
caso("A_entrada_preservada_e_primeiro_quadro", all(f in ent_new for f in frases) and hrefs_old <= hrefs_new and botoes and "<script" not in ent_new,
     f"{len(hrefs_old)} links antigos todos presentes; primeiro quadro com PORTA 02/COMEÇAR/busca/MAPA/ÍNDICE/SURPRESA={botoes}; entrada continua sem JavaScript")
anc = json.loads(Path("/workspace/porta02/fotografia/ancoras.json").read_text()) if Path("/workspace/porta02/fotografia/ancoras.json").exists() else {}
faltam = [(f, a) for f, ids in anc.items() for a in ids if f'id="{a}"' not in (R / f).read_text(errors="ignore")]
caso("A2_todas_as_ancoras_da_fotografia_preservadas", not faltam, f"{sum(len(v) for v in anc.values())} âncoras conferidas; faltando: {faltam[:5]}")
t68 = subprocess.run([sys.executable, "scripts/t68u_regressao_ancoras.py"], cwd=R, capture_output=True, text=True)
caso("A3_regressao_t68u_original", t68.returncode == 0 and "RESULT PASS" in t68.stdout, t68.stdout.strip().splitlines()[-1] if t68.stdout else t68.stderr[-300:])

# ---------- links (todas as páginas html/txt novas e alteradas)
def links_de(rel):
    s = (R / rel).read_text(errors="ignore")
    if rel.endswith(".html"): out = re.findall(r'href="([^"#?][^"]*)"', s) + re.findall(r'href="(#[^"]+)"', s)
    else: out = re.findall(re.escape(SITE) + r'([^\s)>"·]+)', s)
    return out
def resolve(rel, h):
    h = h.replace(SITE, "")
    if h.startswith(("http://", "https://", "mailto:")): return None
    if h.startswith("/carta-porta/"): h = h[len("/carta-porta/"):]
    alvo, _, frag = h.partition("#"); alvo = alvo.split("?")[0]
    base_dir = Path(rel).parent
    alvo = str((base_dir / alvo)) if alvo else rel
    alvo = re.sub(r"(^|/)\./", r"\1", alvo)
    return alvo, frag
verificar = [f for f in set(novos) | set(alterados) if f.endswith((".html", ".txt")) and not f.startswith("scripts/")]
ruins = []
for rel in verificar:
    for h in links_de(rel):
        r = resolve(rel, h)
        if not r: continue
        alvo, frag = r
        if not (R / alvo).is_file(): ruins.append(f"{rel} → {h}"); continue
        if frag and alvo.endswith(".html") and f'id="{frag}"' not in (R / alvo).read_text(errors="ignore"): ruins.append(f"{rel} → {h} (âncora)")
caso("E2_links_quebrados_nas_paginas_novas_e_alteradas", not ruins, f"{len(verificar)} arquivos verificados; quebrados: {ruins[:10]}")

# ---------- B (sem JS) + saltos
cat = json.loads((R / "p02-catalogo.json").read_text())["publicacoes"]
def vizinhos(rel):
    if not (R / rel).is_file() or not rel.endswith((".html", ".txt")): return []
    out = []
    for h in links_de(rel):
        r = resolve(rel, h)
        if r and (R / r[0]).is_file(): out.append(r[0])
    return out
dist = {"suprema2-entrada.html": 0}; fila = deque(["suprema2-entrada.html"])
while fila:
    u = fila.popleft()
    if dist[u] >= 3: continue
    for v in vizinhos(u):
        if v not in dist: dist[v] = dist[u] + 1; fila.append(v)
alvos = [i["arquivo"] for i in cat]
longe = [a for a in alvos if dist.get(a, 99) > 3]
mapa_txt = (R / "suprema2-mapa.txt").read_text(); temas = (R / "p02-indice-temas.txt").read_text()
fonte_ok = "suprema2-acervo-025.html" in temas and "Calçada, Caderno e DUNADA" in (R / "suprema2-acervo-025.html").read_text()
caso("B_sem_JS_mapa_indice_fonte_e_3_saltos", not longe and "suprema2-mapa.html" in mapa_txt and fonte_ok,
     f"{len(alvos) - len(longe)}/{len(alvos)} publicações a ≤3 saltos da entrada só por links estáticos; acima de 3: {longe[:8]}")

# ---------- C (Jornada, registro, caderninho, diários)
jornada = ["suprema2-jornada.html", "suprema2-jornada.txt", "tudo.html", "suprema2-acervo-052.html", "suprema2-acervo-053.html", "suprema2-acervo-055.html", "suprema2-acervo-059.html", "suprema2-acervo-063.html", "suprema2-acervo-010.html"]
iguais = all((R / f).read_bytes() == git("show", f"{BASE}:{f}") for f in jornada)
v2 = (R / "p02-registro-v2.txt").read_text()
campos_v1 = []
for f in ["suprema2-acervo-055.txt", "suprema2-acervo-010.txt"]:
    t = (R / f).read_text()
    campos_v1 += [l.strip() for l in t.splitlines() if re.match(r"^(\d+\. )?[A-ZÁÂÃÉÊÍÓÔÕÚÇ_ ]{4,}[^:]*:", l.strip()) and "http" not in l and "Prova" not in l]
bloco_ent = re.search(r"<pre>REGISTRO DE VIAGEM.*?</pre>", ent_old, re.S).group(0)
campos_v1 += [l.strip() for l in html.unescape(bloco_ent[5:-6]).splitlines() if ":" in l and not l.startswith("versao")]
def rotulo(l): return l.split(":")[0].strip() + ":"
def presente(r): return r in v2 or (r[:-1] + " (") in v2      # "DATA E HORA:" (T112U) == "DATA E HORA (America/Sao_Paulo):" (t68u)
faltando = sorted({rotulo(c) for c in campos_v1 if not presente(rotulo(c))})
caso("C_jornada_registro_caderninho_diarios", iguais and not faltando and "registro.v1" in v2 and "CADERNINHO" in v2,
     f"{len(jornada)} páginas da Jornada/registro/caderninho byte-idênticas={iguais}; {len(set(map(rotulo, campos_v1)))} rótulos v1 conferidos no v2; faltando: {faltando}")

# ---------- D (roteiros e surpresa só com fontes reais)
C = json.loads((R / "scripts/p02_conteudo.json").read_text())
cit_ruins = [c["id"] for c in C["curiosidades"] if c["citacao"] not in visivel((R / c["url"]).read_text())]
paradas = [p["url"] for r in C["roteiros"] for p in r["paradas"]] + [s["url"] for s in C["salas"]] + [s["txt"] for s in C["salas"]]
ausentes = [u for u in paradas if not (R / u).is_file()]
surp = (R / "p02-surpresa.html").read_text()
surp_links = [h for h in re.findall(r'href="([^"#]+)"', surp) if not h.startswith("http")]
surp_ruins = [h for h in surp_links if not (R / h).is_file()]
caso("D_roteiros_e_surpresa_com_fontes_reais", not cit_ruins and not ausentes and not surp_ruins,
     f"{len(C['curiosidades'])} citações literais conferidas na fonte; {len(paradas)} paradas existem; citações ausentes: {cit_ruins}; paradas ausentes: {ausentes}")

# ---------- E (busca antiga preservada)
antiga_ok = (R / "suprema2-busca-indice.json").read_bytes() == git("show", f"{BASE}:suprema2-busca-indice.json") and \
            sem_blocos((R / "suprema2-busca.html").read_text()).encode() == git("show", f"{BASE}:suprema2-busca.html")
caso("E1_busca_antiga_intacta_e_visivel", antiga_ok and 'href="suprema2-busca.html"' in ent_new and 'href="suprema2-busca.html"' in (R / "p02-busca.html").read_text(),
     "índice antigo byte-idêntico; suprema2-busca.html só ganhou 1 linha P02; link para a busca antiga na entrada e na busca nova")

# ---------- F2 (privacidade nos arquivos novos)
import p02_construir as P
achados = {}
for f in set(novos):
    if f.startswith("scripts/"): continue
    t = (R / f).read_text(errors="ignore")
    a = P.achados_privacidade(t if not f.endswith(".html") else visivel(t))
    if a: achados[f] = a
sc = json.loads(subprocess.check_output([sys.executable, "/workspace/porta02/tools/scanner_segredos.py", str(R), ",".join(f for f in set(novos))], text=True)) \
     if Path("/workspace/porta02/tools/scanner_segredos.py").exists() else {"criticos": [], "resumo": {}}
caso("F2_zero_privado_nos_arquivos_novos", not achados and not sc["criticos"] and not sc["resumo"],
     f"filtro do gerador original nos novos: {achados or 'limpo'}; scanner de segredos nos novos: {sc['resumo'] or 'limpo'}")

# ---------- G (nova publicação aprovada atualiza tudo sem edição manual)
hash_ruins = [i["arquivo"] for i in cat if hashlib.sha256((R / i["arquivo"]).read_bytes()).hexdigest() != i["sha256"]]
tmp = Path(tempfile.mkdtemp(prefix="p02g_")); dst = tmp / "repo"
shutil.copytree(R, dst, ignore=shutil.ignore_patterns("node_modules"))
(dst / "exemplo-teste-g.html").write_text('<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><title>Sala de teste G — Planetário Kuala</title></head><body><h1>Sala de teste G</h1><p>Texto de teste com a palavra zumbatronico.</p></body></html>', encoding="utf-8")
(dst / "exemplo-rejeitado.html").write_text('<!doctype html><html><head><title>Rejeitado</title></head><body>sem aprovação</body></html>', encoding="utf-8")
lb = json.loads((dst / "scripts/p02_lista_branca.json").read_text())
lb["adicionais"] = [{"arquivo": "exemplo-teste-g.html", "resumo": "Página fictícia só para o teste G.", "assunto": "origem", "data_fonte": "01/01/2026", "data_publicacao": "10/11/2026", "aprovado_por": "TESTE G (simulação)"},
                    {"arquivo": "exemplo-rejeitado.html", "assunto": "origem"}]
(dst / "scripts/p02_lista_branca.json").write_text(json.dumps(lb, ensure_ascii=False))
rr = subprocess.run([sys.executable, "scripts/p02_construir.py"], cwd=dst, capture_output=True, text=True)
onde = {f: ("exemplo-teste-g.html" in (dst / f).read_text()) for f in ["p02-catalogo.json", "p02-indice-temas.txt", "p02-indice-a-z.txt", "p02-cronologia.txt", "p02-novidades.txt", "p02-busca-indice.json", "sitemap.xml", "p02-changelog.txt", "p02-indice-temas.html"]}
rej = [f for f in ["p02-catalogo.json", "p02-indice-temas.txt", "sitemap.xml", "p02-busca-indice.json"] if "exemplo-rejeitado.html" in (dst / f).read_text()]
rej_log = "exemplo-rejeitado.html — sem aprovado_por" in (dst / "p02-changelog.txt").read_text()
shutil.rmtree(tmp)
caso("G_nova_publicacao_aprovada_atualiza_todos_os_indices", rr.returncode == 0 and all(onde.values()) and not rej and rej_log and not hash_ruins,
     f"item aprovado presente em: {onde}; item sem aprovação vazou para: {rej or 'nenhum'} (registrado como rejeitado={rej_log}); hashes do catálogo conferem: {not hash_ruins}")

print(json.dumps(res, ensure_ascii=False, indent=1))
sys.exit(0 if all(v["resultado"] == "PASSOU" for v in res.values()) else 1)
