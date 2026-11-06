#!/usr/bin/env python3
"""T71: additive public navigation. Source metadata only; no Drive content or permissions."""
from pathlib import Path
import json, re, html, copy
from bs4 import BeautifulSoup
R=Path(__file__).resolve().parents[1]
D=json.loads((R/'scripts/t71u_fontes.json').read_text())
BASE='https://espirrosaga2020-tech.github.io/carta-porta/'
CARTA='https://github.com/espirrosaga2020-tech/CARTA/'
REF='471a340000f7b847460df555d6fdc2a9ffe285c2'
E=html.escape
STYLE='body{font:17px/1.6 system-ui,sans-serif;max-width:1000px;margin:auto;padding:20px;color:#242020;background:#fffdf7}a{color:#853c00}nav,.aviso{padding:16px;border:2px solid #d6a240;background:#fff4d5;border-radius:10px}h1,h2,h3{line-height:1.25}li{margin:.5em 0}pre{white-space:pre-wrap;overflow-wrap:anywhere}table{border-collapse:collapse;width:100%}td,th{padding:8px;border:1px solid #ccc;text-align:left;overflow-wrap:anywhere}code{overflow-wrap:anywhere}footer{margin-top:30px;border-top:1px solid #b99;padding-top:16px}.meta{font-size:.9em}section,article{scroll-margin-top:10px}'
def link(url,title):return f'<a href="{E(url,quote=True)}">{E(title)}</a>'
def p(t):return '<p>'+E(t)+'</p>'
def reg(path):return CARTA+'blob/'+REF+'/registry/'+path
REG=[reg(n) for n in ['enciclopedia.v1.json','ENCICLOPEDIA_INDICE_UNICO.v1.json','ENCICLOPEDIA_ADITIVOS.v1.json','CONSCIENCIAS_CONHECIMENTO.v1.json']]
NAV='<nav>'+link('suprema2-entrada.html','Entrada')+' · '+link('suprema2-mapa.html','Mapa central')+'</nav>'
rooms=[('colheitas','Colheitas e varreduras','42 referências de colheitas, varreduras, passagens e diários; CL01–CL03.'),('enciclopedia','Enciclopédia e engrenagens','27 ancestrais → 47 registros de snapshot → 76 registros; 62 engrenagens em 19 estantes.'),('nexus','NEXUS e anexos','30 itens diretos inventariados, projetos conectados e bancada YouTube v4.'),('mentes','Mentes, consciências e robótica','ALMA, Faísca, Creuza, Copiloto, Megazord, Atlas V5, Elemento X e ESCUDO.'),('app','Aplicativo CARTA','PRs #136–#142 e histórico documentado dos APKs; não é teste do telefone nesta visita.'),('drive','Índice do Drive','Todos os 140 itens do inventário coletado, sem alterar compartilhamento.'),('linha-do-tempo','Linha do tempo','Origem, evolução, colheitas e portas públicas com fontes e datas.'),('jornada','Jornada, prova e registro','C01–C12 completos, caderninho e registro manual; diploma depende de avaliação. '),('acervo','Acervo público em leituras leves','Todo o corpo documental já público da página completa, dividido em páginas menores.')]
manifest={}
def write(slug,title,body,sources,proof=None):
 proof=proof or 'SUPREMA2-'+slug.upper()+'-T71U'
 name='suprema2-'+slug
 footer='<footer><h2>Fontes</h2><ul>'+''.join('<li>'+link(u,u)+'</li>' for u in dict.fromkeys(sources))+'</ul><p>Prova de acesso desta sala: <code>'+proof+'</code>. A frase não prova leitura integral, compreensão, registro nem diploma.</p>'+NAV+'</footer>'
 out='<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Porta Suprema 2 — '+E(title)+'</title><style>'+STYLE+'</style></head><body>'+NAV+'<h1>Porta Suprema 2 — '+E(title)+'</h1>'+body+p('Inventário e fontes: 05/11/2026 (America/Sao_Paulo). Conteúdo documental não é comprovação de execução atual.')+footer+'</body></html>\n'
 (R/(name+'.html')).write_text(out)
 soup=BeautifulSoup(out,'html.parser')
 for a in soup.find_all('a',href=True):a.append(' <'+(BASE+a['href'] if not re.match(r'https?://',a['href']) else a['href'])+'>')
 for x in soup(['style','script','head']):x.decompose()
 text=soup.get_text('\n',strip=True)+'\n'
 (R/(name+'.txt')).write_text(text)
 for suffix in ['html','txt']:
  size=(R/(name+'.'+suffix)).stat().st_size
  assert size<150000,(name,suffix,size)
 manifest[name]={'title':title,'prova':proof,'html':name+'.html','txt':name+'.txt'}

