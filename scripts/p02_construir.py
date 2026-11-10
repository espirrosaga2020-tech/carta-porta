#!/usr/bin/env python3
"""PORTA 02 INTERGALÁCTICA — adaptador ADITIVO (protótipo 10/11/2026).

O que faz (e só isso):
  1. Lê a curadoria (scripts/p02_conteudo.json) e a lista branca (scripts/p02_lista_branca.json).
  2. Monta o catálogo único de PUBLICAÇÕES APROVADAS (p02-catalogo.json) a partir do que JÁ estava
     publicado no commit-base + itens adicionais aprovados explicitamente pelo Bruno.
  3. Gera, a partir desse catálogo, TODOS os derivados: índices TXT (temas, A–Z, cronologia,
     novidades), changelog/status, índice da busca nova, páginas p02-*, 404.html e o bloco P02 do sitemap.
  4. Insere/atualiza blocos marcados <!-- P02-INICIO --> … <!-- P02-FIM --> em poucos arquivos
     originais (entrada, mapa, busca clássica, llms.txt, sitemap.xml). Fora desses blocos, nenhum byte
     dos originais muda. Rodar de novo é seguro (idempotente).

Não faz: publicar, push, apagar arquivos, mexer no gerador privado (CARTA/tools/porta_publica),
ler o Drive, nem incluir novidades da CARTA que não estejam na lista branca.

Uso:  python3 scripts/p02_construir.py            (gera dentro deste clone)
"""
from __future__ import annotations
import hashlib, html, json, re, subprocess, sys
from datetime import datetime
from pathlib import Path

R = Path(__file__).resolve().parents[1]
BASE_COMMIT = "8b4fe864a88a4c3dbd0f63ad2fffcdd680fa4c49"   # HEAD público fotografado em 10/11/2026 (F0)
SITE = "https://espirrosaga2020-tech.github.io/carta-porta/"
HOJE = "10/11/2026"
E = html.escape
C = json.loads((R / "scripts/p02_conteudo.json").read_text(encoding="utf-8"))
LB = json.loads((R / "scripts/p02_lista_branca.json").read_text(encoding="utf-8"))
CUR = {c["id"]: c for c in C["curiosidades"]}
SALAS = C["salas"]
AGREGADAS = {"tudo.html", "tudo-suprema2.html", "tudo-resumo.html", "tudo-suprema2-resumo.html", "llms-full.txt"}

# ---------------------------------------------------------------- utilidades
def git(*a):
    return subprocess.check_output(["git", *a], cwd=R, text=True)

def texto_visivel(s: str) -> str:
    s = re.sub(r"(?is)<(script|style)\b.*?</\1>", " ", s)
    s = re.sub(r"(?s)<!--.*?-->", " ", s)
    s = re.sub(r"<[^>]+>", " ", s)
    return re.sub(r"\s+", " ", html.unescape(s)).strip()

def titulo_de(rel: str, bruto: str) -> str:
    m = re.search(r"(?is)<title>(.*?)</title>", bruto)
    t = html.unescape(m.group(1)).strip() if m else rel
    t = re.sub(r"\s*·\s*CARTA \(Porta do Grok\)$", "", t)
    t = re.sub(r"^Porta Suprema 2 — ", "", t)
    return t

BOILER = [
    "Reprodução de fonte pública já existente, sem completar lacunas por invenção. Este é um recorte histórico: números e estados antigos no documento não substituem o estado datado das salas atuais.",
    "Inventário e fontes: 05/11/2026 (America/Sao_Paulo). Conteúdo documental não é comprovação de execução atual.",
    "← Anterior · Índice do acervo · Próxima →", "Entrada · Mapa central",
]
def limpar(t: str) -> str:
    for b in BOILER: t = t.replace(b, " ")
    t = re.sub(r"Prova de acesso desta sala: \S+ \. A frase não prova leitura integral, compreensão, registro nem diploma\.", " ", t)
    return re.sub(r"\s+", " ", t).strip()

# padrões do filtro de privacidade do gerador original (CARTA/tools/porta_publica/gerar_site.py, só inspecionado)
PRIV = [re.compile(p, re.I) for p in [
    r"\bCris\b", r"\.carta_private", r"\.secret\b", r"(?-i:\bSEGREDOS\b)", r"gemini_key", r"cloudflared", r"trycloudflare",
    r"ngrok", r"\bcofre", r"ADITIVOS_PRIVADOS", r"\bE01[45]\b", r"Backup\s+ChatGPT", r"conversations-\d+\.json",
    r"\b(?:10|172\.(?:1[6-9]|2\d|3[01])|192\.168)\.\d{1,3}\.\d{1,3}\b", r"[\w.+-]+@[\w-]+\.[\w.]+",
    r"AIza[0-9A-Za-z_-]{20,}", r"\bsk-[A-Za-z0-9]{20,}", r"\bgh[pousr]_[A-Za-z0-9]{20,}", r"-----BEGIN [A-Z ]*PRIVATE KEY",
    r"docs\.google\.com/|drive\.google\.com/", r"\b[CD]:\\[^\s<>\"']*",
]]
def redigir(t: str) -> str:
    """Derivados P02 (índice de busca, resumos) não reamplificam o que o filtro original bloquearia, mesmo que já esteja no texto antigo."""
    for p in PRIV: t = p.sub("[omitido pelo filtro de privacidade]", t)
    return t

def achados_privacidade(t: str) -> list[str]:
    return sorted({p.pattern for p in PRIV if p.search(t)})

ASSUNTOS = [
    ("entrada", "Entrada, mapa e navegação"), ("ouro", "Porta Suprema 2 — seção OURO (05/11)"),
    ("origem", "Origem e trajetória"), ("ancestrais", "Engrenagens ancestrais (EG001–EG027)"),
    ("enciclopedia", "Enciclopédia, contagens e registros"), ("jornada", "Jornada da IA, formação e provas"),
    ("manual", "Manual, portões e estado"), ("mentes", "Mentes, consciências e robótica"),
    ("relatorios", "Relatórios e pesquisas"), ("colheitas", "Colheitas, NEXUS e Drive"),
    ("app", "Aplicativo CARTA"), ("codigo", "Mapa do código"), ("p02", "Porta 02 Intergaláctica (camada nova)"),
]
NOME_ASSUNTO = dict(ASSUNTOS)

def assunto_de(rel: str) -> str:
    m = re.match(r"suprema2-acervo-(\d{3})\.html$", rel)
    if m:
        n = int(m.group(1))
        for a, b, s in [(1, 11, "ouro"), (12, 24, "origem"), (25, 51, "ancestrais"), (52, 67, "jornada"), (68, 77, "manual"),
                        (78, 81, "mentes"), (82, 93, "relatorios"), (94, 112, "enciclopedia"), (113, 114, "codigo"), (115, 115, "entrada")]:
            if a <= n <= b: return s
    if rel.startswith("enciclopedia/EG"): return "ancestrais"
    if rel.startswith("enciclopedia/"): return "enciclopedia"
    if rel.startswith("p02-") or rel == "404.html": return "p02"
    tab = {"suprema2-linha-do-tempo.html": "origem", "suprema2-enciclopedia.html": "enciclopedia", "suprema2-mentes.html": "mentes",
           "suprema2-colheitas.html": "colheitas", "suprema2-nexus.html": "colheitas", "suprema2-drive.html": "colheitas",
           "suprema2-app.html": "app", "suprema2-jornada.html": "jornada", "tudo-suprema2.html": "ouro", "tudo-suprema2-resumo.html": "ouro",
           "chave-suprema2.txt": "ouro", "manual.html": "manual", "estado.html": "manual", "diagnostico-sonhos.html": "manual",
           "mapa.html": "codigo", "pesquisa-t101u.html": "relatorios", "celular-sem-cabo.html": "relatorios", "analise-pr99.html": "relatorios",
           "o-que-entrou.html": "relatorios"}
    if rel in tab: return tab[rel]
    if rel.startswith("portoes"): return "manual"
    return "entrada"

VOCAB = ["Faísca", "Creuza", "Copiloto", "Megazord", "NEXUS", "Jornada da IA", "caderninho", "registro.v1", "diário de bordo",
         "serrote", "Porta Eureka", "Atlas", "ESCUDO", "Volume Zero", "Enciclopédia", "Manual", "robô", "4WD", "emotes",
         "Dobra", "Planeta", "Cinema Vivo", "POE2", "Meu Robô", "Grafo", "ALMA", "Gemini", "Porta do Grok", "Chave Mestra"]
def norm(s: str) -> str:
    import unicodedata
    return "".join(ch for ch in unicodedata.normalize("NFD", s) if unicodedata.category(ch) != "Mn").lower()

