/* Porta 02 — motor da busca nova (protótipo 10/11/2026). Mesmo arquivo roda no navegador e no teste (node). Sem rede, sem innerHTML. */
(function (raiz) {
  'use strict';
  var PARADAS = {a:1,o:1,as:1,os:1,e:1,de:1,da:1,'do':1,das:1,dos:1,em:1,no:1,na:1,nos:1,nas:1,um:1,uma:1,para:1,por:1,com:1,que:1,se:1,ao:1};
  var SINONIMOS = {diario:['diarios'], diarios:['diario'], emoji:['emojis','emotes','emote'], emojis:['emoji','emotes'], emotes:['emote','emoji','emojis'],
    robo:['robos','robotica','4wd'], mente:['mentes','consciencia','consciencias'], mentes:['mente','consciencias'], engrenagem:['engrenagens'], engrenagens:['engrenagem'],
    consciencia:['consciencias'], consciencias:['consciencia']};
  function normal(s) { return String(s).normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase(); }
  function esc(s) { return s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'); }
  function conta(n, t) {
    if (t.length <= 3) { var m = n.match(new RegExp('(?:^|[^a-z0-9])' + esc(t) + '(?![a-z0-9])', 'g')); return m ? m.length : 0; }
    return n.split(t).length - 1;
  }
  function primeira(n, t) {
    if (t.length <= 3) { var m = new RegExp('(?:^|[^a-z0-9])(' + esc(t) + ')(?![a-z0-9])').exec(n); return m ? m.index + m[0].length - t.length : -1; }
    return n.indexOf(t);
  }
  function preparar(d) {
    d.paginas.forEach(function (p) { p.n = normal(p.tx); p.nt = normal(p.t); p.nr = p.r ? normal(p.r) : ''; p.nid = normal(p.id); p.ni = (p.ids || []).map(normal); });
    return d;
  }
  function analisar(q) {
    var exatas = [];
    var resto = String(q).replace(/"([^"]+)"|“([^”]+)”/g, function (_, a, b) { var f = normal(a || b).replace(/\s+/g, ' ').trim(); if (f) exatas.push(f); return ' '; });
    var nr = normal(resto);
    var termos = nr.split(/[^a-z0-9]+/).filter(function (t) { return t && !PARADAS[t]; });
    var livre = nr.replace(/\s+/g, ' ').trim();
    return { termos: termos, exatas: exatas, livre: livre.split(' ').length > 1 ? livre : null };
  }
  function temTermo(p, t) {
    if (conta(p.n, t) || conta(p.nt, t)) return t;
    var s = SINONIMOS[t] || [];
    for (var i = 0; i < s.length; i++) if (conta(p.n, s[i])) return s[i];
    return null;
  }
  function pontuar(p, a) {
    var s = 0;
    a.termos.forEach(function (t) {
      if (p.nid === t || (p.ni.length === 1 && p.ni[0] === t)) s += 150; else if (p.ni.indexOf(t) > -1) s += 30;
      if (p.nr && conta(p.nr, t)) s += 30;
      if (conta(p.nt, t)) s += 15;
      var c = conta(p.n, t); if (!c) (SINONIMOS[t] || []).forEach(function (x) { c += conta(p.n, x); });
      s += Math.min(c, 25);
    });
    a.exatas.concat(a.livre ? [a.livre] : []).forEach(function (f) {
      if (p.nt.indexOf(f) > -1) s += 60;
      var c = p.n.split(f).length - 1; if (c) s += 20 + Math.min(c, 10) * 2;
    });
    if (p.k === 'sala') s += 6;
    if (p.k === 'porta-p02') s -= 12;
    return s;
  }
  function trecho(p, a) {
    var alvos = a.exatas.concat(a.livre ? [a.livre] : []).concat(a.termos), pos = -1, tam = 0;
    for (var i = 0; i < alvos.length && pos < 0; i++) { pos = primeira(p.n, alvos[i]); tam = alvos[i].length; }
    if (pos < 0) return p.tx.slice(0, 220);
    return p.tx.slice(Math.max(0, pos - 90), pos + tam + 170);
  }
  function buscar(idx, q, limite) {
    var a = analisar(q);
    if (!a.termos.length && !a.exatas.length) return { itens: [], total: 0, modo: 'vazio', termos: [] };
    var exige = function (p) { return a.exatas.every(function (f) { return p.n.indexOf(f) > -1 || p.nt.indexOf(f) > -1; }); };
    var todos = idx.paginas.filter(function (p) { return exige(p) && a.termos.every(function (t) { return temTermo(p, t); }); }), modo = 'todos';
    if (!todos.length && a.termos.length > 1) { todos = idx.paginas.filter(function (p) { return exige(p) && a.termos.some(function (t) { return temTermo(p, t); }); }); modo = 'qualquer'; }
    var itens = todos.map(function (p) { return { p: p, score: pontuar(p, a) }; }).sort(function (x, y) { return y.score - x.score || x.p.u.localeCompare(y.p.u); });
    return { itens: itens.slice(0, limite || 30).map(function (it) { it.trecho = trecho(it.p, a).replace(/\s+/g, ' '); return it; }),
             total: itens.length, modo: modo, termos: a.termos.concat(a.exatas) };
  }
  var api = { normal: normal, preparar: preparar, buscar: buscar, analisar: analisar };
  if (typeof module !== 'undefined' && module.exports) module.exports = api; else raiz.P02Busca = api;
})(this);
