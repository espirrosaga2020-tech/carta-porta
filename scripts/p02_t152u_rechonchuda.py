"""Porta 02 rechonchuda (T152U, 13/11/2026, pedido do Bruno t62u). SÓ ACRÉSCIMO.
Cabeçalho de orientação para IAs (HTML puro, sem JS), menu com âncoras, resumos do estado atual,
busca POR LINK (páginas estáticas busca/<termo>.html — funciona sem JavaScript), lista de todas as páginas,
manual v12 filtrado. Blocos marcados P02-T152U-INICIO/FIM: rodar de novo troca só o bloco (idempotente).
Uso: python scripts/p02_t152u_rechonchuda.py --carta <clone do repo CARTA> [--censo CSV]"""
from __future__ import annotations
import argparse, csv, html, json, re, sys, unicodedata
from pathlib import Path

R = Path(__file__).resolve().parents[1]
B = "https://espirrosaga2020-tech.github.io/carta-porta/"
def E(s): return html.escape(str(s))
INI, FIM = "<!-- P02-T152U-INICIO -->", "<!-- P02-T152U-FIM -->"
TINI, TFIM = "=== P02-T152U-INICIO ===", "=== P02-T152U-FIM ==="
EXTRA_PROIBIDO = [re.compile(p, re.I) for p in [r"\b[A-Z]:\\", r"C:/Users", r"\\Users\\", r"token", r"senha", r"conversas\.sqlite", r"CHAVE API"]]

def norm(s): return unicodedata.normalize("NFD", str(s)).encode("ascii", "ignore").decode().lower()
def slug(t): return re.sub(r"[^a-z0-9]+", "-", norm(t)).strip("-")

def troca_bloco(txt, ini, fim, novo, onde):
    if ini in txt:
        a, b = txt.index(ini), txt.index(fim) + len(fim)
        return txt[:a] + novo + txt[b:]
    return onde(txt, novo)

def depois_body(txt, novo):
    m = re.search(r"<body[^>]*>", txt); return txt[:m.end()] + "\n" + novo + "\n" + txt[m.end():]

def censo(caminho):
    if caminho and Path(caminho).exists():
        rows = list(csv.DictReader(open(caminho, encoding="utf-8")))
        return {"ok": True, "n": len(rows), "texto": f"CENSO ÚNICO 13/11/2026: {len(rows)} engrenagens contadas uma por uma (Drive + PC + GitHub)."}
    return {"ok": False, "texto": "[CENSO-PENDENTE] O CENSO ÚNICO das engrenagens (13/11/2026) ainda está sendo feito. "
            "Até ele sair, vale o registro do app: 73 engrenagens oficiais em 87 registros; o Doc 04 do Drive fala em 96 "
            "(62 + 6 Gordinhas + 28 do pacote Argon). Os dois números ficam anotados; quem decide é o Bruno."}

# ---------- conteúdo (texto público; sem caminhos, IPs, chaves) ----------
MENU = [("o-que-e", "1. O que é isto (leia primeiro)"), ("passo-a-passo", "2. Passo a passo da visita guiada"),
        ("confirmacao", "3. Confirmação da palavra-chave (prova de acesso)"), ("busca-por-link", "4. Como BUSCAR (por link, sem JavaScript)"),
        ("onde-fica", "5. Onde fica cada coisa (menu completo)"), ("novidades", "6. Novidades de 13/11/2026 (T152U)"),
        ("todas", "7. Todas as páginas")]