def drive_item(x):
 return '<li>'+link(x.get('viewUrl','https://drive.google.com/file/d/'+x['id']+'/view'),x['title'])+'<br><code>'+E(x['id'])+'</code> — abrir logado como Bruno.</li>'
def drives(items):return '<ul>'+''.join(drive_item(x) for x in items)+'</ul>'
def extra(title,id,folder=False):return {'title':title,'id':id,'viewUrl':('https://drive.google.com/drive/folders/' if folder else 'https://drive.google.com/file/d/')+id+('' if folder else '/view')}
def selected(pattern):return [x for x in D['inventory'] if re.search(pattern,x['title'],re.I)]
PRIV=p('Os destinos Drive abaixo são privados ou têm permissão não verificada: abrir logado como Bruno. Um conector autorizado pode ser necessário; link não concede acesso. Se a IA não tiver acesso, Bruno pode anexar/exportar o arquivo. Nenhuma permissão foi alterada, nenhum conteúdo privado foi copiado para este site.')
# Entire existing PUBLIC document split by article, with stable cross-file anchors.
soup=BeautifulSoup((R/'tudo-suprema2.html').read_text(),'html.parser')
pages=[]; mapping={}; section_entries=[]
def split_node(node,limit=105000):
 if len(str(node).encode())<=limit:return [copy.deepcopy(node)]
 if not getattr(node,'name',None):
  text=str(node);lines=text.splitlines(keepends=True);parts=[];buf=''
  for line in lines:
   if len((buf+line).encode())>limit and buf:parts.append(BeautifulSoup('<pre></pre>','html.parser').pre);parts[-1].string=buf;buf=''
   if len(line.encode())>limit:
    for pos in range(0,len(line),20000):
     q=BeautifulSoup('<pre></pre>','html.parser').pre;q.string=line[pos:pos+20000];parts.append(q)
   else:buf+=line
  if buf:q=BeautifulSoup('<pre></pre>','html.parser').pre;q.string=buf;parts.append(q)
  return parts
 pieces=[];buf=None
 for child in node.children:
  for frag in split_node(child,limit-1500):
   if buf is None or len((str(buf)+str(frag)).encode())>limit:
    buf=copy.copy(node);buf.clear()
    if pieces:buf.attrs.pop('id',None)
    pieces.append(buf)
   buf.append(frag)
 return pieces
for sec in soup.find_all('section'):
 sid=sec.get('id');heading=sec.find(['h2','h3']);title=heading.get_text(' ',strip=True) if heading else sid
 docs=[]; pending=[]
 def flush_pending():
  if not pending: return
  fragment=BeautifulSoup('<article></article>','html.parser').article
  for child in pending: fragment.append(copy.deepcopy(child))
  if fragment.get_text(strip=True): docs.append(fragment)
  pending.clear()
 for child in sec.children:
  if getattr(child,'name',None)=='article':
   flush_pending();docs.append(child)
  else: pending.append(child)
 flush_pending()
 group=[]
 for doc in docs:
  h=doc.find(['h3','h2']);dt=h.get_text(' ',strip=True) if h else title
  chunks=split_node(doc)
  for part,node in enumerate(chunks,1):
   slug=f'acervo-{len(pages)+1:03d}'; fname='suprema2-'+slug+'.html'
   ids=[x['id'] for x in node.select('[id]')]
   if node.get('id'):ids.insert(0,node['id'])
   for i in ids:mapping.setdefault(i,fname+'#'+i)
   pages.append((slug,dt+(f' — parte {part}/{len(chunks)}' if len(chunks)>1 else ''),node,sid));group.append((slug,dt))
 mapping.setdefault(sid,'suprema2-'+group[0][0]+'.html')
 section_entries.append((sid,title,group))