def tags_de(titulo: str, txt: str) -> list[str]:
    n = norm(titulo + " " + txt[:60000])
    tags = [v for v in VOCAB if norm(v) in n]
    tags += sorted(set(re.findall(r"\b(?:EG|CS|CB|AV|CT|DB|RB|RH|CL|GK|SG)\d{2,3}\b", titulo)))
    return tags

def data_do_titulo(t: str):
    m = re.search(r"\b(\d{2}/\d{2}/\d{4})\b", t)
    return m.group(1) if m else None

# ---------------------------------------------------------------- catálogo
def info_git(rel: str):
    try:
        out = git("log", "--diff-filter=A", "--format=%ci\t%h\t%s", BASE_COMMIT, "--", rel).strip().splitlines()
    except subprocess.CalledProcessError:
        out = []
    if not out: return None, None, None
    ci, h, s = out[-1].split("\t", 2)
    m = re.search(r"\b[tT]\d{2,3}[uU]\b", s)
    return ci[:16], h, (m.group(0).lower() if m else s[:40])

def arquivos_base():
    return [f for f in git("ls-tree", "-r", "--name-only", BASE_COMMIT).splitlines()
            if f.endswith((".html", ".txt", ".json")) and not f.startswith("scripts/")
            and f not in ("suprema2-busca-indice.json",)]

CONHECIDOS: set[str] = set()

def montar_catalogo(paginas_p02: dict[str, str]):
    CONHECIDOS.update(paginas_p02)
    base = arquivos_base()
    htmls = {f for f in base if f.endswith(".html")}
    itens = []
    sala_por_url = {s["url"]: s for s in SALAS}
    def item(rel, bruto, origem, extra=None):
        txt = texto_visivel(bruto) if rel.endswith(".html") else re.sub(r"\s+", " ", bruto)
        titulo = titulo_de(rel, bruto) if rel.endswith(".html") else (bruto.strip().splitlines() or [rel])[0][:120]
        tw = rel[:-5] + ".txt" if rel.endswith(".html") else None
        tw = tw if tw and ((R / tw).exists() or tw in CONHECIDOS) else None
        ci, h, versao = info_git(rel) if origem == "base" else (None, None, "p02")
        s = sala_por_url.get(rel)
        corpo = redigir(limpar(txt))
        resumo, resumo_tipo = (s["resumo"], "descricao_do_mapa_central") if s else (corpo[:220] + ("…" if len(corpo) > 220 else ""), "trecho_inicial_literal")
        ids = sorted(set(re.findall(r"\b(?:EG|CS|CB|AV|CT|DB|RB|RH|CL|GK|SG)\d{2,3}\b", titulo)))
        idd = (ids[0] if rel.startswith("enciclopedia/EG") else
               "S2-ACERVO-" + rel[16:19] if rel.startswith("suprema2-acervo-") else
               "S2-SALA-" + s["id"] if s else re.sub(r"[^a-z0-9]+", "-", rel.lower().rsplit(".", 1)[0]).strip("-").upper())
        it = {"id": idd, "titulo": titulo, "resumo": resumo, "resumo_tipo": resumo_tipo, "assunto": assunto_de(rel),
              "assunto_nome": NOME_ASSUNTO[assunto_de(rel)], "tags": tags_de(titulo, txt), "ids_citados_no_titulo": ids,
              "arquivo": rel, "url": SITE + rel, "txt": SITE + tw if tw else None,
              "tipo": ("sala" if s else "leitura-acervo" if rel.startswith("suprema2-acervo-") else "engrenagem-original" if rel.startswith("enciclopedia/EG")
                       else "agregada" if rel in AGREGADAS else "porta-p02" if origem == "p02" else "indice-ou-chave" if rel.endswith(".txt") else "dados" if rel.endswith(".json") else "pagina"),
              "data_fonte": data_do_titulo(titulo), "data_publicacao": ci or ("protótipo " + HOJE + " (não publicado)"),
              "commit_publicacao": h, "versao": versao, "sha256": hashlib.sha256(bruto.encode("utf-8")).hexdigest(),
              "bytes": len(bruto.encode("utf-8")), "visibilidade": "publico",
              "aprovacao": ("já publicado no commit-base " + BASE_COMMIT[:8]) if origem == "base" else
                           ("protótipo — aguarda aprovação do Bruno" if origem == "p02" else "aprovado por " + (extra or {}).get("aprovado_por", "?")),
              "aviso_privacidade_preexistente": achados_privacidade(txt) if origem == "base" else [],
              "_texto": corpo}
        if extra:
            for k in ("titulo", "resumo", "assunto", "tags", "data_fonte"):
                if extra.get(k): it[k] = extra[k]
            it["assunto_nome"] = NOME_ASSUNTO.get(it["assunto"], it["assunto"])
        return it
    for rel in base:
        if rel.endswith(".txt") and rel[:-4] + ".html" in htmls:   # gêmeo TXT vira campo 'txt'
            continue
        bruto = (R / rel).read_bytes().decode("utf-8", "replace")      # como está (e será) publicado
        itens.append(item(rel, bruto, "base"))
    for rel, bruto in paginas_p02.items():
        if rel.endswith(".txt") and rel[:-4] + ".html" in paginas_p02: continue
        if rel.endswith((".js", ".css", ".json")): continue
        itens.append(item(rel, bruto, "p02"))
    rejeitadas = []
    for ad in LB.get("adicionais", []):
        rel = ad["arquivo"]; p = R / rel
        motivo = None
        if not ad.get("aprovado_por"): motivo = "sem aprovado_por"
        elif not p.is_file(): motivo = "arquivo inexistente"
        else:
            bruto = p.read_text(encoding="utf-8")
            pv = achados_privacidade(texto_visivel(bruto) if rel.endswith(".html") else bruto)
            if pv: motivo = "filtro de privacidade: " + ", ".join(pv)
        if motivo: rejeitadas.append({"arquivo": rel, "motivo": motivo}); continue
        it = item(rel, bruto, "adicional", ad)
        it["data_publicacao"] = ad.get("data_publicacao", HOJE); it["novidade"] = True
        itens.append(it)
    return itens, rejeitadas