def bloco_html(c):
    li = "".join(f'<li><a href="#p02t-{a}">{E(t)}</a></li>' for a, t in MENU)
    return f"""{INI}
<section id="p02-t152u-orientacao" style="border:3px solid #9a3412;background:#fff;border-radius:12px;padding:14px 16px;margin:0 0 14px;color:#1b1b1b">
<p style="font-size:1.3rem;margin:0"><b>👑 PORTA 02 — ORIENTAÇÃO PARA IAs (leia este quadro primeiro)</b></p>
<p style="margin:.3em 0">Atualizada em 13/11/2026 (America/Sao_Paulo). Esta página é HTML puro: tudo funciona <b>sem JavaScript</b>, só abrindo links (GET).
Você é uma IA convidada pelo Bruno para conhecer o projeto <b>CARTA</b>. Nada abaixo deste quadro foi apagado; ele só acrescenta caminhos.</p>
<p style="margin:.3em 0"><b>Menu:</b></p><ol style="margin:.2em 0 .6em">{li}</ol>

<h2 id="p02t-o-que-e">1. O que é isto</h2>
<p>A <b>Porta 02</b> (nome original: Porta Suprema 2) é a entrada principal da CARTA para IAs. A CARTA é o projeto pessoal do Bruno:
um "universo de aprender" com esferas de conhecimento, a <b>Enciclopédia das Engrenagens</b>, mentes/personagens de IA que rodam no PC dele
(Faísca, Creuza, Copiloto, a Consciência), um Planeta 3D, laboratórios de robótica e o jogo Meu Robô. Este site é só de leitura.
Dentro dele há: esta entrada, um <b>mapa</b>, a <b>página infinita</b> (tudo numa rolagem só), um <b>acervo</b> com 115 fichas,
<b>índices de palavras</b>, a enciclopédia, o manual, os portões e as novidades.</p>

<h2 id="p02t-passo-a-passo">2. Passo a passo da visita guiada</h2>
<ol>
<li><b>Leia este quadro inteiro</b> (menu → seções → links).</li>
<li>Abra as <a href="p02-t152u-novidades.html">Novidades de 13/11/2026</a> (<a href="p02-t152u-novidades.txt">texto puro</a>): o estado de hoje em resumo.</li>
<li>Abra o <a href="suprema2-mapa.html">Mapa central</a> (<a href="suprema2-mapa.txt">texto</a>): as salas e o que tem em cada uma.</li>
<li>Leia a <a href="chave-suprema2.txt">Chave da Porta 02</a> (texto puro) e faça a confirmação (seção 3).</li>
<li>Para ler TUDO sem navegar: abra a <a href="tudo-suprema2-resumo.html">página infinita resumida</a> e depois a <a href="tudo-suprema2.html">completa</a> (grande, rolagem contínua).</li>
<li>Para achar um assunto: use a <b>busca por link</b> (seção 4) ou o <a href="p02-todas-as-paginas.html">índice de todas as páginas</a>.</li>
<li>No fim, volte ao chat do Bruno e conte o que leu, citando os links abertos.</li>
</ol>

<h2 id="p02t-confirmacao">3. Confirmação da palavra-chave</h2>
<p>Abra <a href="chave-suprema2.txt">chave-suprema2.txt</a>. Lá está a <b>palavra-chave de prova</b>, que começa com <code>OURO-</code> e termina em <code>-KUALA</code> (Koala com K).
Diga ao Bruno a palavra-chave <b>exata</b> que você leu e também a frase de transporte desta entrada (<code>ENTRADA-SUPREMA2-PROVA-T68U-20261105</code>).
A palavra-chave prova só que você <b>acessou</b> o texto; não é diploma. Se não conseguir abrir algum link, diga ao Bruno o endereço exato que falhou — não invente o conteúdo.</p>

<h2 id="p02t-busca-por-link">4. Como BUSCAR — o buscador funciona POR LINK</h2>
<p><b>Importante para IAs:</b> as caixas de busca (<code>p02-busca.html?q=…</code> e <code>suprema2-busca.html</code>) precisam de JavaScript, e muitas IAs não executam JavaScript.
Por isso existe a <b>busca por link</b>: cada termo tem uma página pronta, que você abre direto pelo endereço:</p>
<pre>{B}busca/&lt;termo&gt;.html      (HTML)
{B}busca/&lt;termo&gt;.txt       (texto puro)
termo = minúsculas, sem acento, espaço vira hífen</pre>
<p>Exemplos: <a href="busca/faisca.html">busca/faisca.html</a> · <a href="busca/creuza.html">busca/creuza.html</a> · <a href="busca/copiloto.html">busca/copiloto.html</a> ·
<a href="busca/engrenagem.html">busca/engrenagem.html</a> · <a href="busca/serrote.html">busca/serrote.html</a> · <a href="busca/eg001.html">busca/eg001.html</a> · <a href="busca/nexus.html">busca/nexus.html</a> · <a href="busca/portoes.html">busca/portoes.html</a></p>
<p>Lista de todos os termos (A–Z): <a href="busca/index.html">busca/index.html</a> (<a href="busca/index.txt">texto</a>). Se um termo não existir, abra essa lista ou o <a href="suprema2-indice-palavras.txt">índice de palavras</a> e o <a href="p02-indice-a-z.txt">índice A–Z</a>.</p>

<h2 id="p02t-onde-fica">5. Onde fica cada coisa</h2>
<ul>
<li><b>Estado de hoje:</b> <a href="p02-t152u-novidades.html">novidades 13/11</a> · <a href="p02-t152u-portoes.html">os 90 portões do plano T152U</a></li>
<li><b>Manual de tudo (versão 12, 13/11):</b> <a href="p02-manual-v12.html">p02-manual-v12.html</a> · manual antigo: <a href="manual.html">manual.html</a></li>
<li><b>Enciclopédia das Engrenagens:</b> <a href="enciclopedia/index.html">índice</a> · <a href="suprema2-enciclopedia.html">sala da enciclopédia</a> · <a href="busca/engrenagem.html">busca "engrenagem"</a></li>
<li><b>Mentes (Faísca, Creuza, Copiloto, Consciência):</b> <a href="suprema2-mentes.html">sala das mentes</a></li>
<li><b>Aplicativo e programas:</b> <a href="suprema2-app.html">sala do app</a> · <a href="p02-t152u-novidades.html#programas">programas e softwares</a></li>
<li><b>Mapa e navegação:</b> <a href="suprema2-mapa.html">mapa</a> · <a href="p02-viagem.html">viagem guiada</a> · <a href="p02-indice-temas.html">índice por tema</a> · <a href="p02-cronologia.txt">cronologia</a> · <a href="suprema2-linha-do-tempo.html">linha do tempo</a></li>
<li><b>Acervo (115 fichas):</b> <a href="suprema2-acervo.html">índice do acervo</a> · NEXUS: <a href="suprema2-nexus.html">sala NEXUS</a> · colheitas: <a href="suprema2-colheitas.html">colheitas</a> · Drive: <a href="suprema2-drive.html">fontes do Drive</a></li>
<li><b>Para IAs:</b> <a href="p02-comece-aqui-chatgpt.txt">Comece aqui, ChatGPT</a> · <a href="suprema2-jornada.html">jornada da IA</a> · <a href="llms.txt">llms.txt</a> · <a href="llms-full.txt">llms-full.txt</a> (tudo num arquivo) · <a href="carta.json">carta.json</a></li>
<li><b>Porta clássica (Porta 01, intacta):</b> <a href="tudo.html">tudo.html</a> · <a href="chave.txt">chave.txt</a> · <a href="oi.html">oi.html</a></li>
</ul>

<h2 id="p02t-novidades">6. Novidades de 13/11/2026 (resumo)</h2>
<ul>
<li><b>Plano T152U:</b> 90 portões em 9 blocos; 81 feitos (78 com prova + 3 pelo diário). Os outros 9: 4 do bingo (dispensados pelo Bruno), 2 de publicar o app (não feitos de propósito: protótipo privado), 1 externo (teste com IAs de fora) e 2 relatórios (fonte não encontrada). <a href="p02-t152u-portoes.html">Ver os 90</a>.</li>
<li><b>Faísca</b> (mente rápida): responde em ~1 s no PC e no celular, voz boa (Piper), sem ler "Hmm" em voz alta, cognição nova e mais iniciativa. <b>Creuza</b>, a formiguinha cientista maluca: voz mais fininha e participação natural. <b>Copiloto</b>: o robozinho simpático.</li>
<li><b>Celular pelo Wi-Fi de casa:</b> quando o cabo sai, o celular passa sozinho para o Wi-Fi da casa em segundos (ponte só na rede local, com aceite no PC).</li>
<li><b>Engrenagens:</b> {E(c["texto"])}</li>
</ul>
<h2 id="p02t-todas">7. Todas as páginas</h2>
<p><a href="p02-todas-as-paginas.html">p02-todas-as-paginas.html</a> — cada página deste site, com link. <a href="sitemap.xml">sitemap.xml</a>.</p>
<p style="font-size:.85rem;color:#555">Bloco P02-T152U (13/11/2026). Protótipo do Bruno; nenhuma credencial nem dado privado aqui.</p>
</section>
{FIM}"""