# Rewrite all local fragment links to their lightweight counterpart.
for index,(slug,title,node,sid) in enumerate(pages):
 for a in node.find_all('a',href=True):
  h=a['href']
  if h.startswith('#'):a['href']=mapping.get(h[1:],'tudo-suprema2.html'+h)
  elif h.startswith('tudo-suprema2.html#'):a['href']=mapping.get(h.split('#',1)[1],h)
 prev=pages[index-1][0] if index else None; nxt=pages[index+1][0] if index+1<len(pages) else None
 paging='<p>'+(''+link('suprema2-'+prev+'.html','← Anterior')+' · ' if prev else '')+link('suprema2-acervo.html','Índice do acervo')+(' · '+link('suprema2-'+nxt+'.html','Próxima →') if nxt else '')+'</p>'
 body='<aside class="aviso">Reprodução de fonte pública já existente, sem completar lacunas por invenção. Este é um recorte histórico: números e estados antigos no documento não substituem o estado datado das salas atuais.</aside>'+paging+'<main id="public-source">'+str(node)+'</main>'+paging
 write(slug,title,body,['https://espirrosaga2020-tech.github.io/carta-porta/tudo-suprema2.html#'+sid])
def dest(i):return mapping.get(i,'tudo-suprema2.html#'+i)
acervo=p(f'{len(pages)} leituras leves preservam o corpo documental público por seção, inclusive as 27 histórias ancestrais completas. Títulos e texto são da fonte; registros históricos não são reclassificados como estado de hoje.')
for sid,title,group in section_entries:
 acervo+='<section id="'+sid+'"><h2>'+E(title)+'</h2><ul>'+''.join('<li>'+link('suprema2-'+s+'.html',t)+'</li>' for s,t in group)+'</ul></section>'
write('acervo','Acervo público em leituras leves',acervo,['tudo-suprema2.html'])
body=p('As colheitas ligam o material documental ao projeto: CL01 Colheita NEXUS; CL02 Pit Stop ESFERA; CL03 Chave e Contagem. A fonte separa relato, documento e implementação: ESCUDO não recebe o número EG040 rejeitado.')
for x in D['mentes']['engrenagens_novas_carta20']:
 if x['id'].startswith('CL'):body+='<h2>'+E(x['id']+' — '+x['titulo'])+'</h2>'+p(x['resumo'])