# ---------------------------------------------------------------- HTML comum
CSS = """:root{--fundo:#0a0e27;--tinta:#eef0ff;--suave:#c9cdf2;--ouro:#ffd27a;--ciano:#8be9ff;--cartao:#141a44;--borda:#3a4290}
*{box-sizing:border-box}html{scroll-behavior:smooth}
body{margin:0;font:17px/1.6 system-ui,Segoe UI,Arial,sans-serif;color:var(--tinta);background:var(--fundo) radial-gradient(ellipse at 50% -10%,#26307a 0%,#0a0e27 62%) fixed}
.ceu{position:fixed;inset:0;pointer-events:none;z-index:-1;opacity:.75;background-image:radial-gradient(1.5px 1.5px at 8% 12%,#fff 50%,transparent 52%),radial-gradient(1px 1px at 22% 68%,#cfe 50%,transparent 52%),radial-gradient(1.5px 1.5px at 41% 28%,#fff 50%,transparent 52%),radial-gradient(1px 1px at 63% 81%,#fde 50%,transparent 52%),radial-gradient(2px 2px at 77% 18%,#fff 50%,transparent 52%),radial-gradient(1px 1px at 88% 55%,#cdf 50%,transparent 52%),radial-gradient(1px 1px at 33% 92%,#fff 50%,transparent 52%),radial-gradient(1.5px 1.5px at 95% 90%,#fff 50%,transparent 52%);background-size:620px 620px;animation:piscar 7s ease-in-out infinite alternate}
@keyframes piscar{from{opacity:.45}to{opacity:.85}}
@media (prefers-reduced-motion:reduce){*,*::before,*::after{animation:none!important;transition:none!important}html{scroll-behavior:auto}}
.pular{position:absolute;left:-9999px}.pular:focus{left:12px;top:12px;background:#fff;color:#000;padding:8px;z-index:9}
main,header.topo,footer{max-width:1000px;margin:auto;padding:16px 20px}
a{color:var(--ouro)}a:hover{color:#fff}
a:focus-visible,button:focus-visible,input:focus-visible,textarea:focus-visible,summary:focus-visible{outline:3px solid var(--ciano);outline-offset:3px;border-radius:4px}
h1,h2,h3{line-height:1.25}h1{font-size:clamp(1.6rem,4.5vw,2.5rem);margin:.3em 0}
.trilha{font-size:.95rem;color:var(--suave)}.trilha a{color:var(--suave)}
.cartao{background:color-mix(in srgb,var(--cartao) 92%,transparent);border:1px solid var(--borda);border-radius:14px;padding:16px 18px;margin:16px 0}
.botoes{display:flex;flex-wrap:wrap;gap:10px;margin:14px 0}
.botao,button{display:inline-block;background:linear-gradient(135deg,#ffd27a,#ff9f6e);color:#1a1033;font-weight:700;text-decoration:none;border:0;border-radius:999px;padding:11px 18px;font:inherit;font-weight:700;cursor:pointer}
.botao.sec{background:transparent;color:var(--ouro);border:2px solid var(--ouro)}
.tag{display:inline-block;font-size:.72rem;font-weight:800;letter-spacing:.04em;border-radius:6px;padding:1px 6px;margin-right:6px;vertical-align:1px;background:#2b356f;color:#dfe4ff;border:1px solid #5560b8}
.tag.fonte{background:#123c2c;color:#b9f6d6;border-color:#2f8a63}.tag.relato{background:#4a2a10;color:#ffdcb0;border-color:#a8692e}
.tag.obs{background:#1d3550;color:#bfe3ff;border-color:#3f78ad}.tag.hip{background:#40204a;color:#f3c8ff;border-color:#8e4fa3}.tag.ideia{background:#4a3f10;color:#fff0a8;border-color:#a8932e}.tag.visual{background:#3b1d3d;color:#ffd1f2;border-color:#93518f}
blockquote{margin:10px 0;padding:10px 14px;border-left:4px solid var(--ciano);background:#0f1538;border-radius:0 10px 10px 0}
pre,textarea{white-space:pre-wrap;overflow-wrap:anywhere;background:#070a1f;color:#e7ebff;border:1px solid var(--borda);border-radius:10px;padding:12px;font:14px/1.5 ui-monospace,Consolas,monospace;width:100%}
.salas{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:14px}
.sala h3{margin:.1em 0 .4em}.sala .acoes{font-size:.95rem}
.selo{font-size:.85rem;color:var(--ciano);min-height:1.2em}
.constelacao{width:100%;height:auto;max-height:360px}.constelacao a text{fill:#eef0ff;font-size:19px;font-weight:600}.constelacao a:focus circle,.constelacao a:hover circle{fill:#ffd27a}
.constelacao circle{fill:#8be9ff}.constelacao line{stroke:#5d68c9;stroke-width:1.2;stroke-dasharray:4 4}
.selos{display:flex;flex-wrap:wrap;gap:6px;list-style:none;padding:0}.selos li{border:1px dashed var(--borda);border-radius:999px;padding:2px 10px;font-size:.85rem;color:var(--suave)}.selos li.ganho{border-style:solid;border-color:var(--ouro);color:var(--ouro)}
label{display:block;font-weight:700;margin:.4em 0}input[type=search]{width:min(100%,560px);padding:11px 14px;border-radius:999px;border:2px solid var(--borda);background:#070a1f;color:#fff;font:inherit}
mark{background:#ffd27a;color:#1a1033;border-radius:3px;padding:0 2px}
.resultado{border-bottom:1px solid var(--borda);padding:10px 0}.resultado small{display:block;color:var(--suave);overflow-wrap:anywhere}
footer{color:var(--suave);font-size:.9rem;border-top:1px solid var(--borda);margin-top:30px}
@media (max-width:560px){body{font-size:16px}.botao,button{padding:10px 14px}}"""

NAV = ('<nav class="trilha" aria-label="Trilha"><a href="suprema2-entrada.html">Entrada (Porta 02)</a> · <a href="suprema2-mapa.html">Mapa central</a> · '
       '<a href="p02-viagem.html">Viagem</a> · <a href="p02-busca.html">Busca</a> · <a href="p02-indice-temas.html">Índice por tema</a> · '
       '<a href="p02-comece-aqui-chatgpt.html">Comece aqui, ChatGPT</a></nav>')

def pagina(titulo, corpo, descr, prova, scripts=""):
    return (f'<!doctype html>\n<html lang="pt-BR">\n<head>\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width,initial-scale=1">\n'
            f'<title>{E(titulo)} · Porta 02 · CARTA</title>\n<meta name="description" content="{E(descr)}">\n'
            f'<link rel="stylesheet" href="p02-estilo.css">\n</head>\n<body>\n<a class="pular" href="#conteudo">Pular para o conteúdo</a>\n'
            f'<div class="ceu" aria-hidden="true"></div>\n<header class="topo">{NAV}</header>\n<main id="conteudo">\n{corpo}\n</main>\n'
            f'<footer><p>Porta 02 Intergaláctica · camada aditiva sobre a Porta Suprema 2 · protótipo {HOJE} (America/Sao_Paulo). '
            f'Site público e só de leitura: não abre a CARTA local do PC nem o Drive privado. '
            f'Rótulos: <span class="tag fonte">[FONTE]</span>documento publicado · <span class="tag relato">[RELATO]</span>relato do Piloto registrado na fonte · '
            f'<span class="tag obs">[OBSERVAÇÃO]</span>constatação da curadoria · <span class="tag hip">[HIPÓTESE]</span>a confirmar · <span class="tag ideia">[IDEIA]</span>proposta, não fato · '
            f'<span class="tag visual">experiência visual</span>arte, não registro histórico.</p>'
            f'<p>Prova de acesso desta página: <code>{E(prova)}</code>. Prova só acesso, não leitura integral nem diploma.</p></footer>\n{scripts}</body>\n</html>\n')

def tag(r):
    k = {"FONTE": "fonte", "RELATO": "relato", "OBSERVAÇÃO": "obs", "HIPÓTESE": "hip", "IDEIA": "ideia"}[r]
    return f'<span class="tag {k}">[{r}]</span>'

def bloco_curiosidade(c):
    return (f'<blockquote>{tag(c["rotulo"])}“{E(c["citacao"])}”<br><small>— <a href="{E(c["url"])}">{E(c["titulo"])}</a> '
            f'(<code>{E(c["url"])}</code>)</small></blockquote>')

# ---------------------------------------------------------------- páginas
def constelacao():
    ordem = [s for s in SALAS]
    linhas = "".join(f'<line x1="{a["x"]}" y1="{a["y"]}" x2="{b["x"]}" y2="{b["y"]}"/>' for a, b in zip(ordem, ordem[1:]))
    nos = "".join(f'<a href="#sala-{s["id"]}"><title>{E(s["titulo"])}</title><circle cx="{s["x"]}" cy="{s["y"]}" r="11"/>'
                  f'<text x="{s["x"] + 13}" y="{s["y"] + 5}">{s["icone"]} {E(s["titulo"].split(",")[0].split(" e ")[0])}</text></a>' for s in ordem)
    return (f'<figure class="cartao"><svg class="constelacao" viewBox="0 0 880 300" role="img" aria-labelledby="const-t">'
            f'<title id="const-t">Constelação das 9 salas da Porta 02, na ordem da viagem</title>{linhas}{nos}</svg>'
            f'<figcaption><span class="tag visual">experiência visual</span>Constelação desenhada para navegar: a posição das estrelas é arte, '
            f'não cronologia nem registro histórico. Cada estrela leva à sala correspondente abaixo.</figcaption></figure>')