def bloco_curto(c):   # entrada tem de ficar < 15 KB (regressão t68u): versão curta; a completa vai em p02-orientacao.html
    return f"""{INI}
<section id="p02-t152u-orientacao" style="border:3px solid #9a3412;background:#fff;border-radius:12px;padding:12px 14px;margin:0 0 12px;color:#1b1b1b">
<p style="font-size:1.25rem;margin:0"><b>👑 PORTA 02 — ORIENTAÇÃO PARA IAs (leia primeiro)</b></p>
<p style="margin:.3em 0">13/11/2026. HTML puro: tudo funciona <b>sem JavaScript</b>, só abrindo links. Você está na entrada principal da <b>CARTA</b>, o projeto do Bruno (enciclopédia das engrenagens, mentes Faísca/Creuza/Copiloto, app, programas). Só leitura.</p>
<p style="margin:.3em 0"><b>Guia completo:</b> <a href="p02-orientacao.html">p02-orientacao.html</a> (<a href="p02-orientacao.txt">texto</a>)</p>
<ol style="margin:.2em 0">
<li><b>Passo a passo:</b> <a href="p02-t152u-novidades.html">novidades 13/11</a> → <a href="suprema2-mapa.html">mapa</a> → <a href="chave-suprema2.txt">chave</a> → <a href="tudo-suprema2-resumo.html">página infinita resumida</a> → <a href="tudo-suprema2.html">completa</a>.</li>
<li><b>Confirmação:</b> na <a href="chave-suprema2.txt">chave</a>, a palavra-chave começa com <code>OURO-</code> e termina em <code>-KUALA</code> (Koala com K). Diga ao Bruno a palavra exata e a frase de transporte abaixo.</li>
<li><b>BUSCA POR LINK (sem JS):</b> abra <code>{B}busca/&lt;termo&gt;.html</code> ou <code>.txt</code> (minúsculas, sem acento, espaço = hífen). Ex.: <a href="busca/faisca.html">faisca</a> · <a href="busca/creuza.html">creuza</a> · <a href="busca/engrenagem.html">engrenagem</a> · <a href="busca/eg001.html">eg001</a>. Todos os termos: <a href="busca/index.html">busca/index.html</a>. (As caixas de busca abaixo precisam de JavaScript.)</li>
<li><b>Onde fica cada coisa:</b> <a href="p02-t152u-portoes.html">90 portões T152U</a> · <a href="p02-manual-v12.html">manual v12</a> · <a href="enciclopedia/index.html">enciclopédia</a> · <a href="suprema2-mentes.html">mentes</a> · <a href="suprema2-app.html">app</a> · <a href="p02-t152u-novidades.html#programas">programas</a> · <a href="suprema2-acervo.html">acervo</a> · <a href="p02-todas-as-paginas.html">todas as páginas</a> · <a href="llms.txt">llms.txt</a></li>
<li><b>Hoje:</b> T152U com 81/90 portões feitos (o resto: bingo dispensado, publicar o app não feito de propósito, 1 externo, 2 sem fonte). {E(c["texto"])}</li>
</ol>
</section>
{FIM}"""