body+='<h2>42 referências inventariadas</h2>'+PRIV+drives(D['harvests'])
body+='<h2>Conexões</h2><p>'+link('suprema2-nexus.html','NEXUS e bancada')+' · '+link('suprema2-enciclopedia.html','Índice de engrenagens')+' · '+link('suprema2-linha-do-tempo.html','Linha do tempo')+'</p>'
write('colheitas','Colheitas e varreduras',body,REG+[CARTA+'pull/136'])
enc=[extra('Enciclopédia em 3 partes — pasta','1RaeT1lGaUZhHg-KwGWSe7BGSmc6lrxci',True),extra('Enciclopédia — PDF Parte 1','1HKWAYxsPj_s1SQBAoljGAvdvxf8HMoZX'),extra('Enciclopédia — PDF Parte 2','1eCLbrRMQnpOPfL2pg6VK1BZhgHUQ92-6'),extra('Enciclopédia — PDF Parte 3','1K_jFYFJZdh40kncuu3vwZ4h0c_qPOm5s'),extra('Volume Zero — índice mestre','1Ulpg0JWgL-iW3E3YgXqT65S2TbcFyihfhRLflyaSGLE'),extra('Histórico de Contagens — CARTA 2.0','1GppM2l5LnIQJp2CwQPCmDqrxuRE7Giu29H6YQ_7d4fc')]
body=p('27 → 47 → 76 é evolução documental, não contadores em conflito. As 27 fontes ancestrais EG001–EG027 formam o Volume Zero. O índice único guarda 47 registros documentais no snapshot de 18/10/2026. Os 29 aditivos posteriores completam 76 registros. A regra de contagem CARTA 2.0 declara 62 engrenagens em 19 estantes: registro documental e engrenagem não são a mesma unidade.')+PRIV+drives(enc)
body+='<h2>76 registros: IDs, nomes e fontes</h2>'+p('Os prefixos são significativos: EG035, CS035 e CB036 coexistem; não renumerar nem duplicar. Títulos abaixo são extraídos dos dois registros públicos, sem supor que cada documento equivale a uma esfera.')+'<table><tr><th>ID</th><th>Nome</th><th>Camada e leitura</th></tr>'
for layer,key in [('Snapshot 18/10','indice'),('Aditivo posterior','aditivos')]:
 for x in D[key]['registros']:
  id=x['id']; source=reg('ENCICLOPEDIA_'+('INDICE_UNICO' if key=='indice' else 'ADITIVOS')+'.v1.json');read=mapping.get('pg-enciclopedia-'+id.lower(),source)
  body+='<tr><td id="registro-'+E(id)+'">'+E(id)+'</td><td>'+E(x.get('nome',x.get('titulo','')))+'</td><td>'+E(layer)+' · '+link(source,'registro-fonte')+' · '+link(read,'ler')+'</td></tr>'