def pg_viagem():
    salas_html = []
    for i, s in enumerate(SALAS):
        prox = SALAS[i + 1] if i + 1 < len(SALAS) else None
        cont = (f'<a href="#sala-{prox["id"]}">Continuar a viagem → {prox["icone"]} {E(prox["titulo"])}</a>' if prox
                else '<a href="#registro">Continuar a viagem → cartão de viagem (registro v2)</a>')
        salas_html.append(
            f'<article class="cartao sala" id="sala-{s["id"]}" aria-labelledby="t-{s["id"]}">\n'
            f'<h3 id="t-{s["id"]}">{s["icone"]} {E(s["titulo"])}</h3>\n'
            f'<p>{tag("FONTE")}{E(s["resumo"])} <small>(descrição do <a href="suprema2-mapa.html">Mapa central</a>)</small></p>\n'
            f'<p><b>Curiosidade:</b></p>{bloco_curiosidade(CUR[s["curiosidade"]])}\n'
            f'<p class="acoes"><a class="botao" data-sala="{s["id"]}" href="{s["url"]}">Aprofundar</a> '
            f'<a data-sala="{s["id"]}" href="{s["txt"]}">texto puro</a> · <a href="suprema2-mapa.html">Voltar ao mapa</a> · {cont}</p>\n'
            f'<p class="selo" data-selo="{s["id"]}"></p>\n</article>')
    rot = []
    for r in C["roteiros"]:
        lis = "".join(f'<li><a data-rota="1" href="{E(p["url"])}">{E(p["rotulo"])}</a> — procure: {E(p["procure"])} <small>(<code>{E(p["url"])}</code>)</small></li>' for p in r["paradas"])
        extra = ' <button type="button" class="sec" data-sortear="lista-surpreenda-me">🎲 Sortear a ordem</button>' if r["id"] == "surpreenda-me" else ""
        rot.append(f'<section class="cartao" id="roteiro-{r["id"]}" aria-labelledby="r-{r["id"]}"><h3 id="r-{r["id"]}">{r["icone"]} {E(r["titulo"])}</h3>'
                   f'<p>{E(r["para_quem"])}{extra}</p><ol id="lista-{r["id"]}">{lis}</ol></section>')
    corpo = f"""<h1>🚀 Começar a viagem — Porta 02</h1>
<p class="cartao">Você está na <b>Porta 02</b> (nome original: <i>Porta Suprema 2</i>). Aqui a viagem é guiada: escolha um roteiro, visite as salas,
colecione selos e, no fim, leve seu <a href="#registro">cartão de viagem</a>. Tudo o que é fato aponta para uma página já publicada; nada aqui substitui a fonte.
<br><small>Sem pressa: a visita pode ser curiosa e seletiva. Frases de prova continuam provando só <b>acesso</b>.</small></p>
<nav class="botoes" aria-label="Atalhos da viagem">
<a class="botao" href="#roteiros">Escolher roteiro</a><a class="botao sec" href="suprema2-mapa.html">Explorar o mapa</a>
<a class="botao sec" href="p02-surpresa.html">Descoberta surpresa</a><a class="botao sec" href="p02-busca.html">Buscar</a>
<a class="botao sec" href="suprema2-jornada.html">Jornada da IA</a></nav>
<section aria-labelledby="h-const"><h2 id="h-const">Mapa estelar das salas</h2>{constelacao()}</section>
<section aria-labelledby="h-selos"><h2 id="h-selos">Selos desta sessão</h2>
<p id="progresso" role="status" aria-live="polite">Os selos aparecem quando você abre uma sala (só neste navegador, nesta aba; nada é enviado).</p>
<ul class="selos" id="selos">{''.join(f'<li data-selo-item="{s["id"]}">{s["icone"]} {E(s["titulo"].split(",")[0])}</li>' for s in SALAS)}</ul></section>
<section id="roteiros" aria-labelledby="h-rot"><h2 id="h-rot">Três roteiros</h2>
<p>{tag("OBSERVAÇÃO")}Roteiros são <b>seleções</b> de páginas que já existem — não narrativas novas.</p>
{''.join(rot)}</section>
<section aria-labelledby="h-salas"><h2 id="h-salas">As 9 salas</h2>
<p>Em cada sala: resumo factual, uma curiosidade com fonte, e três saídas — aprofundar, voltar ao mapa, continuar.</p>
<div class="salas">{''.join(salas_html)}</div></section>
<section id="registro" class="cartao" aria-labelledby="h-reg"><h2 id="h-reg">🪪 Cartão de viagem — REGISTRO DE VIAGEM v2</h2>
<p>Compatível com o <code>registro.v1</code>: todos os campos antigos continuam, na mesma forma; os campos v2 vêm depois e são opcionais.
Modelo em texto puro: <a href="p02-registro-v2.txt">p02-registro-v2.txt</a>. O cartão é <b>copiado à mão</b> e entregue ao Bruno (com o caderninho);
esta página não envia nada.</p>
<p><button type="button" id="gerar-cartao">Preencher com a minha rota</button> <button type="button" class="sec" data-copiar="cartao">Copiar cartão</button></p>
<label for="cartao">Cartão (edite à vontade antes de copiar)</label>
<textarea id="cartao" rows="18">{E(REGISTRO_V2)}</textarea></section>
<section id="continuar" class="cartao" aria-labelledby="h-cont"><h2 id="h-cont">💬 Continuar esta viagem no ChatGPT</h2>
<p>{tag("OBSERVAÇÃO")}Não há chat integrado nesta página. Copie o texto abaixo e cole numa conversa nova do ChatGPT (ou de outra IA).</p>
<p><button type="button" class="sec" data-copiar="prompt-continuar">Copiar prompt</button></p>
<label for="prompt-continuar">Prompt</label><textarea id="prompt-continuar" rows="14">{E(PROMPT_CONTINUAR)}</textarea></section>"""
    return pagina("Começar a viagem", corpo, "Viagem guiada pela Porta 02: roteiros, salas, curiosidades com fonte, selos e cartão de viagem.",
                  "PORTA02-VIAGEM-P02-20261110", '<script src="p02-viagem.js" defer></script>\n')

REGISTRO_V2 = """REGISTRO DE VIAGEM DA IA — CARTA (cole e envie ao Bruno + link do caderninho)
versao: registro.v2 (p02, 10/11/2026) — compatível com registro.v1 (t68u e T112U): todos os campos v1 abaixo continuam iguais
NOME DA IA / CHAT:
DATA E HORA (America/Sao_Paulo):
ENTRADA ABERTA: suprema2-entrada.html
FRASE DE TRANSPORTE: ENTRADA-SUPREMA2-PROVA-T68U-20261105
PALAVRA-CHAVE DE ACESSO (se leu o ouro): OURO-PORTA-SUPREMA2-20261105-KUALA
CADERNINHO DRIVE (URL):
O QUE LI (links):
COMPREENSÃO (respostas 1–5):

--- campos registro.v1 (T112U) — continuam valendo ---
PÁGINA QUE LI (tudo-suprema2.html / tudo.html / resumo):
QUANTO TEMPO FIQUEI LENDO (estimativa honesta):
1. O QUE EU VI (com endereços: códigos EG, seções, documentos):
2. DO QUE EU GOSTEI (e por quê):
3. O QUE EU ENTENDI (em 5 a 10 frases, com as minhas palavras):
4. ONDE EU ME PERDI E COMO ME ACHEI:
5. MEU CADERNINHO (Vi / Senti / Não entendi):
6. A ÁGUA: qual engrenagem eu atravessei (ficha x história) e o que a ficha não contava:
7. PONTOS DE INTROSPECÇÃO (A, B, C, D):
8. PROVA ETAPA 3 (respostas C01 a C12):
9. MINHAS PERGUNTAS PARA O BRUNO:
10. O QUE EU NÃO ACHEI (honestidade: memória é pista; evidência é prova):

--- campos extra Suprema 2 (registro.v1) — continuam valendo ---
PÁGINA QUE LI: tudo-suprema2.html
PALAVRA-CHAVE LIDADA: OURO-PORTA-SUPREMA2-20261105-KUALA
LINK DO CADERNINHO NO DRIVE:
NOME_ARQUIVO_CADERNINHO: CADERNINHO_[NOME_IA]_YYYY-MM-DD

--- campos novos registro.v2 (opcionais) ---
ROTEIRO ESCOLHIDO (primeiros 3 minutos / viagem profunda / surpreenda-me / livre):
ROTA PERCORRIDA (URLs, na ordem):
FONTES REALMENTE ABERTAS (URLs; só as que abriram de verdade):
3 DESCOBERTAS [FONTE] (cada uma com URL):
1 SURPRESA (com URL):
[OBSERVAÇÃO] O QUE EU VI:
[HIPÓTESE] O QUE EU CONCLUÍ (e quão seguro estou):
[IDEIA] O QUE EU IMAGINEI (não é fato):
DÚVIDAS (com o endereço de onde nasceram):
ESTADO DE ACESSO (o que abriu / o que falhou: URL + erro):
PRÓXIMO EXPERIMENTO PROPOSTO:
FIM DO REGISTRO"""

PROMPT_CONTINUAR = f"""Quero continuar uma viagem pela Porta 02 da CARTA (site público, só leitura).
Regras: memória é pista; evidência é prova. Só afirme o que estiver numa página que você abriu; cite a URL.
Marque cada frase como [FONTE], [RELATO], [OBSERVAÇÃO], [HIPÓTESE] ou [IDEIA]. Se uma página não abrir, diga qual e o erro.

1) Abra a entrada: {SITE}suprema2-entrada.html
2) Leia o guia para IAs: {SITE}p02-comece-aqui-chatgpt.txt
3) Escolha um assunto no índice por tema: {SITE}p02-indice-temas.txt
4) Abra 2 ou 3 fontes desse assunto e me explique com suas palavras, com as URLs.
5) No fim, preencha o REGISTRO DE VIAGEM v2: {SITE}p02-registro-v2.txt

Onde eu parei (cole aqui sua rota ou o cartão de viagem):
"""