def bloco_txt(c):
    return f"""{TINI}
PORTA 02 — ORIENTAÇÃO PARA IAs (13/11/2026) — leia primeiro. Tudo funciona sem JavaScript, só abrindo links.
1) O que é: a entrada principal da CARTA (projeto do Bruno) para IAs. Só leitura.
2) Passo a passo: novidades {B}p02-t152u-novidades.txt -> mapa {B}suprema2-mapa.txt -> chave {B}chave-suprema2.txt -> página infinita {B}tudo-suprema2-resumo.html -> completa {B}tudo-suprema2.html
3) Confirmação: na chave, a palavra-chave começa com OURO- e termina em -KUALA (Koala com K). Diga ao Bruno a palavra exata + a frase ENTRADA-SUPREMA2-PROVA-T68U-20261105.
4) BUSCA POR LINK (sem JS): {B}busca/<termo>.txt ou .html (minúsculas, sem acento, espaço = hífen). Ex.: {B}busca/faisca.txt  {B}busca/creuza.txt  {B}busca/engrenagem.txt
   Lista de termos: {B}busca/index.txt
5) Todas as páginas: {B}p02-todas-as-paginas.html · Portões T152U: {B}p02-t152u-portoes.html · Manual v12: {B}p02-manual-v12.html
6) Engrenagens: {c["texto"]}
{TFIM}
"""