body+='</table><h2>Histórias ancestrais completas</h2><ul>'
for x in D['ancestral']['engrenagens']:body+='<li>'+link(dest('pg-enciclopedia-'+x['id'].lower()),x['id']+' — '+x['titulo'])+'</li>'
body+='</ul>'+p('Para fichas, mestre e documentos públicos adicionais:')+link('suprema2-acervo.html#enciclopedia','Enciclopédia — índice das leituras leves')
write('enciclopedia','Enciclopédia e engrenagens',body,REG+[x['viewUrl'] for x in enc])
nex=[extra('NEXUS — Arquitetura viva','13kBN7Wrvd12gTLVv7abaTrTJtKh6B259',True)]
anex=[extra(t,i) for t,i in [('P06 — CapCut','1smCoI9-Xj7T2bTNtzIBIoT1ws71bQCd5YAkKS2b8m58'),('P03 — Roteiros','1WfH9T6h7vN6WXZ9c6o-LP1Xw8CjTXMCBbP950s1EZAE'),('P04 — Thumbnails','1UF4KzdiFNBuWOjL7G3ncoNnyAXFxY7cODY-MzCcFtns'),('P05 — SEO','1r_E08riu79_5vrqIBlnbDxukvuLzcvrXbawHSRgeEGE'),('P08 — Radar','1xpxEdNrvEr-jsNo9D6hWcAeBCOrxwzT87-8pbWhsOZk'),('Índice da bancada v4','1FwXZPUGggfbWsfHbHMepqeXJb7uk8UVUQn4lKmFSj5g')]]
body=p('NEXUS é a arquitetura viva que conecta projetos e suas fontes. O inventário desta entrega contém 30 filhos diretos da pasta, incluindo documentos, pastas e anexos — não 30 projetos diferentes. O dashboard é intitulado “38 projetos”; essa referência não é uma contagem independente feita por esta página.')+PRIV+drives(nex)+'<h2>Bancada YouTube — anexos v4</h2>'+drives(anex)+'<h2>30 itens diretos do inventário</h2>'+drives(D['nexus'])+'<p>'+link('suprema2-colheitas.html','Colheitas, varreduras e passagens')+' · '+link('suprema2-drive.html','Índice completo do Drive')+'</p>'
write('nexus','NEXUS e anexos',body,[x['viewUrl'] for x in nex+anex]+['tudo-suprema2.html#ouro-suprema2'])
body=p('ALMA é orientação de conversa conectada às consciências, não uma alegação de subjetividade. A fonte declara a Faísca como o Copiloto morando no celular; Creuza e Copiloto têm identidades documentadas. Megazord reúne especialistas de um cérebro compartilhado. A Cris ainda não existe no código, conforme o registro público.')
body+='<h2>Consciências declaradas na fonte</h2><ul>'+''.join('<li>'+E(x['nome'])+' — '+E(x['por_onde'])+'</li>' for x in D['mentes']['consciencias'])+'</ul>'
body+='<h2>Como o conhecimento chega às mentes</h2>'+p(D['mentes']['superconsciencia'])+'<ul>'
for x in D['mentes']['engrenagens_novas_carta20']:body+='<li>'+E(x['id']+' — '+x['titulo'])+': '+E(x['resumo'])+'</li>'
body+='</ul><h2>Atlas V5 e Elemento X</h2>'+p('PR #137 preencheu o Atlas V5 mantendo 95 tiles e os rótulos de disponibilidade: REAL 10, PARCIAL 1, SIMULADO 1, PLANEJADO 83. Preenchimento documental não converte planejado em realizado. PR #138 moveu cores/neon e Elemento X para Configurações (⚙️), padrão X=3. PR #140 conectou tema.js à Faísca.')
body+='<h2>ESCUDO e robótica</h2>'+p('O texto público descreve pit stop, radinho e “Discordar pra Cima”: esclarecer entendimento, comunicar status e discordar com fundamento e alternativa útil. A robótica 4WD tem portões antes de energizar; nenhum comando de motor é executado por esta página.')+PRIV+drives(selected('ESCUDO|MANUAL|ATLAS|FAÍSCA|CONSCIÊNCIAS|ROBÓ|RAMIFICA'))
body+='<p>'+link('suprema2-acervo.html#consciencias','Documentação das consciências')+' · '+link('suprema2-acervo.html#manual','Manual completo em leitura leve')+' · '+link('suprema2-app.html','Mudanças do app')+'</p>'
write('mentes','Mentes, consciências e robótica',body,REG+[CARTA+'pull/'+str(i) for i in [137,138,139,140]]+['tudo-suprema2.html#ouro-suprema2'])
body=p('Esta sala documenta o app, não instala APK nem comprova a tela atual do celular. PR #141 introduz o card da Porta Suprema 2 na última linha do Início, depois da Porta do Grok. PR #142 muda seu link primário para a entrada pequena, preservando completa e chave como secundários.')
body+='<h2>PRs #136–#142 — fonte e estado</h2><ul>'
for x in D['prs']:
 body+='<li>'+link(x['html_url'],'#'+str(x['number'])+' — '+x['title'])+'<br>'+E('Mesclado; commit '+str(x['merge_commit_sha']))+'</li>'
