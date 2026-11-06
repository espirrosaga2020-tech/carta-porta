#!/usr/bin/env python3
"""New search artifacts only; existing map gets one additive link line."""
import json,re,unicodedata,collections,math
from pathlib import Path
R=Path(__file__).resolve().parents[1];BASE='https://espirrosaga2020-tech.github.io/carta-porta/'
def norm(s):return ''.join(c for c in unicodedata.normalize('NFD',s.lower()) if unicodedata.category(c)!='Mn')
m=json.loads((R/'scripts/t71u_manifesto.json').read_text());pages=[]
for stem,x in m['pages'].items():pages.append({'title':x['title'],'url':BASE+x['html'],'text':(R/x['txt']).read_text()})
assert len(pages)==125
(R/'suprema2-busca-indice.json').write_text(json.dumps({'schema':'suprema2.busca.v1','pages':pages},ensure_ascii=False,separators=(',',':'))+'\n')
stop=set('a ao aos as ate com como da das de dela dele deles depois desse deste do dos e ela ele em entre era essa esse esta este eu foi foram ha isso isto ja la mais mas meu minha muito na nao nas nem no nos nossa nosso num numa o os ou para pela pelo por porque quando que quem se sem seu sua sao ser so sobre sua suas tem ter todo todos tudo um uma uns voce voces'.split())
corpus=[norm(p['text']) for p in pages];counts=[collections.Counter(re.findall(r'\b[a-z][a-z0-9-]{3,}\b',t)) for t in corpus];df=collections.Counter(k for c in counts for k in c)
keys=set('serrote consciencia consciencias faisca creuza copiloto megazord alma atlas nexus escudo enciclopedia engrenagens ancestral volume-zero radinho colheita varredura dobra lanterna mochila memoria evidencia godot robo motores jornada caderninho diploma neon elemento youtube capcut roteiro thumb seo radar android app suprema eg020 cl01 cl02 cl03'.split())
for p,c in zip(pages,counts):
 scores=sorted(((v*math.log((len(pages)+1)/(df[k]+1)),k) for k,v in c.items() if k not in stop and len(k)<36),reverse=True)
 keys.update(k for _,k in scores[:9]);keys.update(w for w in re.findall(r'\b[a-z][a-z0-9-]{3,}\b',norm(p['title'])) if w not in stop)
def entries(key):
 hits=[]
 for p,text in zip(pages,corpus):
  match=re.search(r'(?<![a-z0-9])'+re.escape(key)+r'(?![a-z0-9])',text)
  if match:
   context=re.sub(r'\s+',' ',p['text'][max(0,match.start()-35):match.end()+110]).strip()
   hits.append((key in norm(p['title']),p,context))
 hits.sort(key=lambda h:(not h[0],h[1]['url']))
 return hits
header='PORTA SUPREMA 2 — ÍNDICE DE PALAVRAS (T73U)\nProva: SUPREMA2-INDICE-PALAVRAS-T73U\nEntrada única: '+BASE+'suprema2-entrada.html\nMapa: '+BASE+'suprema2-mapa.html\nBusca local completa: '+BASE+'suprema2-busca.html\n\n125 páginas indexadas. Aqui estão palavras selecionadas dos títulos e do conteúdo, com até 5 destinos por palavra; não é resposta gerada nem prova de compreensão. O buscador HTML pesquisa o texto integral, sem enviar consultas a servidor. A palavra serrote aparece primeiro. Para outras palavras, abra o intervalo alfabético abaixo.\n\n'
blocks={}
for k in sorted(keys):
 h=entries(k)
 if h:blocks[k]=k+' ('+str(len(h))+' destinos; até 5 abaixo)\n'+''.join('  '+p['title']+'\n  '+p['url']+'\n  Contexto: '+ctx+'\n' for _,p,ctx in h[:5])+'\n'
chunks=[];buf='';start='';end=''
for k,b in blocks.items():
 if len((buf+b).encode())>125000 and buf:chunks.append((start,end,buf));buf='';start=''
 if not start:start=k
 end=k;buf+=b
if buf:chunks.append((start,end,buf))
main=header
for i,(a,b,text) in enumerate(chunks,1):
 file=f'suprema2-indice-palavras-{i:02}.txt';(R/file).write_text('PORTA SUPREMA 2 — PALAVRAS '+a+' → '+b+'\nVoltar: '+BASE+'suprema2-indice-palavras.txt\n\n'+text);main+=a+' → '+b+': '+BASE+file+'\n'
for k in ['serrote','consciencia','faisca','creuza','nexus','enciclopedia','engrenagens','caderninho']:main+='\n'+blocks.get(k,k+': nenhum resultado literal.\n')
(R/'suprema2-indice-palavras.txt').write_text(main)
print('Pages',len(pages),'selected keywords',len(blocks),'text shards',len(chunks),'JSON bytes',(R/'suprema2-busca-indice.json').stat().st_size)