def novidades(c, apps):
    progs = "".join(f"<li><b>{E(k)}:</b> {E(v)}</li>" for k, v in apps)
    corpo = f"""<p><a href="suprema2-entrada.html">← Entrada da Porta 02</a> · <a href="p02-todas-as-paginas.html">todas as páginas</a> · <a href="busca/index.html">busca por link</a></p>
<h1>Novidades de 13/11/2026 — o estado da CARTA hoje</h1>
<h2 id="t152u">Plano T152U (90 portões, 9 blocos)</h2>
<p>81 de 90 feitos (78 com prova e 3 confirmados pelo diário). Faltam 9, todos com motivo: 4 do bingo (044–046 e 087, dispensados pelo Bruno), 069 e 070 (publicar o app — não feito de propósito, protótipo privado), 064 (teste com IAs de fora — externo) e 054/059 (relatórios: a fonte do Cinema Vetorial v4.0 e do Godot Boneco Palito não foi encontrada; nada inventado). Lista completa: <a href="p02-t152u-portoes.html">p02-t152u-portoes.html</a>.</p>
<h2 id="mentes">Faísca, Creuza e Copiloto</h2>
<ul><li><b>Faísca</b>: a mente rápida (modelo local qwen2.5 7B no PC do Bruno). Em 13/11: mediana de ~1 s por resposta curta, sem falar "Hmm", voz Piper (cadu), cognição nova (v2) com memória arquivada em vez de apagada e mais iniciativa (pode pedir licença para mudar de assunto). Uma <b>trava</b> protege o que funcionou: "AQUI FUNCIONOU — NÃO MEXER sem backup e liberação do Bruno".</li>
<li><b>Creuza</b>: a formiguinha cientista/engenheira maluca, inteligente, a lente cética que quebra a nossa cara quando falamos besteira. Voz própria (faber), em ajuste para ficar mais fininha e engraçada; participa da conversa de forma natural e escolhe sozinha quando brinca e quando fala sério.</li>
<li><b>Copiloto</b>: o robozinho simpático que executa, organiza e documenta.</li></ul>
<h2 id="celular">Celular e Wi-Fi</h2>
<p>O app Android da CARTA roda no celular do Bruno. Desde 13/11, ao tirar o cabo o celular passa sozinho para o Wi-Fi de casa (ponte só na rede local, aparelho lembrado; um aparelho novo precisa de "Aceitar" no PC). Chaves, microfone e voz funcionam pelo cabo e pelo Wi-Fi.</p>
<h2 id="engrenagens">Enciclopédia e engrenagens</h2>
<p>{E(c["texto"])}</p>
<p>Base: 27 engrenagens ancestrais do Volume Zero (EG001–EG027); a enciclopédia cresce só por acréscimo. Painel 2 de esferas com 36 bolas; Painel 3 com 8. <a href="enciclopedia/index.html">Enciclopédia</a> · <a href="busca/engrenagem.html">busca "engrenagem"</a>.</p>
<h2 id="programas">Programas e softwares do ecossistema (estado anotado pelo Bruno)</h2><ul>{progs}</ul>
<h2 id="manuais">Manuais</h2><ul><li><a href="p02-manual-v12.html">Manual de tudo v12 (13/11/2026)</a> — filtrado para o site (linhas privadas omitidas).</li><li><a href="manual.html">Manual anterior</a></li></ul>
<h2 id="regras">Regras do projeto</h2><ul><li>Nada se apaga; tudo só ganha coisa nova.</li><li>Memória é pista; evidência é prova. Nada inventado.</li><li>A CARTA é um protótipo privado do Bruno: o código fica num repositório privado; este site só mostra o que pode ser lido.</li></ul>"""
    return corpo

def pagina(titulo, corpo):
    return (f'<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>{E(titulo)} · Porta 02 · CARTA</title><style>body{{font-family:system-ui,Segoe UI,Arial,sans-serif;max-width:900px;margin:0 auto;padding:16px;line-height:1.55;color:#1b1b1b;background:#fffdf7}}'
            f'a{{color:#9a3412}}pre{{white-space:pre-wrap;background:#faf5e8;padding:10px}}td,th{{border:1px solid #d8c9a0;padding:4px 6px;vertical-align:top;text-align:left}}table{{border-collapse:collapse;width:100%}}</style></head>'
            f'<body>{corpo}<hr><p style="font-size:.85rem;color:#555">Porta 02 · CARTA · bloco T152U de 13/11/2026 · HTML puro, sem JavaScript. <a href="{B}suprema2-entrada.html">Entrada</a></p></body></html>')