body+='</ul><h2>Histórico de APKs</h2>'+p('vc27–vc30 são versões históricas mencionadas na continuidade do projeto. Para vc27 não há manifesto de versão validado nesta coleta: não se inventa rótulo, instalação nem teste. O registro de consciências menciona vc28. A seção OURO documenta vc29 1.23.0-carta20-t56u-bolinha; o PR #141 documenta vc30 1.24.0-carta20-t63u-suprema2. A atualização posterior do código no PR #142 não prova que o aparelho recebeu outro APK.')
body+='<h2>Faísca</h2>'+p('Cores/neon e Elemento X ficam no ⚙️; menu #bola permanece. O conhecimento CL01–CL03 e Enc.62 é ramificado na ALMA pelo PR #139. Consulte as salas de mentes e engrenagens para os conteúdos e o app para verificar a execução.')+PRIV+drives(selected('APP CARTA|T54U|PASSAGEM_BASTAO_T63'))
write('app','Aplicativo CARTA',body,[x['html_url'] for x in D['prs']]+REG+['tudo-suprema2.html#ouro-suprema2'])
body=p('140 itens únicos do inventário coletado, não um inventário exaustivo de todo o Google Drive. As buscas gerais tinham paginação restante. Títulos repetidos com IDs diferentes são arquivos distintos, preservados. Aqui estão todos os 140 itens recebidos para esta entrega.')+PRIV+drives(D['inventory'])
write('drive','Índice do Drive',body,['https://drive.google.com/drive/folders/13kBN7Wrvd12gTLVv7abaTrTJtKh6B259','suprema2-nexus.html','suprema2-colheitas.html'])
trajectory=copy.deepcopy(soup.find(id='trajetoria'))
body=p('A cronologia abaixo é reproduzida da seção de origem, como documento histórico. “Planejado” não significa realizado. Para as mudanças de 05/11 use os PRs datados abaixo.')+str(trajectory)+'<h2>Camadas da Enciclopédia</h2>'+p('27 fontes ancestrais até 10/10 → snapshot de 47 registros em 18/10 → 29 aditivos até 05/11 = 76 registros. O registro de consciências declara 62 engrenagens, em 19 estantes.')+'<h2>Portas públicas e expansão</h2>'+p('A primeira conquista pública está documentada em 03–04/11, preservada como clássica. A Porta Suprema 2 acrescenta a seção OURO de 05/11. A entrada leve t68u separa transporte, leitura, compreensão e registro; esta entrega t71u acrescenta mapa e salas sem substituir a entrada ou a clássica.')+'<ul>'
for x in D['prs']:
 from datetime import datetime
 from zoneinfo import ZoneInfo
 dt=datetime.fromisoformat(x['merged_at'].replace('Z','+00:00')).astimezone(ZoneInfo('America/Sao_Paulo')).strftime('%d/%m/%Y %H:%M')
 body+='<li>'+E(dt+' (America/Sao_Paulo) — ')+link(x['html_url'],'#'+str(x['number'])+' '+x['title'])+'</li>'
body+='</ul>'+PRIV+drives(selected('ENDURANCE|HISTÓRICO DE CONTAGENS|PASSAGEM'))
write('linha-do-tempo','Linha do tempo',body,['tudo-suprema2.html#origem',REG[1],REG[2]]+[x['html_url'] for x in D['prs']])
journey=copy.deepcopy(soup.find(id='jornada'))
for a in journey.find_all('a',href=True):
 h=a['href']
 if h.startswith('#'):a['href']=dest(h[1:])
