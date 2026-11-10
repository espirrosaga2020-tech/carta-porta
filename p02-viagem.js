/* Porta 02 — selos, sorteio, cartão de viagem e cópia. Só sessionStorage desta aba; nada é enviado. Sem JS, a página funciona como lista de links. */
(function () {
  'use strict';
  var ss = null; try { ss = window.sessionStorage; ss.setItem('p02.t', '1'); } catch (e) { ss = null; }
  function ler(k) { try { return JSON.parse((ss && ss.getItem(k)) || '[]'); } catch (e) { return []; } }
  function gravar(k, v) { if (ss) try { ss.setItem(k, JSON.stringify(v)); } catch (e) {} }
  var total = document.querySelectorAll('[data-selo-item]').length;
  function pintar() {
    var selos = ler('p02.selos');
    document.querySelectorAll('[data-selo-item]').forEach(function (li) {
      var g = selos.indexOf(li.getAttribute('data-selo-item')) > -1; li.classList.toggle('ganho', g); if (g && li.textContent.indexOf('✓') < 0) li.append(' ✓');
    });
    document.querySelectorAll('[data-selo]').forEach(function (p) { p.textContent = selos.indexOf(p.getAttribute('data-selo')) > -1 ? '✓ selo desta sala conquistado nesta sessão' : ''; });
    var pr = document.getElementById('progresso');
    if (pr) pr.textContent = ss ? ('Selos desta sessão: ' + selos.length + ' de ' + total + '. Ficam só nesta aba do navegador; nada é enviado.') : 'Este navegador não guarda selos; a viagem funciona do mesmo jeito.';
  }
  document.addEventListener('click', function (e) {
    var a = e.target.closest && e.target.closest('a[href]'); if (!a) return;
    var href = a.getAttribute('href'); if (!href || href.charAt(0) === '#') return;
    var rota = ler('p02.rota'); var url = new URL(href, location.href).href; if (rota[rota.length - 1] !== url) { rota.push(url); gravar('p02.rota', rota.slice(-60)); }
    var s = a.getAttribute('data-sala'); if (s) { var selos = ler('p02.selos'); if (selos.indexOf(s) < 0) { selos.push(s); gravar('p02.selos', selos); } }
  });
  document.querySelectorAll('[data-sortear]').forEach(function (b) {
    b.addEventListener('click', function () {
      var ol = document.getElementById(b.getAttribute('data-sortear')); var lis = [].slice.call(ol.children);
      for (var i = lis.length - 1; i > 0; i--) { var j = Math.floor(Math.random() * (i + 1)); var t = lis[i]; lis[i] = lis[j]; lis[j] = t; }
      lis.forEach(function (li) { ol.append(li); }); b.textContent = '🎲 Sortear de novo';
    });
  });
  var gerar = document.getElementById('gerar-cartao');
  if (gerar) gerar.addEventListener('click', function () {
    var ta = document.getElementById('cartao'); var agora = new Date().toLocaleString('pt-BR', { timeZone: 'America/Sao_Paulo' });
    var rota = ler('p02.rota'), selos = ler('p02.selos');
    ta.value = ta.value.replace(/^DATA E HORA \(America\/Sao_Paulo\):.*$/m, 'DATA E HORA (America/Sao_Paulo): ' + agora)
      .replace(/^ROTA PERCORRIDA \(URLs, na ordem\):.*$/m, 'ROTA PERCORRIDA (URLs, na ordem): ' + (rota.length ? '\n  ' + rota.join('\n  ') : '(nenhum link aberto nesta sessão)'))
      .replace(/^O QUE LI \(links\):.*$/m, 'O QUE LI (links): ' + (selos.length ? 'salas com selo nesta sessão: ' + selos.join(', ') : ''));
    gerar.textContent = 'Cartão preenchido com a rota desta sessão';
  });
  document.querySelectorAll('[data-copiar]').forEach(function (b) {
    b.addEventListener('click', function () {
      var el = document.getElementById(b.getAttribute('data-copiar')); var ok = function () { b.textContent = 'Copiado ✓'; };
      if (navigator.clipboard && window.isSecureContext) navigator.clipboard.writeText(el.value).then(ok, function () { el.select(); document.execCommand('copy'); ok(); });
      else { el.select(); document.execCommand('copy'); ok(); }
    });
  });
  pintar(); window.addEventListener('pageshow', pintar);
})();