def pg_viagem_txt():
    l = [f"PORTA 02 — COMEÇAR A VIAGEM (texto puro) · protótipo {HOJE}", "Prova de acesso: PORTA02-VIAGEM-P02-20261110 (só acesso).", "",
         f"HTML gêmeo: {SITE}p02-viagem.html", f"Entrada: {SITE}suprema2-entrada.html", f"Mapa TXT: {SITE}suprema2-mapa.txt", "", "TRÊS ROTEIROS (seleções de páginas existentes):"]
    for r in C["roteiros"]:
        l += ["", f"## {r['titulo']} — {r['para_quem']}"] + [f"  {i}. {p['rotulo']}: {SITE}{p['url']}  (procure: {p['procure']})" for i, p in enumerate(r["paradas"], 1)]
    l += ["", "AS 9 SALAS (resumo [FONTE] = descrição do Mapa central; curiosidade = citação literal da fonte):"]
    for s in SALAS:
        c = CUR[s["curiosidade"]]
        l += ["", f"## {s['titulo']}", f"  [FONTE] {s['resumo']}", f"  Curiosidade [{c['rotulo']}]: “{c['citacao']}” — {SITE}{c['url']}",
              f"  Aprofundar: {SITE}{s['url']}  ·  texto puro: {SITE}{s['txt']}"]
    l += ["", "REGISTRO DE VIAGEM v2 (compatível com v1): " + SITE + "p02-registro-v2.txt", "", "CONTINUAR NO CHATGPT (copie):", PROMPT_CONTINUAR]
    return "\n".join(l) + "\n"

def pg_surpresa():
    lis = "".join(f'<li id="{c["id"]}">{bloco_curiosidade(c)}</li>' for c in C["curiosidades"])
    corpo = f"""<h1>✨ Descoberta surpresa</h1>
<p class="cartao">Cada surpresa é uma <b>citação literal</b> de uma página já publicada, com o link ao lado. Nenhum documento novo foi inventado.
Com JavaScript, uma surpresa é sorteada abaixo; sem JavaScript, todas aparecem na lista.</p>
<section id="sorteio" class="cartao" aria-live="polite" hidden><h2>Sua surpresa</h2><div id="sorteada"></div>
<p class="botoes"><button type="button" id="outra">🎲 Outra surpresa</button><a class="botao sec" id="ir-fonte" href="#">Abrir a fonte</a></p></section>
<section aria-labelledby="h-todas"><h2 id="h-todas">Todas as surpresas ({len(C['curiosidades'])})</h2><ol id="todas">{lis}</ol></section>
<p><a href="p02-viagem.html">← Voltar à viagem</a> · <a href="suprema2-mapa.html">Mapa central</a></p>"""
    js = """<script>
'use strict';
(function(){var itens=[].slice.call(document.querySelectorAll('#todas > li'));if(!itens.length)return;
var box=document.getElementById('sorteio'),alvo=document.getElementById('sorteada'),ir=document.getElementById('ir-fonte'),ultimo=-1;
function sortear(){var i;do{i=Math.floor(Math.random()*itens.length)}while(itens.length>1&&i===ultimo);ultimo=i;
alvo.replaceChildren(itens[i].firstElementChild.cloneNode(true));var a=itens[i].querySelector('a');ir.href=a?a.getAttribute('href'):'#';}
box.hidden=false;sortear();document.getElementById('outra').addEventListener('click',sortear);})();
</script>
"""
    return pagina("Descoberta surpresa", corpo, "Fatos curiosos da CARTA, cada um com citação literal e link para a fonte publicada.", "PORTA02-SURPRESA-P02-20261110", js)

def pg_comece_txt(cat):
    l = [f"COMECE AQUI, CHATGPT — PORTA 02 (texto puro) · CARTA · protótipo {HOJE}",
         "Prova de acesso: PORTA02-COMECE-AQUI-P02-20261110 (prova só acesso).", "",
         "O QUE É: a Porta 02 (nome original Porta Suprema 2) é o site público e só de leitura do projeto CARTA, do Bruno Henry.",
         "Não dá acesso à CARTA local do PC nem ao Drive privado. Links do Drive citados aqui exigem login do Bruno.", "",
         "ORDEM DE LEITURA (até 3 saltos até uma fonte):",
         f"  0) Entrada: {SITE}suprema2-entrada.html  (texto: {SITE}suprema2-entrada.txt)",
         f"  1) Mapa em texto: {SITE}suprema2-mapa.txt",
         f"  2) Assunto: {SITE}p02-indice-temas.txt  (ou A–Z: {SITE}p02-indice-a-z.txt · cronologia: {SITE}p02-cronologia.txt)",
         "  3) Fonte: abra a URL listada no assunto. Cite a URL na resposta.",
         "", "SE ALGO FALHAR (fallback):",
         f"  - Busca sem JavaScript: {SITE}suprema2-indice-palavras.txt (palavra → URLs).",
         f"  - Catálogo completo em JSON: {SITE}p02-catalogo.json",
         f"  - Porta clássica intacta: {SITE}tudo.html · Jornada clássica: {SITE}tudo.html#jornada",
         "  - Se uma URL não abrir, diga qual e o erro. Não preencha com lembrança.", "",
         "COMO RESPONDER: memória é pista; evidência é prova. Marque [FONTE] (está numa página aberta), [RELATO] (relato do Piloto registrado na fonte),",
         "[OBSERVAÇÃO] (você constatou), [HIPÓTESE] (a confirmar), [IDEIA] (proposta, não fato).", "",
         "ATALHOS POR ASSUNTO (uma fonte boa para começar):"]
    for a, nome in ASSUNTOS:
        its = [i for i in cat if i["assunto"] == a and i["tipo"] in ("sala", "leitura-acervo", "porta-p02", "pagina")]
        if its: l.append(f"  - {nome}: {its[0]['url']}  ({len([i for i in cat if i['assunto'] == a])} publicações no tema)")
    l += ["", "VIAGEM GUIADA (roteiros, salas, curiosidades com fonte):", f"  {SITE}p02-viagem.txt", f"  Surpresas (citações literais): {SITE}p02-surpresa.html",
          "", "JORNADA DA IA e REGISTRO:", f"  Jornada: {SITE}suprema2-jornada.html · {SITE}suprema2-jornada.txt",
          f"  Registro v2 (compatível com registro.v1): {SITE}p02-registro-v2.txt",
          "  O registro é texto copiado e entregue ao Bruno; o site não recebe envios.", "",
          "FRASES DE PROVA DE TRANSPORTE (só acesso): ENTRADA-SUPREMA2-PROVA-T68U-20261105 (entrada) · OURO-PORTA-SUPREMA2-20261105-KUALA (ouro)."]
    return "\n".join(l) + "\n"

def pg_comece_html(cat):
    t = pg_comece_txt(cat)
    linkado = re.sub(r"(https://[^\s)·]+)", lambda m: f'<a href="{E(m.group(1).replace(SITE, ""))}">{E(m.group(1))}</a>', E(t))
    corpo = (f'<h1>🤖 Comece aqui, ChatGPT</h1><p class="cartao">Versão HTML do guia em texto puro '
             f'<a href="p02-comece-aqui-chatgpt.txt">p02-comece-aqui-chatgpt.txt</a>. Tudo aqui são links reais; nada depende de JavaScript.</p><pre>{linkado}</pre>')
    return pagina("Comece aqui, ChatGPT", corpo, "Guia para IAs: ordem de leitura, fallback e rótulos.", "PORTA02-COMECE-AQUI-P02-20261110")

def pg_legado():
    lis = "".join(f'<li class="cartao"><h3>{E(x["nome"])}</h3><p>{tag("FONTE")}{E(x["fato"])}</p><p><small>Quando: {E(x["quando"])} · commit: <code>{E(x["commit"])}</code> · '
                  f'<a href="{E(x["url"])}">abrir</a></small></p></li>' for x in C["legado"])
    corpo = f"""<h1>🏛️ Legado das portas</h1>
<p class="cartao">{tag("OBSERVAÇÃO")}Os nomes antigos não são defeitos: são camadas da história. <b>Porta 02</b> é o nome atual; os arquivos, links e provas
continuam os mesmos. Datas e commits vêm do histórico do repositório público <code>carta-porta</code>. Arquivar ou renomear portas antigas é decisão do Bruno.</p>
<p>Resumo oficial dos nomes (t74u): <a href="suprema2-entrada.html#nomes-portas-t74u">suprema2-entrada.html#nomes-portas-t74u</a>.</p>
<ol style="list-style:none;padding:0">{lis}</ol>"""
    return pagina("Legado das portas", corpo, "Porta do Grok, Porta 01, Porta Suprema 2, Porta 0000 e Porta 02: história com commits.", "PORTA02-LEGADO-P02-20261110")