body='<aside class="aviso">A jornada e C01–C12 são tarefas da IA visitante, não falhas da porta. Criar o caderninho exige um conector Drive autorizado. Sem ele, a IA entrega o texto ao Bruno e declara registro pendente — não finge que gravou. Registro é cópia manual ao Bruno + caderninho; esta página não envia respostas ao app.</aside>'+p('Nome do caderninho: CADERNINHO_<IA>_<data>. Registre Vi / Senti ou gostei / Não entendi, sempre com endereços. Recuperar frase prova transporte; ler é outra etapa; compreender e registrar são etapas independentes.')+str(journey)+'<h2>Onde pesquisar cada pergunta sem carregar a página gigante</h2><ul>'
for sid,title,_ in section_entries:body+='<li>'+link('suprema2-acervo.html#'+sid,title)+'</li>'
body+='</ul>'
write('jornada','Jornada, prova e registro',body,['tudo-suprema2.html#jornada','chave-suprema2.txt','suprema2-entrada.html'])
body='<aside class="aviso"><b>Comece por aqui.</b> Uma entrada, um mapa, caminhos curtos. Leia uma sala por vez; cada HTML tem uma alternativa em texto puro. O acervo público foi dividido, e o Drive privado permanece privado.</aside>'+p(f'Esta entrega reúne 140 itens do Drive, 42 referências de colheitas/varreduras, 30 filhos diretos da pasta NEXUS e {len(pages)} leituras leves do acervo público anterior. Não são milhões de links nem uma alegação de ter lido todo o Drive.')+'<h2>Salas do projeto</h2><ol>'
for slug,title,desc in rooms:body+='<li>'+link('suprema2-'+slug+'.html',title)+' — '+E(desc)+' '+link('suprema2-'+slug+'.txt','texto puro')+'</li>'
body+='</ol><h2>Todos os temas já públicos</h2><ul>'
for sid,title,_ in section_entries:body+='<li>'+link('suprema2-acervo.html#'+sid,title)+'</li>'
body+='</ul><h2>Roteiros recomendados</h2><ul><li>Conhecer a história: Linha do tempo → Acervo / A origem → Enciclopédia → Jornada.</li><li>Retomar trabalho: Colheitas → NEXUS → Mentes → App → fontes pertinentes no Drive.</li><li>Fazer a prova: Jornada → escolher a história ancestral inteira → caderninho → C01–C12 → devolver registro ao Bruno.</li></ul>'+PRIV+'<h2>Limites claros</h2>'+p('O site público não abre portas locais 8790/8791 nem liga motores, não dá acesso automático ao Drive privado, não instala APK, não envia registro e não concede diploma. Links e documentação não equivalem a execução. Se um destino falhar, informe o endereço e o erro; não substitua evidência por lembrança.')+'<p>'+link('tudo-suprema2.html','Documento público completo anterior')+' · '+link('tudo.html','Clássica preservada')+' · '+link('chave-suprema2.txt','Orientações da Porta Suprema 2')+'</p>'
write('mapa','Mapa central',body,['tudo-suprema2.html',*REG])
# Additive insertion only in approved nonclassic surfaces.
for f in ['suprema2-entrada.html','tudo-suprema2-resumo.html','index.html']:
 path=R/f;s=path.read_text()
 marker='<p class="card" id="mapa-central-t71u"><strong>'+link('suprema2-mapa.html','Porta Suprema 2 — MAPA COMPLETO DO PROJETO')+'</strong> · '+link('suprema2-mapa.txt','mapa em texto puro')+' · salas, acervo público leve e fontes do Drive.</p>\n'
 if 'id="mapa-central-t71u"' not in s:
  s=re.sub(r'(<body[^>]*>)',lambda m:m.group(1)+'\n'+marker,s,count=1);path.write_text(s)
for f in ['chave-suprema2.txt','llms.txt']:
 path=R/f;s=path.read_text()
 if BASE+'suprema2-mapa.html' not in s:path.write_text(s+'\nPorta Suprema 2 — mapa completo (T71U): '+BASE+'suprema2-mapa.html\nAlternativa texto puro: '+BASE+'suprema2-mapa.txt\n')
# Entry TXT keeps parity with HTML addition, without regenerating original content.
p=R/'suprema2-entrada.txt';t=p.read_text()
if BASE+'suprema2-mapa.html' not in t:p.write_text(t+'\nPorta Suprema 2 — mapa completo: '+BASE+'suprema2-mapa.html\n')
(R/'scripts/t71u_manifesto.json').write_text(json.dumps({'base_porta':'bd295e0','carta_ref':REF,'drive_items':140,'harvest_refs':42,'nexus_children':30,'public_readings':len(pages),'pages':manifest},ensure_ascii=False,indent=2)+'\n')
print('Generated',len(manifest),'page pairs;',len(pages),'public readings')