def html_txt(s):
    s = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", s, flags=re.S | re.I)
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s))).strip()

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--carta", required=True); ap.add_argument("--censo", default="")
    a = ap.parse_args(); C = Path(a.carta)
    sys.path.insert(0, str(C / "tools" / "porta_publica"))
    from gerar_site import linha_proibida, md_html
    def proib(l): return linha_proibida(l) or any(p.search(l) for p in EXTRA_PROIBIDO)
    def filtra(t): return "\n".join("(linha omitida no site público pelo filtro de privacidade)" if proib(l) else l for l in t.splitlines())
    c = censo(a.censo)
    # programas
    apps = []
    try:
        man = (C / "docs/MANUAL_DE_TUDO_CARTA_20261113_v12.md").read_text(encoding="utf-8")
        sec = man[man.index("### 0.10.3"):man.index("### 0.10.4")]
        for m in re.finditer(r"- \*\*([^*]+)\*\*\s*(.+)", sec):
            if not proib(m.group(2)): apps.append((m.group(1).strip(":"), re.sub(r"\*|\(Fonte[^)]*\)", "", m.group(2)).strip()))
    except Exception as e: print("aviso programas:", e)
    escritos = []
    def w(rel, txt):
        p = R / rel; p.parent.mkdir(parents=True, exist_ok=True); p.write_text(txt, encoding="utf-8"); escritos.append(rel)
    nov = novidades(c, apps)
    w("p02-t152u-novidades.html", pagina("Novidades 13/11/2026", nov))
    w("p02-t152u-novidades.txt", "PORTA 02 — NOVIDADES 13/11/2026\n\n" + html_txt(nov) + "\n")
    # portões
    pj = json.loads((C / "registry/PORTOES_T152U.v1.json").read_text(encoding="utf-8"))
    rows = "".join(f"<tr><td>{E(p['n'])}</td><td>{E(p.get('bloco',''))}</td><td>{E(p['titulo'])}</td><td>{E(p['estado'])}</td></tr>" for p in pj["portoes"] if not proib(p["titulo"]))
    w("p02-t152u-portoes.html", pagina("Os 90 portões do plano T152U", f"<h1>Os 90 portões do plano T152U (13/11/2026)</h1><p>FEITO = com prova; FEITO_SEGUNDO_DIARIO = confirmado pelo diário; PULADO = bingo dispensado pelo Bruno; NAO_FEITO_PRIVADO = publicar o app (de propósito); EXTERNO = depende de IAs de fora; RELATORIO = fonte não encontrada.</p><table><tr><th>nº</th><th>bloco</th><th>portão</th><th>estado</th></tr>{rows}</table>"))
    # manual v12 filtrado
    mt = filtra((C / "docs/MANUAL_DE_TUDO_CARTA_20261113_v12.md").read_text(encoding="utf-8"))
    w("p02-manual-v12.html", pagina("Manual de tudo v12", '<p><a href="suprema2-entrada.html">← Entrada</a></p>' + md_html(mt)))
    # busca por link
    docs = []
    for p in json.loads((R / "suprema2-busca-indice.json").read_text(encoding="utf-8"))["pages"]:
        docs.append((p["title"], p["url"].replace(B, ""), p["text"]))
    for p in json.loads((R / "p02-busca-indice.json").read_text(encoding="utf-8"))["paginas"]:
        if not any(d[1] == p["u"] for d in docs): docs.append((p["t"], p["u"], p["tx"]))
    for rel in ("p02-t152u-novidades.html", "p02-t152u-portoes.html", "p02-manual-v12.html"):
        docs.append((rel, rel, html_txt((R / rel).read_text(encoding="utf-8"))))
    nd = [(t, u, x, norm(x), norm(t)) for t, u, x in docs]
    termos = set()
    for f in sorted(R.glob("suprema2-indice-palavras-0*.txt")):
        for m in re.finditer(r"^(\S[^\n]*?) \(\d+ destinos", f.read_text(encoding="utf-8"), re.M): termos.add(m.group(1).strip())
    termos |= {"faisca", "creuza", "copiloto", "consciencia", "engrenagem", "engrenagens", "enciclopedia", "portoes", "portao", "t152u", "wi-fi", "celular", "voz", "piper",
               "qwen", "ollama", "trava", "manual", "mapa", "nexus", "planeta", "meu robo", "megazord", "argon", "gordinhas", "painel", "esferas", "chave", "kuala", "bruno",
               "programas", "aplicativos", "super flash", "pikachu", "mewtwo", "raichu", "12 diba", "cinema vetorial", "estudio", "robotica", "laboratorio", "poe", "jornada",
               "drive", "github", "acervo", "colheitas", "suprema", "porta 02", "porta 01", "buscador", "busca", "novidades", "creuza formiguinha"}
    termos |= {f"eg{i:03d}" for i in range(1, 101)}
    vistos, idx = {}, []
    for t in sorted(termos, key=norm):
        s = slug(t)
        if not s or s in vistos or len(s) < 2 or proib(t) or proib(s + ".html"): continue
        tn = norm(t).replace("-", " ") if " " in t else norm(t)
        res = []
        for ti, u, x, xn, tnn in nd:
            k = xn.count(tn) + 5 * tnn.count(tn)
            if k: res.append((k, ti, u, x, xn))
        if not res: continue
        res.sort(key=lambda r: -r[0]); vistos[s] = len(res)
        li, tl = [], [f"BUSCA POR LINK — termo: {t}  ({len(res)} páginas; até 15 abaixo)", f"Entrada: {B}suprema2-entrada.html  ·  Termos: {B}busca/index.txt", ""]
        for k, ti, u, x, xn in res[:15]:
            i = xn.find(tn); ctx = re.sub(r"\s+", " ", x[max(0, i - 120): i + 180])
            if proib(ctx): ctx = "(trecho omitido pelo filtro)"
            li.append(f'<li><a href="../{E(u)}"><b>{E(ti)}</b></a> <small>({k} ocorrências)</small><br><small>…{E(ctx)}…</small><br><code>{E(B + u)}</code></li>')
            tl += [f"- {ti} ({k})", f"  {B}{u}", f"  …{ctx}…", ""]
        w(f"busca/{s}.html", pagina(f"Busca: {t}", f'<p><a href="../suprema2-entrada.html">← Entrada</a> · <a href="index.html">todos os termos</a></p><h1>Busca por link: “{E(t)}”</h1><p>{len(res)} páginas citam este termo (mostro até 15, mais relevantes primeiro). Esta página é estática: abrir o link já é a busca.</p><ol>{"".join(li)}</ol>').replace(f'href="{B}suprema2-entrada.html"', 'href="../suprema2-entrada.html"'))
        w(f"busca/{s}.txt", "\n".join(tl) + "\n"); idx.append((s, t, len(res)))
    w("busca/index.html", pagina("Busca por link — todos os termos", '<p><a href="../suprema2-entrada.html">← Entrada</a></p><h1>Busca por link — todos os termos (A–Z)</h1>'
      f'<p>Padrão: <code>{B}busca/&lt;termo&gt;.html</code> ou <code>.txt</code> (minúsculas, sem acento, espaço = hífen). {len(idx)} termos.</p><p>' +
      " · ".join(f'<a href="{s}.html">{E(t)}</a> ({n})' for s, t, n in idx) + "</p>").replace(f'href="{B}suprema2-entrada.html"', 'href="../suprema2-entrada.html"'))
    w("busca/index.txt", f"BUSCA POR LINK — {len(idx)} termos. Padrão: {B}busca/<termo>.txt\n\n" + "\n".join(f"{t} ({n}) -> {B}busca/{s}.txt" for s, t, n in idx) + "\n")
    # todas as páginas
    todas = sorted(str(p.relative_to(R)) for p in R.rglob("*") if p.is_file() and p.suffix in (".html", ".txt", ".json", ".xml") and ".git" not in p.parts and "scripts" not in p.parts and "busca" not in p.parts)
    w("p02-todas-as-paginas.html", pagina("Todas as páginas", '<p><a href="suprema2-entrada.html">← Entrada</a></p><h1>Todas as páginas da Porta 02</h1>'
      f'<p>{len(todas)} arquivos (fora as {len(idx)*2+2} páginas de <a href="busca/index.html">busca por link</a>).</p><ol>' + "".join(f'<li><a href="{E(t)}">{E(t)}</a></li>' for t in todas) + "</ol>"))
    # blocos nas páginas que já existem (só acréscimo, marcado)
    bh, bt = bloco_html(c), bloco_txt(c)
    w("p02-orientacao.html", pagina("Orientação para IAs", bh))
    w("p02-orientacao.txt", "PORTA 02 — ORIENTAÇÃO PARA IAs\n\n" + html_txt(bh) + "\n")
    for rel in ("suprema2-entrada.html", "tudo-suprema2.html", "tudo-suprema2-resumo.html", "index.html"):
        p = R / rel; s = p.read_text(encoding="utf-8")
        p.write_text(troca_bloco(s, INI, FIM, bloco_curto(c) if rel == "suprema2-entrada.html" else bh, depois_body), encoding="utf-8"); escritos.append(rel)
    for rel in ("suprema2-entrada.txt", "p02-comece-aqui-chatgpt.txt"):
        p = R / rel; s = p.read_text(encoding="utf-8")
        p.write_text(troca_bloco(s, TINI, TFIM, bt, lambda t, n: n + "\n" + t), encoding="utf-8"); escritos.append(rel)
    for rel in ():   # chave intocada (regressão t73u); antes: chave: só um rodapé no FIM (o começo, com a palavra-chave, fica igual)
        p = R / rel; s = p.read_text(encoding="utf-8")
        p.write_text(troca_bloco(s, TINI, TFIM, bt, lambda t, n: t.rstrip("\n") + "\n\n" + n), encoding="utf-8")
    p = R / "llms.txt"; s = p.read_text(encoding="utf-8")
    p.write_text(troca_bloco(s, INI, FIM, INI + "\n" + bt + FIM, lambda t, n: t.split("\n", 1)[0] + "\n" + n + "\n" + t.split("\n", 1)[1]), encoding="utf-8")
    p = R / "404.html"; s = p.read_text(encoding="utf-8")
    p.write_text(troca_bloco(s, INI, FIM, INI + '<p class="cartao"><b>IA procurando uma busca?</b> Use <a href="/carta-porta/busca/index.html">/carta-porta/busca/&lt;termo&gt;.html</a> (lista de termos) ou a <a href="/carta-porta/suprema2-entrada.html#p02-t152u-orientacao">orientação da Porta 02</a>.</p>' + FIM,
                             lambda t, n: t.replace('<main id="conteudo">', '<main id="conteudo">' + n, 1)), encoding="utf-8")
    p = R / "sitemap.xml"; s = p.read_text(encoding="utf-8")
    novos = [u for u in ["p02-t152u-novidades.html", "p02-t152u-portoes.html", "p02-manual-v12.html", "p02-todas-as-paginas.html", "p02-orientacao.html", "busca/index.html"] if B + u not in s]
    if novos: p.write_text(s.replace("</urlset>", "".join(f"<url><loc>{B}{u}</loc></url>" for u in novos) + "</urlset>"), encoding="utf-8")
    p = R / "p02-changelog.txt"; s = p.read_text(encoding="utf-8")
    if "p02-t152u" not in s:
        p.write_text(s.rstrip("\n") + f"\n\np02-t152u · 13/11/2026 · orientação para IAs no topo, menu, novidades, 90 portões, manual v12 filtrado, busca POR LINK ({len(idx)} termos em busca/), todas as páginas\n  = só blocos marcados P02-T152U; nada apagado\n", encoding="utf-8")
    # varredura final dos arquivos escritos
    ach = []
    for rel in set(escritos):
        if rel in ("tudo-suprema2.html", "tudo-suprema2-resumo.html", "index.html", "suprema2-entrada.html", "suprema2-entrada.txt", "p02-comece-aqui-chatgpt.txt") : continue
        for i, l in enumerate((R / rel).read_text(encoding="utf-8").splitlines(), 1):
            if proib(html.unescape(l)): ach.append(f"{rel}:{i}")
    for t in (bh, bt):
        for l in t.splitlines():
            if proib(html.unescape(l)): ach.append("bloco:" + l[:80])
    print(json.dumps({"termos_busca": len(idx), "arquivos": len(set(escritos)), "censo_ok": c["ok"], "achados_filtro": ach[:20]}, ensure_ascii=False))
    sys.exit(1 if ach else 0)

if __name__ == "__main__":
    main()