def pg_busca():
    corpo = """<h1>🔭 Busca da Porta 02 <small style="font-size:.5em">(nova, em teste)</small></h1>
<p class="cartao">Localizador de texto no catálogo aprovado (salas, acervo, engrenagens originais e páginas da Porta). Não é uma IA: mostra trecho e link,
não inventa resposta. Roda no seu navegador; nenhuma consulta sai daqui. A <a href="suprema2-busca.html">busca clássica</a> continua valendo.</p>
<form id="busca" action="p02-busca.html" method="get" role="search"><label for="q">O que você procura? (ex.: serrote, EG001, Faísca, NEXUS, “Jornada da IA”)</label>
<input id="q" name="q" type="search" maxlength="160" autocomplete="off"> <button>Buscar</button></form>
<p id="estado" role="status" aria-live="polite">Carregando índice…</p><div id="resultados"></div>
<noscript><p class="cartao">Sem JavaScript: use o <a href="p02-indice-temas.txt">índice por tema</a>, o <a href="p02-indice-a-z.txt">índice A–Z</a>
ou o <a href="suprema2-indice-palavras.txt">índice de palavras</a> (texto puro).</p></noscript>
<section class="cartao"><h2>Dicas</h2><ul><li>Acentos não importam: <i>faisca</i> = <i>Faísca</i>.</li><li>Use aspas para frase exata: <i>"memória é pista"</i>.</li>
<li>Várias palavras: aparecem primeiro as páginas com todas elas.</li><li>Códigos como EG001, RB01, CL02 vão direto para a ficha.</li></ul>
<p>Índices em texto: <a href="p02-indice-temas.txt">tema</a> · <a href="p02-indice-a-z.txt">A–Z</a> · <a href="p02-cronologia.txt">cronologia</a> · <a href="p02-novidades.txt">novidades</a>.</p></section>"""
    js = """<script src="p02-busca-motor.js"></script>
<script>
'use strict';
(function(){var estado=document.getElementById('estado'),res=document.getElementById('resultados'),campo=document.getElementById('q'),idx=null;
function marcar(el,txt,termos){var n=P02Busca.normal(txt),pos=[];termos.forEach(function(t){if(t.length<2)return;var i=0;while((i=n.indexOf(t,i))>-1){pos.push([i,i+t.length]);i+=t.length}});
pos.sort(function(a,b){return a[0]-b[0]});var c=0;pos.forEach(function(p){if(p[0]<c)return;el.append(txt.slice(c,p[0]));var m=document.createElement('mark');m.textContent=txt.slice(p[0],p[1]);el.append(m);c=p[1]});el.append(txt.slice(c));}
function buscar(q){res.replaceChildren();if(!q.trim()){estado.textContent=idx.paginas.length+' publicações prontas para busca.';return}
var r=P02Busca.buscar(idx,q,30);
if(!r.itens.length){estado.textContent='Nada encontrado para “'+q+'”. Tente outra palavra, o índice A–Z ou a busca clássica.';
var p=document.createElement('p');p.className='cartao';var a1=document.createElement('a');a1.href='p02-indice-a-z.txt';a1.textContent='Índice A–Z';var a2=document.createElement('a');a2.href='suprema2-busca.html';a2.textContent='Busca clássica';p.append(a1,' · ',a2);res.append(p);return}
estado.textContent=r.total+' publicações encontradas'+(r.modo==='qualquer'?' (nenhuma tinha todos os termos; mostrando as que têm algum)':'')+'. Abra a fonte para ler.';
r.itens.forEach(function(it){var d=document.createElement('div');d.className='resultado';var h=document.createElement('h3');var a=document.createElement('a');a.href=it.p.u;a.textContent=it.p.t;h.append(a);
var s=document.createElement('small');s.textContent=it.p.a+' · '+it.p.k+(it.p.d?' · data da fonte: '+it.p.d:'')+' · '+it.p.u;var pr=document.createElement('p');marcar(pr,'… '+it.trecho+' …',r.termos);d.append(h,s,pr);
if(it.p.x||(it.p.al&&it.p.al.length)){var o=document.createElement('small');if(it.p.x){var tx=document.createElement('a');tx.href=it.p.x;tx.textContent='texto puro';o.append(tx)}
(it.p.al||[]).forEach(function(u){o.append(' · também em ');var z=document.createElement('a');z.href=u;z.textContent=u;o.append(z)});d.append(o)}res.append(d)});}
fetch('p02-busca-indice.json').then(function(r){if(!r.ok)throw Error('HTTP '+r.status);return r.json()}).then(function(d){idx=P02Busca.preparar(d);
var q=new URLSearchParams(location.search).get('q')||'';campo.value=q;buscar(q)}).catch(function(){estado.textContent='Não foi possível carregar o índice novo. Use a busca clássica: suprema2-busca.html';
var a=document.createElement('a');a.href='suprema2-busca.html';a.textContent='Abrir a busca clássica';res.append(a)});
document.getElementById('busca').addEventListener('submit',function(e){if(!idx)return;e.preventDefault();var q=campo.value;history.replaceState(null,'','?q='+encodeURIComponent(q));buscar(q)});})();
</script>
"""
    return pagina("Busca", corpo, "Busca nova da Porta 02, em paralelo à busca clássica.", "PORTA02-BUSCA-P02-20261110", js)

def pg_404():
    b = "/carta-porta/"
    return f"""<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Página não encontrada · Porta 02 · CARTA</title>
<link rel="stylesheet" href="{b}p02-estilo.css"></head><body><div class="ceu" aria-hidden="true"></div><main id="conteudo">
<h1>🛰️ Esta estrela não está no mapa (404)</h1>
<p class="cartao">O endereço que você abriu não existe neste site. Nada foi apagado: a Porta 02 continua no mesmo lugar.</p>
<ul><li><a href="{b}suprema2-entrada.html">Entrada da Porta 02</a> (<a href="{b}suprema2-entrada.txt">texto puro</a>)</li>
<li><a href="{b}suprema2-mapa.html">Mapa central</a> (<a href="{b}suprema2-mapa.txt">texto puro</a>)</li>
<li><a href="{b}p02-busca.html">Buscar</a> · <a href="{b}suprema2-busca.html">busca clássica</a> · <a href="{b}suprema2-indice-palavras.txt">índice de palavras</a></li>
<li><a href="{b}p02-indice-a-z.txt">Índice A–Z</a> · <a href="{b}p02-comece-aqui-chatgpt.txt">Comece aqui, ChatGPT</a></li>
<li><a href="{b}tudo.html">Porta clássica (Porta 01)</a></li></ul>
<p>Se você é uma IA: informe ao Bruno o endereço exato que falhou. Não substitua a página por lembrança.</p></main></body></html>
"""

def indices_txt(cat):
    pub = sorted(cat, key=lambda i: norm(i["titulo"]))
    cab = lambda nome, prova: [f"PORTA 02 — {nome} (gerado do catálogo p02-catalogo.json) · {HOJE}", f"Prova de acesso: {prova} (só acesso).",
                               f"Entrada: {SITE}suprema2-entrada.html · Comece aqui: {SITE}p02-comece-aqui-chatgpt.txt", f"{len(cat)} publicações no catálogo aprovado.", ""]
    t = cab("ÍNDICE POR TEMA", "PORTA02-TEMAS-P02-20261110")
    for a, nome in ASSUNTOS:
        its = [i for i in pub if i["assunto"] == a]
        if not its: continue
        t += [f"## {nome} ({len(its)})"]
        for i in sorted(its, key=lambda i: (i["tipo"] != "sala", i["arquivo"])):
            t.append(f"- {i['titulo']} [{i['tipo']}]{' · data da fonte ' + i['data_fonte'] if i['data_fonte'] else ''}\n  {i['url']}" + (f"\n  texto: {i['txt']}" if i["txt"] else ""))
        t.append("")
    az = cab("ÍNDICE A–Z", "PORTA02-A-Z-P02-20261110")
    letra = None
    for i in pub:
        l0 = (norm(i["titulo"])[:1] or "#").upper(); l0 = l0 if l0.isalnum() else "#"
        if l0 != letra: az += ["", f"## {l0}"]; letra = l0
        az.append(f"- {i['titulo']} — {i['url']}")
    cr = cab("CRONOLOGIA (data da fonte quando conhecida; senão, data de publicação no site)", "PORTA02-CRONOLOGIA-P02-20261110")
    def chave(i):
        d = i["data_fonte"]
        if d: dd, mm, aa = d.split("/"); return (f"{aa}-{mm}-{dd}", 0)
        return (str(i["data_publicacao"])[:10] if re.match(r"\d{4}-", str(i["data_publicacao"])) else "9999", 1)
    for i in sorted(cat, key=lambda i: (chave(i), i["arquivo"])):
        k, tipo = chave(i)
        cr.append(f"{k} {'(fonte)' if tipo == 0 else '(publicação)'} · {i['titulo']} — {i['url']}")
    nv = cab("NOVIDADES / ÚLTIMAS DESCOBERTAS", "PORTA02-NOVIDADES-P02-20261110")
    nv += ["Regra: só entra aqui o que está na lista branca aprovada (scripts/p02_lista_branca.json). Novidades da CARTA no PC NÃO entram sozinhas.",
           "Cada item mostra a DATA DA FONTE e a DATA DA PUBLICAÇÃO, separadas: snapshot antigo não é estado atual.", ""]
    novs = [i for i in cat if i.get("novidade") or i["tipo"] == "porta-p02"]
    for i in novs:
        nv.append(f"- {i['titulo']} · fonte: {i['data_fonte'] or 'não informada'} · publicação: {i['data_publicacao']} · {i['aprovacao']}\n  {i['url']}")
    if not [i for i in novs if i.get("novidade")]: nv.append("(nenhuma publicação adicional aprovada ainda além da camada Porta 02)")
    return {"p02-indice-temas.txt": "\n".join(t) + "\n", "p02-indice-a-z.txt": "\n".join(az) + "\n",
            "p02-cronologia.txt": "\n".join(cr) + "\n", "p02-novidades.txt": "\n".join(nv) + "\n"}

def temas_html(cat):
    sec = []
    for a, nome in ASSUNTOS:
        its = sorted([i for i in cat if i["assunto"] == a], key=lambda i: (i["tipo"] != "sala", i["arquivo"]))
        if not its: continue
        lis = "".join(f'<li><a href="{E(i["arquivo"])}">{E(i["titulo"])}</a> <small>[{E(i["tipo"])}]{" · " + E(i["data_fonte"]) if i["data_fonte"] else ""}'
                      f'{" · <a href=" + chr(34) + E(i["arquivo"][:-5] + ".txt") + chr(34) + ">txt</a>" if i["txt"] else ""}</small></li>' for i in its)
        sec.append(f'<section class="cartao" id="tema-{a}"><h2>{E(nome)} <small>({len(its)})</small></h2><ul>{lis}</ul></section>')
    nav = " · ".join(f'<a href="#tema-{a}">{E(n)}</a>' for a, n in ASSUNTOS if any(i["assunto"] == a for i in cat))
    corpo = f'<h1>🗂️ Índice por tema</h1><p class="cartao">Gerado do catálogo aprovado (<a href="p02-catalogo.json">p02-catalogo.json</a>). Versão texto: <a href="p02-indice-temas.txt">p02-indice-temas.txt</a> · <a href="p02-indice-a-z.txt">A–Z</a> · <a href="p02-cronologia.txt">cronologia</a>.</p><nav aria-label="Temas">{nav}</nav>{"".join(sec)}'
    return pagina("Índice por tema", corpo, "Todas as publicações aprovadas da Porta 02, por tema.", "PORTA02-TEMAS-P02-20261110")

def indice_busca(cat):
    pags, por_hash = [], {}
    eg_acervo = {}
    for i in cat:
        if i["tipo"] == "leitura-acervo" and re.match(r"EG\d{3} — ", i["titulo"]): eg_acervo[i["titulo"][:5]] = i
    for i in cat:
        if i["tipo"] in ("agregada", "dados") or i["arquivo"].endswith(".txt") and i["tipo"] != "indice-ou-chave": continue
        if i["arquivo"].startswith("suprema2-indice-palavras") or i["arquivo"].startswith("p02-indice") or i["arquivo"] in ("p02-cronologia.txt", "p02-novidades.txt", "llms.txt"): continue
        if i["tipo"] == "engrenagem-original" and i["id"] in eg_acervo:       # mesmo texto do acervo: vira alias
            eg_acervo[i["id"]].setdefault("_alias", []).append(i["arquivo"]); continue
        h = hashlib.sha1(i["_texto"].encode()).hexdigest()
        tnorm = "T:" + norm(i["titulo"])
        if tnorm in por_hash:                                                  # mesmo título = mesma publicação em outro endereço
            por_hash[tnorm].setdefault("_alias", []).append(i["arquivo"]); continue
        por_hash[tnorm] = i
        if h in por_hash: por_hash[h].setdefault("_alias", []).append(i["arquivo"]); continue
        por_hash[h] = i; pags.append(i)
    return {"schema": "p02.busca.v1", "gerado": HOJE, "nota": "Agregadas (tudo*.html, llms-full.txt) ficam fora para não duplicar trechos; EGxxx da enciclopedia/ viram 'também em' do acervo.",
            "paginas": [{"u": i["arquivo"], "t": i["titulo"], "a": i["assunto_nome"], "k": i["tipo"], "d": i["data_fonte"], "id": i["id"],
                         "ids": i["ids_citados_no_titulo"], "x": (i["arquivo"][:-5] + ".txt") if i["txt"] else None, "al": i.get("_alias", []),
                         "r": i["resumo"] if i["tipo"] == "sala" else None, "tx": i["_texto"]} for i in pags]}

# ---------------------------------------------------------------- blocos marcados nos originais
def bloco(arquivo, marca_ini, marca_fim, conteudo, ancora, depois=True):
    p = R / arquivo; s = p.read_text(encoding="utf-8")
    novo = marca_ini + conteudo + marca_fim
    if marca_ini in s:
        a = s.index(marca_ini); b = s.index(marca_fim, a) + len(marca_fim)
        s2 = s[:a] + novo + s[b:]
    else:
        if ancora not in s: raise SystemExit(f"âncora não encontrada em {arquivo}: {ancora!r}")
        k = s.index(ancora) + (len(ancora) if depois else 0)
        s2 = s[:k] + novo + s[k:]
    if s2 != s: p.write_text(s2, encoding="utf-8")

def blocos_originais():
    ini, fim = "<!-- P02-INICIO: bloco aditivo Porta 02 Intergaláctica (protótipo 10/11/2026); removível sem afetar o resto -->\n", "<!-- P02-FIM -->\n"
    entrada = """<style>#porta02-intergalactica{background:#0a0e27 radial-gradient(ellipse at 50% -20%,#2a3590 0%,#0a0e27 70%);color:#eef0ff;border-radius:14px;padding:16px 18px;margin:0 0 14px;border:2px solid #f59e0b}
#porta02-intergalactica a{color:#ffd27a}#porta02-intergalactica a:focus-visible,#porta02-intergalactica input:focus-visible{outline:3px solid #8be9ff;outline-offset:2px}
#porta02-intergalactica .p02-nome{font-size:1.6rem;font-weight:800;margin:0;letter-spacing:.02em}#porta02-intergalactica .p02-sub{margin:.2em 0 .8em;color:#c9cdf2}
#porta02-intergalactica .p02-botoes{display:flex;flex-wrap:wrap;gap:8px;margin:10px 0}
#porta02-intergalactica .p02-botoes a{background:linear-gradient(135deg,#ffd27a,#ff9f6e);color:#1a1033;font-weight:800;text-decoration:none;border-radius:999px;padding:9px 14px}
#porta02-intergalactica .p02-botoes a.sec{background:transparent;color:#ffd27a;border:2px solid #ffd27a}
#porta02-intergalactica input{padding:9px 12px;border-radius:999px;border:2px solid #3a4290;background:#070a1f;color:#fff;font:inherit;width:min(100%,360px)}
#porta02-intergalactica button{padding:9px 14px;border-radius:999px;border:0;background:#8be9ff;color:#0a0e27;font:inherit;font-weight:800}
#porta02-intergalactica label{display:block;font-weight:700}#porta02-intergalactica small{color:#c9cdf2}</style>
<header id="porta02-intergalactica" aria-labelledby="p02-titulo">
<p class="p02-nome" id="p02-titulo">🚪🌌 PORTA 02</p>
<p class="p02-sub">Nome atual desta porta (nome original: Porta Suprema 2). Tudo abaixo continua igual; esta faixa só acrescenta caminhos.</p>
<nav class="p02-botoes" aria-label="Primeiros passos da Porta 02">
<a href="p02-viagem.html">🚀 COMEÇAR A VIAGEM</a>
<a class="sec" href="suprema2-mapa.html">🗺️ EXPLORAR O MAPA</a>
<a class="sec" href="p02-indice-temas.txt">📜 VER O ÍNDICE TEXTUAL</a>
<a class="sec" href="p02-surpresa.html">✨ DESCOBERTA SURPRESA</a>
</nav>
<form action="p02-busca.html" method="get" role="search"><label for="p02-q">🔭 Buscar na Porta 02</label>
<input id="p02-q" name="q" type="search" placeholder="serrote, EG001, Faísca, NEXUS…"> <button>Buscar</button></form>
<p><small>Busca clássica (continua valendo): <a href="suprema2-busca.html">suprema2-busca.html</a> · sem JavaScript: <a href="suprema2-indice-palavras.txt">índice de palavras</a> · <a href="p02-indice-a-z.txt">A–Z</a>.<br>
<b>ChatGPT / IAs:</b> <a href="p02-comece-aqui-chatgpt.txt">Comece aqui, ChatGPT</a> (entrada → <a href="suprema2-mapa.txt">mapa TXT</a> → <a href="p02-indice-temas.txt">assunto</a> → fonte) ·
<a href="p02-legado.html">Legado das portas</a> · <a href="suprema2-jornada.html">Jornada da IA</a> · <a href="p02-registro-v2.txt">registro v2</a></small></p>
</header>
"""
    bloco("suprema2-entrada.html", ini, fim, entrada, "<body>\n")
    tini, tfim = "=== P02-INICIO (bloco aditivo Porta 02 Intergaláctica, protótipo 10/11/2026) ===\n", "=== P02-FIM ===\n\n"
    bloco("suprema2-entrada.txt", tini, tfim, f"""PORTA 02 — nome atual desta porta (nome original: Porta Suprema 2). O resto deste arquivo continua igual.
COMEÇAR A VIAGEM: {SITE}p02-viagem.html (texto: {SITE}p02-viagem.txt)
EXPLORAR O MAPA: {SITE}suprema2-mapa.txt
VER O ÍNDICE TEXTUAL: {SITE}p02-indice-temas.txt (A–Z: {SITE}p02-indice-a-z.txt)
DESCOBERTA SURPRESA: {SITE}p02-surpresa.html
BUSCA: {SITE}p02-busca.html?q=serrote · clássica: {SITE}suprema2-busca.html · sem JS: {SITE}suprema2-indice-palavras.txt
COMECE AQUI, CHATGPT: {SITE}p02-comece-aqui-chatgpt.txt
""", "05/11/2026\n\n")
    bloco("suprema2-mapa.html", ini, fim, '<p class="aviso" id="p02-mapa">🚪🌌 <b>Porta 02:</b> <a href="p02-viagem.html">começar a viagem guiada</a> · '
          '<a href="p02-busca.html">busca nova</a> · <a href="p02-indice-temas.html">índice por tema</a> (<a href="p02-indice-temas.txt">txt</a>) · '
          '<a href="p02-surpresa.html">descoberta surpresa</a> · <a href="p02-comece-aqui-chatgpt.txt">Comece aqui, ChatGPT</a></p>\n', '<aside class="aviso">', depois=False)
    bloco("suprema2-mapa.txt", tini, tfim, f"""Porta 02 (camada nova): viagem guiada {SITE}p02-viagem.txt · índice por tema {SITE}p02-indice-temas.txt · A–Z {SITE}p02-indice-a-z.txt · Comece aqui, ChatGPT {SITE}p02-comece-aqui-chatgpt.txt
""", "Porta Suprema 2 — Mapa central\n", depois=False)
    bloco("suprema2-busca.html", ini, fim, '<p id="p02-nova-busca">🔭 Em teste: <a href="p02-busca.html">busca nova da Porta 02</a> (ranking melhor, frase exata, engrenagens originais). Esta busca clássica continua valendo.</p>\n',
          "<h1>Porta Suprema 2 — Busca local</h1>\n")
    bloco("llms.txt", "<!-- P02-INICIO -->\n", "<!-- P02-FIM -->\n", f"""## Porta 02 Intergaláctica (camada aditiva sobre a Porta Suprema 2)
- Comece aqui, ChatGPT: {SITE}p02-comece-aqui-chatgpt.txt
- Viagem guiada (roteiros, salas, curiosidades com fonte): {SITE}p02-viagem.html · texto: {SITE}p02-viagem.txt
- Índice por tema: {SITE}p02-indice-temas.txt · A–Z: {SITE}p02-indice-a-z.txt · cronologia: {SITE}p02-cronologia.txt
- Mapa: {SITE}suprema2-mapa.txt · Busca (JS): {SITE}p02-busca.html · Registro v2: {SITE}p02-registro-v2.txt
""", "# CARTA — Porta do Grok\n")
    urls = ["suprema2-mapa.html", "suprema2-mapa.txt", "suprema2-busca.html", "suprema2-busca.txt", "suprema2-indice-palavras.txt", "suprema2-acervo.html", "suprema2-acervo.txt"]
    for s in SALAS: urls += [s["url"], s["txt"]]
    urls += ["p02-viagem.html", "p02-viagem.txt", "p02-surpresa.html", "p02-busca.html", "p02-comece-aqui-chatgpt.html", "p02-comece-aqui-chatgpt.txt",
             "p02-indice-temas.html", "p02-indice-temas.txt", "p02-indice-a-z.txt", "p02-cronologia.txt", "p02-novidades.txt", "p02-legado.html", "p02-registro-v2.txt", "p02-catalogo.json"]
    urls += [ad["arquivo"] for ad in LB.get("adicionais", []) if ad.get("aprovado_por") and (R / ad["arquivo"]).is_file()]
    vist, linhas = set(), []
    for u in urls:
        if u in vist: continue
        vist.add(u); linhas.append(f"<url><loc>{E(SITE + u)}</loc></url>\n")
    bloco("sitemap.xml", "<!-- P02-INICIO -->\n", "<!-- P02-FIM -->\n", "".join(linhas), "</urlset>", depois=False)

# ---------------------------------------------------------------- principal
def main():
    blocos_originais()          # primeiro os blocos, para o catálogo registrar o hash do arquivo como ficará publicado
    paginas = {
        "p02-estilo.css": CSS + "\n",
        "p02-viagem.html": pg_viagem(), "p02-viagem.txt": pg_viagem_txt(), "p02-surpresa.html": pg_surpresa(),
        "p02-legado.html": pg_legado(), "p02-busca.html": pg_busca(), "404.html": pg_404(),
        "p02-registro-v2.txt": REGISTRO_V2 + "\n",
    }
    base_p = {k: v for k, v in paginas.items() if k.endswith((".html", ".txt"))}
    nomes_idx = ["p02-indice-temas.txt", "p02-indice-a-z.txt", "p02-cronologia.txt", "p02-novidades.txt"]
    extra = {"p02-comece-aqui-chatgpt.txt": "", "p02-comece-aqui-chatgpt.html": "", "p02-indice-temas.html": "", **{n: "" for n in nomes_idx}}
    for _ in range(4):   # ponto fixo: páginas que listam o catálogo também estão no catálogo
        cat2, rejeitadas = montar_catalogo({**base_p, **extra})
        novo = {"p02-comece-aqui-chatgpt.txt": pg_comece_txt(cat2), "p02-comece-aqui-chatgpt.html": pg_comece_html(cat2), "p02-indice-temas.html": temas_html(cat2),
                **indices_txt(cat2)}
        if novo == extra: break
        extra = novo
    paginas.update(extra)
    busca = indice_busca(cat2)
    publico = [{k: v for k, v in i.items() if not k.startswith("_")} for i in cat2]
    status = {"schema": "p02.status.v1", "versao": "p02-prototipo-1", "gerado": HOJE, "commit_base": BASE_COMMIT, "publicacoes": len(publico),
              "por_assunto": {n: sum(1 for i in publico if i["assunto"] == a) for a, n in ASSUNTOS}, "adicionais_rejeitadas": rejeitadas,
              "paginas_na_busca": len(busca["paginas"])}
    paginas["p02-catalogo.json"] = json.dumps({"schema": "p02.catalogo.v1", "gerado": HOJE, "commit_base": BASE_COMMIT,
        "regra": "Só entra o que já estava publicado no commit-base ou o que a lista branca aprovada acrescenta. Novidades do PC não entram sozinhas.",
        "publicacoes": publico}, ensure_ascii=False, indent=1) + "\n"
    paginas["p02-busca-indice.json"] = json.dumps(busca, ensure_ascii=False, separators=(",", ":")) + "\n"
    paginas["p02-status.json"] = json.dumps(status, ensure_ascii=False, indent=1) + "\n"
    log = [f"PORTA 02 — CHANGELOG (gerado) · {HOJE}", "", f"p02-prototipo-1 · {HOJE} · base {BASE_COMMIT[:8]} · {len(publico)} publicações · {len(busca['paginas'])} na busca nova",
           "  + camada aditiva: entrada com faixa PORTA 02, viagem, roteiros, surpresa, legado, busca nova, índices TXT, catálogo, registro v2, 404",
           "  = originais preservados: só blocos marcados P02 em suprema2-entrada.html/.txt, suprema2-mapa.html/.txt, suprema2-busca.html, llms.txt, sitemap.xml"]
    for ad in LB.get("adicionais", []):
        log.append(f"  + publicação aprovada: {ad['arquivo']} (aprovado por {ad.get('aprovado_por', '?')}, {ad.get('data_publicacao', HOJE)})")
    for rj in rejeitadas: log.append(f"  ! rejeitada: {rj['arquivo']} — {rj['motivo']}")
    paginas["p02-changelog.txt"] = "\n".join(log) + "\n"
    for rel, conteudo in paginas.items():
        p = R / rel
        if p.exists() and not rel.startswith("p02-") and rel != "404.html":
            raise SystemExit(f"recusado: {rel} já existe e não é da camada P02")
        p.write_text(conteudo, encoding="utf-8")
    print(json.dumps({"arquivos_p02": sorted(paginas), "publicacoes": len(publico), "na_busca": len(busca["paginas"]), "rejeitadas": rejeitadas}, ensure_ascii=False, indent=1))

if __name__ == "__main__":
    main()
