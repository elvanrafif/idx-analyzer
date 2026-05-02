const themes = {
  dark:  { icon: '\u2600\uFE0F', label: 'Light Mode', next: 'light' },
  light: { icon: '\uD83C\uDF19', label: 'Dark Mode',  next: 'dark'  }
};

function applyTheme(t) {
  document.documentElement.setAttribute('data-theme', t);
  document.getElementById('t-icon').textContent  = themes[t].icon;
  document.getElementById('t-label').textContent = themes[t].label;
  localStorage.setItem('idx-theme', t);
}

function toggleTheme() {
  const cur = document.documentElement.getAttribute('data-theme') || 'dark';
  applyTheme(themes[cur].next);
}

applyTheme(localStorage.getItem('idx-theme') || 'dark');

const inp = document.getElementById('ticker-input');
inp.addEventListener('keydown', e => { if (e.key === 'Enter') analyze(); });
inp.addEventListener('input',   () => { inp.value = inp.value.toUpperCase(); });

async function analyze() {
  const ticker = inp.value.trim().toUpperCase();
  if (!ticker) return;
  hide('error-box'); hide('result'); show('loading');
  document.getElementById('search-btn').disabled = true;
  try {
    const r = await fetch('/api/analyze?ticker=' + ticker);
    const d = await r.json();
    hide('loading');
    document.getElementById('search-btn').disabled = false;
    if (d.error) { showErr(d.error); return; }
    render(d);
  } catch (e) {
    hide('loading');
    document.getElementById('search-btn').disabled = false;
    showErr('Koneksi gagal atau limit tercapai. Tunggu beberapa saat.');
  }
}

function show(id) { document.getElementById(id).style.display = 'block'; }
function hide(id) { document.getElementById(id).style.display = 'none'; }
function showErr(m) {
  const el = document.getElementById('error-box');
  el.textContent = '\u26A0 ' + m;
  el.style.display = 'block';
}

function fnum(v, type) {
  if (v === null || v === undefined || v !== v) return '<span class="na">\u2014</span>';
  const n = parseFloat(v);
  if (isNaN(n)) return String(v);
  const abs = Math.abs(n), sign = n < 0;
  let s;
  if (type === 'idr') {
    if (abs >= 1e12) s = 'Rp ' + (n / 1e12).toFixed(2) + 'T';
    else if (abs >= 1e9)  s = 'Rp ' + (n / 1e9).toFixed(2) + 'M';
    else if (abs >= 1e6)  s = 'Rp ' + (n / 1e6).toFixed(2) + 'Jt';
    else s = 'Rp ' + n.toLocaleString('id');
  } else if (type === 'pct') {
    s = (n * 100).toFixed(2) + '%';
  } else {
    if (abs >= 1e12) s = (n / 1e12).toFixed(2) + 'T';
    else if (abs >= 1e9) s = (n / 1e9).toFixed(2) + 'B';
    else if (abs >= 1e6) s = (n / 1e6).toFixed(2) + 'M';
    else s = n.toLocaleString('id', { maximumFractionDigits: 2 });
  }
  return sign ? '<span class="neg">' + s + '</span>' : s;
}

function fval(v) {
  return fnum(v, typeof v === 'number' && Math.abs(v) > 5000 ? 'idr' : 'num');
}

const R = {
  pe:  v => !v ? '' : v < 10 ? '\uD83D\uDFE2 Murah' : v < 20 ? '\uD83D\uDFE1 Wajar' : v < 30 ? '\uD83D\uDFE0 Mahal' : '\uD83D\uDD34 Sangat Mahal',
  pb:  v => !v ? '' : v < 1 ? '\uD83D\uDFE2 Di Bawah Book' : v < 2 ? '\uD83D\uDFE1 Wajar' : v < 4 ? '\uD83D\uDFE0 Premium' : '\uD83D\uDD34 Sangat Mahal',
  de:  v => !v ? '' : v < 50 ? '\uD83D\uDFE2 Rendah' : v < 100 ? '\uD83D\uDFE1 Sedang' : v < 200 ? '\uD83D\uDFE0 Tinggi' : '\uD83D\uDD34 Sangat Tinggi',
  roe: v => !v ? '' : (p => p >= 20 ? '\uD83D\uDFE2 Excellent' : p >= 15 ? '\uD83D\uDFE1 Bagus' : p >= 10 ? '\uD83D\uDFE0 Sedang' : p > 0 ? '\uD83D\uDD34 Rendah' : '\uD83D\uDD34 Rugi')(v * 100),
  roa: v => !v ? '' : (p => p >= 10 ? '\uD83D\uDFE2 Excellent' : p >= 7 ? '\uD83D\uDFE1 Bagus' : p >= 5 ? '\uD83D\uDFE0 Sedang' : p > 0 ? '\uD83D\uDD34 Rendah' : '\uD83D\uDD34 Rugi')(v * 100),
  npm: v => !v ? '' : (p => p >= 20 ? '\uD83D\uDFE2 Tinggi' : p >= 10 ? '\uD83D\uDFE1 Sedang' : p >= 5 ? '\uD83D\uDFE0 Tipis' : p > 0 ? '\uD83D\uDD34 Sangat Tipis' : '\uD83D\uDD34 Rugi')(v * 100),
  cr:  v => !v ? '' : v >= 2 ? '\uD83D\uDFE2 Sangat Sehat' : v >= 1.5 ? '\uD83D\uDFE1 Sehat' : v >= 1 ? '\uD83D\uDFE0 Cukup' : '\uD83D\uDD34 Rawan',
  dy:  v => !v ? '' : (p => p >= 5 ? '\uD83D\uDFE2 Tinggi' : p >= 3 ? '\uD83D\uDFE1 Menarik' : p >= 1 ? '\uD83D\uDFE0 Rendah' : '\uD83D\uDD34 Sangat Rendah')(v * 100),
};

function badge(txt) {
  if (!txt) return '';
  const m = { '\uD83D\uDFE2': 'bg', '\uD83D\uDFE1': 'by', '\uD83D\uDFE0': 'bo', '\uD83D\uDD34': 'br', '\uD83D\uDD18': 'bb', '\u2705': 'bg' };
  return '<span class="badge ' + (m[txt[0]] || 'bb') + '">' + txt + '</span>';
}

function sec(icon, title, body, open, wide) {
  const id = 's' + Math.random().toString(36).slice(2, 8);
  return '<div class="section glass' + (open ? '' : ' collapsed') + '"' + (wide ? ' style="grid-column:span 2"' : '') + ' id="' + id + '">' +
    '<div class="section-header" onclick="document.getElementById(\'' + id + '\').classList.toggle(\'collapsed\')">' +
      '<div class="section-icon">' + icon + '</div>' +
      '<div class="section-title">' + title + '</div>' +
      '<div class="section-toggle">\u25BC</div>' +
    '</div>' +
    '<div class="section-divider"></div>' +
    '<div class="section-body">' + body + '</div>' +
  '</div>';
}

function dtable(rows) {
  return '<table class="data-table">' + rows.map(function(r) {
    return '<tr><td class="td-label">' + r[0] + '</td><td class="td-val">' + fval(r[1]) + '</td><td class="td-rating">' + (r[2] ? badge(r[2]) : '') + '</td></tr>';
  }).join('') + '</table>';
}

function ftable(data, metrics) {
  if (!data || !data.columns || !data.columns.length) return '<p class="no-data">Data tidak tersedia.</p>';
  const cols = data.columns.slice(0, 4);
  return '<div class="table-scroll"><table class="fin-table">' +
    '<thead><tr><th>Metrik</th>' + cols.map(function(c) { return '<th>' + c + '</th>'; }).join('') + '</tr></thead>' +
    '<tbody>' + metrics.map(function(m) {
      var key = m[0], label = m[1];
      var row = data.data[key];
      if (!row) return '<tr><td>' + label + '</td>' + cols.map(function() { return '<td class="na">\u2014</td>'; }).join('') + '</tr>';
      return '<tr><td>' + label + '</td>' + cols.map(function(c) {
        var v = row[c];
        if (v === null || v === undefined) return '<td class="na">\u2014</td>';
        return '<td class="' + (v < 0 ? 'neg' : '') + '">' + fnum(v, 'idr') + '</td>';
      }).join('') + '</tr>';
    }).join('') + '</tbody></table></div>';
}

function initTabs() {
  document.querySelectorAll('.tabs').forEach(function(tabBar) {
    tabBar.querySelectorAll('.tab').forEach(function(tab) {
      tab.addEventListener('click', function() {
        var panelId = tab.getAttribute('data-panel');
        var parent = tabBar.parentElement;
        tabBar.querySelectorAll('.tab').forEach(function(t) { t.classList.remove('active'); });
        tab.classList.add('active');
        parent.querySelectorAll('.tab-panel').forEach(function(p) { p.classList.remove('active'); });
        var target = document.getElementById(panelId);
        if (target) target.classList.add('active');
      });
    });
  });
}

function fetchAIInsight(ticker, section, data) {
  var cacheKey = 'ai_' + ticker + '_' + section;
  var cached = sessionStorage.getItem(cacheKey);
  if (cached) {
    insertAIBox(section, '<div class="ai-insight"><div class="ai-label">\uD83E\uDD16 AI INSIGHT</div><div class="ai-text">' + cached + '</div></div>');
    return;
  }
  var placeholderId = 'ai-' + section + '-' + Math.random().toString(36).slice(2, 8);
  insertAIBox(section, '<div class="ai-insight" id="' + placeholderId + '"><div class="ai-label">\uD83E\uDD16 AI INSIGHT</div><div class="ai-text ai-loading">Memuat insight...</div></div>');

  fetch('/api/ai-insight', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ ticker: ticker, section: section, data: data })
  }).then(function(r) { return r.json(); }).then(function(res) {
    if (res.insight) {
      sessionStorage.setItem(cacheKey, res.insight);
      var el = document.getElementById(placeholderId);
      if (el) {
        var textEl = el.querySelector('.ai-text');
        textEl.classList.remove('ai-loading');
        typeText(textEl, res.insight);
      }
    } else {
      var el2 = document.getElementById(placeholderId);
      if (el2) el2.style.display = 'none';
    }
  }).catch(function() {
    var el3 = document.getElementById(placeholderId);
    if (el3) el3.style.display = 'none';
  });
}

function insertAIBox(section, html) {
  var targets = {
    'valuasi': function() {
      var panels = document.querySelectorAll('.tab-panel');
      if (panels.length > 0) panels[0].insertAdjacentHTML('beforeend', html);
    },
    'profitabilitas': function() {
      var panels = document.querySelectorAll('.tab-panel');
      if (panels.length > 1) panels[1].insertAdjacentHTML('beforeend', html);
    },
    'kesehatan': function() {
      var panels = document.querySelectorAll('.tab-panel');
      if (panels.length > 2) panels[2].insertAdjacentHTML('beforeend', html);
    },
    'dividen': function() {
      var panels = document.querySelectorAll('.tab-panel');
      if (panels.length > 3) panels[3].insertAdjacentHTML('beforeend', html);
    },
    'composite': function() {
      var sections = document.querySelectorAll('.section');
      if (sections.length > 2) sections[2].querySelector('.section-body').insertAdjacentHTML('beforeend', html);
    },
    'consensus': function() {
      var sections = document.querySelectorAll('.section');
      if (sections.length > 1) sections[1].querySelector('.section-body').insertAdjacentHTML('beforeend', html);
    },
    'scoring': function() {
      var sections = document.querySelectorAll('.section');
      if (sections.length > 4) sections[4].querySelector('.section-body').insertAdjacentHTML('beforeend', html);
    },
    'technical': function() {
      var sections = document.querySelectorAll('.section');
      for (var i = 0; i < sections.length; i++) {
        if (sections[i].querySelector('.section-title') && sections[i].querySelector('.section-title').textContent.indexOf('TECHNICAL') >= 0) {
          sections[i].querySelector('.section-body').insertAdjacentHTML('beforeend', html);
          return;
        }
      }
    },
    'risk': function() {
      var sections = document.querySelectorAll('.section');
      for (var i = 0; i < sections.length; i++) {
        if (sections[i].querySelector('.section-title') && sections[i].querySelector('.section-title').textContent.indexOf('RISK') >= 0) {
          sections[i].querySelector('.section-body').insertAdjacentHTML('beforeend', html);
          return;
        }
      }
    },
    'financial': function() {
      var sections = document.querySelectorAll('.section');
      for (var i = 0; i < sections.length; i++) {
        if (sections[i].querySelector('.section-title') && sections[i].querySelector('.section-title').textContent.indexOf('FINANCIAL') >= 0) {
          sections[i].querySelector('.section-body').insertAdjacentHTML('beforeend', html);
          return;
        }
      }
    }
  };
  if (targets[section]) targets[section]();
}

function typeText(el, text) {
  var i = 0;
  var speed = 12;
  function tick() {
    if (i < text.length) {
      el.textContent += text.charAt(i);
      i++;
      setTimeout(tick, speed);
    }
  }
  el.textContent = '';
  tick();
}

function renderHero(d) {
  var i = d.info;
  var price = i.regularMarketPrice || i.currentPrice;
  var prev  = i.regularMarketPreviousClose;
  var chg   = prev ? (price - prev) / prev * 100 : null;
  var chgCls = chg > 0 ? 'up' : chg < 0 ? 'down' : 'neutral';
  var chgStr = chg !== null ? (chg >= 0 ? '+' : '') + chg.toFixed(2) + '%' : '\u2014';

  return '<div class="hero glass">' +
    '<div>' +
      '<div class="hero-ticker">' + d.ticker + ' \u00B7 IDX \u00B7 ' + d.updated + '</div>' +
      '<div class="hero-name">' + (i.longName || i.shortName || d.ticker) + '</div>' +
      '<div class="hero-tags">' +
        '<span class="tag">' + (i.sector || 'N/A') + '</span>' +
        '<span class="tag">' + (i.industry || 'N/A') + '</span>' +
      '</div>' +
    '</div>' +
    '<div class="hero-price">' +
      '<div class="price-main">Rp ' + (price ? price.toLocaleString('id') : '\u2014') + '</div>' +
      '<div class="price-change ' + chgCls + '">' + chgStr + ' hari ini</div>' +
    '</div>' +
  '</div>';
}

function renderMetrics(d) {
  var i = d.info;
  var price = i.regularMarketPrice || i.currentPrice;
  var wk52pos = (i.fiftyTwoWeekLow && i.fiftyTwoWeekHigh && price)
    ? ((price - i.fiftyTwoWeekLow) / (i.fiftyTwoWeekHigh - i.fiftyTwoWeekLow) * 100).toFixed(1) + '%'
    : null;
  var upside = (i.targetMeanPrice && price) ? ((i.targetMeanPrice - price) / price * 100).toFixed(1) : null;

  var left = [
    ['Market Cap', fnum(i.marketCap, 'idr')],
    ['52wk High', '<span class="pos">' + fnum(i.fiftyTwoWeekHigh, 'idr') + '</span>'],
    ['52wk Low', '<span class="neg">' + fnum(i.fiftyTwoWeekLow, 'idr') + '</span>'],
    ['52wk Position', wk52pos || '<span class="na">\u2014</span>'],
    ['Volume Hari Ini', fnum(i.regularMarketVolume)],
    ['Avg Volume 10d', fnum(i.averageVolume10days)]
  ];

  var right = [
    ['P/E Ratio', fval(i.trailingPE)],
    ['Debt/Equity', fval(i.debtToEquity)],
    ['ROE', fval(i.returnOnEquity)],
    ['Current Ratio', fval(i.currentRatio)],
    ['Div. Yield', i.dividendYield != null ? (i.dividendYield * 100).toFixed(2) + '%' : '<span class="na">\u2014</span>'],
    ['Target Upside', upside != null ? '<span class="' + (upside > 0 ? 'pos' : 'neg') + '">' + (upside > 0 ? '+' : '') + upside + '%</span>' : '<span class="na">\u2014</span>']
  ];

  function metricCard(title, rows) {
    return '<div class="metric-card"><div class="metric-card-title">' + title + '</div>' +
      rows.map(function(r) {
        return '<div class="metric-row"><span class="metric-label">' + r[0] + '</span><span class="metric-value">' + r[1] + '</span></div>';
      }).join('') + '</div>';
  }

  return '<div class="metrics-grid">' + metricCard('STATISTIK', left) + metricCard('SCORING', right) + '</div>';
}

function renderComposite(c) {
  if (!c) return '<p class="no-data">Data composite tidak tersedia.</p>';
  var weights = { Fundamental: '30%', Technical: '25%', Risk: '20%', Momentum: '15%', Sentiment: '10%' };
  return '<div class="composite-card">' +
    '<div>' +
      '<div class="composite-score-num ' + (c.final >= 70 ? 'pos' : c.final < 35 ? 'neg' : '') + '">' + c.final + '</div>' +
      '<div style="font-size:10px;color:var(--text-secondary);margin-top:4px;">/ 100</div>' +
    '</div>' +
    '<div class="composite-info">' +
      '<div class="composite-signal ' + c.cls + '">' + c.signal + '</div>' +
      '<div style="font-size:10px;color:var(--text-secondary);margin-top:6px;">Skor Keputusan Komprehensif</div>' +
    '</div>' +
    '<div class="composite-bars">' +
      Object.entries(c.components).map(function(e) {
        return '<div class="cbar-row">' +
          '<span class="cbar-label">' + e[0] + ' <span style="opacity:.5">' + (weights[e[0]] || '') + '</span></span>' +
          '<div class="cbar-track"><div class="cbar-fill" style="width:' + e[1] + '%"></div></div>' +
          '<span class="cbar-val">' + e[1] + '</span>' +
        '</div>';
      }).join('') +
    '</div>' +
  '</div>';
}

function renderConsensus(d) {
  var votes = [];
  if (d.macd_bb) {
    var sig = d.macd_bb.macd.signal_label;
    var v = sig === 'BULLISH' ? 1 : -1;
    votes.push({ name: 'MACD (12,26,9)', label: sig, cls: v === 1 ? 'sig-bullish' : 'sig-bearish', vote: v, detail: 'hist ' + d.macd_bb.macd.hist });
  }
  if (d.macd_bb) {
    var bsig = d.macd_bb.bb.signal;
    var bv = (bsig === 'BULLISH' || bsig === 'OVERSOLD') ? 1 : (bsig === 'BEARISH' || bsig === 'OVERBOUGHT') ? -1 : 0;
    var bcls = bsig === 'OVERBOUGHT' ? 'sig-overbought' : bsig === 'OVERSOLD' ? 'sig-oversold' : bv === 1 ? 'sig-bullish' : bv === -1 ? 'sig-bearish' : 'sig-netral';
    votes.push({ name: 'Bollinger Bands', label: bsig, cls: bcls, vote: bv, detail: '%B ' + (d.macd_bb.bb.pct_b * 100).toFixed(0) + '%' });
  }
  if (d.rsi) {
    var rv = d.rsi.signal === 'OVERSOLD' ? 1 : d.rsi.signal === 'OVERBOUGHT' ? -1 : 0;
    var rcls = d.rsi.signal === 'OVERSOLD' ? 'sig-oversold' : d.rsi.signal === 'OVERBOUGHT' ? 'sig-overbought' : 'sig-netral';
    votes.push({ name: 'RSI (14)', label: d.rsi.signal, cls: rcls, vote: rv, detail: 'RSI ' + d.rsi.value });
  }
  if (d.piotroski) {
    var pv = d.piotroski.rating === 'KUAT' ? 1 : d.piotroski.rating === 'LEMAH' ? -1 : 0;
    var pcls = d.piotroski.rating === 'KUAT' ? 'sig-bullish' : d.piotroski.rating === 'LEMAH' ? 'sig-bearish' : 'sig-netral';
    votes.push({ name: 'Piotroski F-Score', label: d.piotroski.rating, cls: pcls, vote: pv, detail: d.piotroski.score + '/9 poin' });
  }
  if (d.altman) {
    var av = d.altman.zone === 'AMAN' ? 1 : d.altman.zone === 'BAHAYA' ? -1 : 0;
    var acls = d.altman.zone === 'AMAN' ? 'sig-bullish' : d.altman.zone === 'BAHAYA' ? 'sig-bearish' : 'sig-netral';
    votes.push({ name: 'Altman Z-Score', label: d.altman.zone, cls: acls, vote: av, detail: 'Z ' + d.altman.z_score });
  }
  if (d.rvol) {
    var rvv = (d.rvol.signal === 'SANGAT TINGGI' || d.rvol.signal === 'TINGGI') ? 1 : d.rvol.signal === 'RENDAH' ? -1 : 0;
    var rvcls = rvv === 1 ? 'sig-bullish' : rvv === -1 ? 'sig-bearish' : 'sig-netral';
    votes.push({ name: 'Rel. Volume', label: d.rvol.signal, cls: rvcls, vote: rvv, detail: d.rvol.rvol + 'x avg' });
  }
  if (votes.length === 0) return '<p class="no-data">Data tidak cukup untuk konsensus.</p>';

  var buyCount = votes.filter(function(x) { return x.vote === 1; }).length;
  var sellCount = votes.filter(function(x) { return x.vote === -1; }).length;
  var neutCount = votes.filter(function(x) { return x.vote === 0; }).length;
  var score = buyCount - sellCount;
  var verdict, vcls;
  if (score >= 4)       { verdict = 'STRONG BUY'; vcls = 'c-sb'; }
  else if (score >= 2)  { verdict = 'BUY';        vcls = 'c-b'; }
  else if (score >= -1) { verdict = 'HOLD';       vcls = 'c-h'; }
  else if (score >= -3) { verdict = 'SELL';       vcls = 'c-s'; }
  else                  { verdict = 'STRONG SELL'; vcls = 'c-ss'; }

  var rows = votes.map(function(v) {
    var arrow = v.vote === 1 ? '<span class="consensus-vote pos">\u25B2</span>' : v.vote === -1 ? '<span class="consensus-vote neg">\u25BC</span>' : '<span class="consensus-vote neutral">\u2014</span>';
    return '<div class="consensus-row">' +
      '<span class="consensus-name">' + v.name + '</span>' +
      '<span class="tech-sig ' + v.cls + '" style="font-size:10px;padding:2px 8px;margin:0">' + v.label + '</span>' +
      '<span class="consensus-detail">' + v.detail + '</span>' +
      arrow +
    '</div>';
  }).join('');

  return '<div class="consensus-wrap">' +
    '<div class="consensus-verdict">' +
      '<div class="consensus-badge ' + vcls + '">' + verdict + '</div>' +
      '<div class="consensus-counts">' +
        '<span class="pos">\u25B2 ' + buyCount + ' Beli</span>' +
        '<span class="neutral">\u2014 ' + neutCount + ' Netral</span>' +
        '<span class="neg">\u25BC ' + sellCount + ' Jual</span>' +
      '</div>' +
      '<div style="font-size:10px;color:var(--text-secondary);margin-top:2px">' + votes.length + ' indikator</div>' +
    '</div>' +
    '<div class="consensus-list">' + rows + '</div>' +
  '</div>';
}

function renderTechnical(mb, rsi, sma, rvol) {
  if (!mb && !rsi && !sma && !rvol) return '<p class="no-data">Data historis tidak cukup.</p>';
  var cards = [];

  if (mb) {
    var m = mb.macd, b = mb.bb;
    var sc = { bullish: 'sig-bullish', bearish: 'sig-bearish', overbought: 'sig-overbought', oversold: 'sig-oversold', netral: 'sig-netral' };
    var ms = (m.signal_label || '').toLowerCase();
    var bs = (b.signal || '').toLowerCase();
    var cross = m.cross ? '<div class="tech-sig ' + (m.cross.includes('GOLDEN') ? 'sig-golden' : 'sig-death') + '" style="margin-top:6px;font-size:10px;">' + m.cross + '</div>' : '';

    cards.push('<div class="tech-card">' +
      '<div class="tech-card-title">MACD (12,26,9)</div>' +
      '<div class="tech-sig ' + (sc[ms] || 'sig-netral') + '">' + m.signal_label + '</div>' + cross +
      '<div class="tech-row"><span class="tech-row-label">MACD Line</span><span>' + m.line + '</span></div>' +
      '<div class="tech-row"><span class="tech-row-label">Signal Line</span><span>' + m.signal + '</span></div>' +
      '<div class="tech-row"><span class="tech-row-label">Histogram</span><span class="' + (m.hist > 0 ? 'pos' : 'neg') + '">' + m.hist + '</span></div>' +
    '</div>');

    cards.push('<div class="tech-card">' +
      '<div class="tech-card-title">Bollinger Bands (20,2)</div>' +
      '<div class="tech-sig ' + (sc[bs] || 'sig-netral') + '">' + b.signal + '</div>' +
      '<div class="tech-row"><span class="tech-row-label">Upper Band</span><span class="neg">Rp ' + b.upper.toLocaleString('id') + '</span></div>' +
      '<div class="tech-row"><span class="tech-row-label">Middle (SMA20)</span><span>Rp ' + b.mid.toLocaleString('id') + '</span></div>' +
      '<div class="tech-row"><span class="tech-row-label">Lower Band</span><span class="pos">Rp ' + b.lower.toLocaleString('id') + '</span></div>' +
      '<div class="tech-row"><span class="tech-row-label">%B Position</span><span>' + (b.pct_b * 100).toFixed(0) + '%</span></div>' +
      '<div class="tech-row"><span class="tech-row-label">Bandwidth</span><span>' + (b.bandwidth != null ? b.bandwidth : '\u2014') + '</span></div>' +
      (b.squeeze ? '<div class="tech-row"><span class="tech-row-label">Squeeze</span><span class="badge bb">ACTIVE</span></div>' : '') +
    '</div>');
  }

  if (rsi) {
    var rsiColor = rsi.value > 70 ? 'var(--warn)' : rsi.value < 30 ? 'var(--info)' : 'var(--pos)';
    var rsiSigCls = rsi.signal === 'OVERBOUGHT' ? 'sig-overbought' : rsi.signal === 'OVERSOLD' ? 'sig-oversold' : 'sig-netral';
    cards.push('<div class="tech-card">' +
      '<div class="tech-card-title">RSI (14)</div>' +
      '<div class="tech-sig ' + rsiSigCls + '">' + rsi.signal + '</div>' +
      '<div style="font-family:\'JetBrains Mono\',monospace;font-size:28px;font-weight:600;color:' + rsiColor + ';margin:6px 0;">' + rsi.value + '</div>' +
      '<div style="margin:10px 0;">' +
        '<div style="height:8px;border-radius:4px;overflow:hidden;background:rgba(255,255,255,0.04);">' +
          '<div style="height:100%;border-radius:4px;width:' + rsi.value + '%;background:' + rsiColor + ';transition:width .5s;"></div>' +
        '</div>' +
        '<div style="display:flex;justify-content:space-between;font-family:\'JetBrains Mono\',monospace;font-size:8px;color:var(--text-secondary);margin-top:3px;">' +
          '<span style="color:var(--info);">0 Oversold</span><span>30</span><span>50</span><span>70</span><span style="color:var(--warn);">100 Overbought</span>' +
        '</div>' +
      '</div>' +
    '</div>');
  }

  if (sma) {
    var gcls = sma.golden_cross === true ? 'sig-golden' : sma.golden_cross === false ? 'sig-death' : 'sig-netral';
    var glabel = sma.golden_cross === true ? 'Golden Cross' : sma.golden_cross === false ? 'Death Cross' : 'N/A';
    cards.push('<div class="tech-card">' +
      '<div class="tech-card-title">Moving Averages</div>' +
      '<div class="tech-sig ' + gcls + '" style="margin-bottom:10px;">' + glabel + '</div>' +
      '<div class="tech-row"><span class="tech-row-label">Harga</span><span>Rp ' + sma.price.toLocaleString('id') + '</span></div>' +
      '<div class="tech-row"><span class="tech-row-label">EMA 20</span><span class="' + (sma.price > sma.ema20 ? 'pos' : 'neg') + '">Rp ' + sma.ema20.toLocaleString('id') + '</span></div>' +
      '<div class="tech-row"><span class="tech-row-label">SMA 50</span><span class="' + (sma.above_sma50 ? 'pos' : 'neg') + '">Rp ' + sma.sma50.toLocaleString('id') + '</span></div>' +
      '<div class="tech-row"><span class="tech-row-label">SMA 200</span><span>' + (sma.sma200 ? 'Rp ' + sma.sma200.toLocaleString('id') : '<span class="na">\u2014</span>') + '</span></div>' +
    '</div>');
  }

  if (rvol) {
    var rvsc = rvol.signal === 'SANGAT TINGGI' ? 'bg' : rvol.signal === 'TINGGI' ? 'by' : rvol.signal === 'NORMAL' ? 'bb' : 'br';
    var barW = Math.min(100, rvol.rvol / 4 * 100);
    cards.push('<div class="tech-card">' +
      '<div class="tech-card-title">Relative Volume</div>' +
      '<div style="display:flex;align-items:center;gap:12px;margin-bottom:10px;">' +
        '<div style="font-family:\'JetBrains Mono\',monospace;font-size:32px;font-weight:600;line-height:1;" class="' + (rvol.rvol >= 2 ? 'pos' : rvol.rvol < 0.7 ? 'neg' : '') + '">' + rvol.rvol + 'x</div>' +
        '<span class="badge ' + rvsc + '">' + rvol.signal + '</span>' +
      '</div>' +
      '<div style="height:6px;border-radius:3px;overflow:hidden;background:rgba(255,255,255,0.04);margin:8px 0;">' +
        '<div style="height:100%;border-radius:3px;width:' + barW + '%;background:linear-gradient(90deg,var(--info),var(--pos));transition:width .5s;"></div>' +
      '</div>' +
      '<div class="tech-row"><span class="tech-row-label">Volume Hari Ini</span><span>' + (rvol.today / 1e6).toFixed(2) + 'M</span></div>' +
      '<div class="tech-row"><span class="tech-row-label">Avg 20 Hari</span><span>' + (rvol.avg / 1e6).toFixed(2) + 'M</span></div>' +
    '</div>');
  }

  return '<div class="tech-grid">' + cards.join('') + '</div>';
}

function renderFundamentalTabs(d) {
  var i = d.info;

  var valRows = [
    ['P/E Ratio (Trailing)', i.trailingPE, R.pe(i.trailingPE)],
    ['P/E Ratio (Forward)',  i.forwardPE,  R.pe(i.forwardPE)],
    ['Price to Book (P/BV)', i.priceToBook, R.pb(i.priceToBook)],
    ['Price to Sales',       i.priceToSalesTrailing12Months, ''],
    ['PEG Ratio',            i.pegRatio, '']
  ];

  var profRows = [
    ['Return on Equity (ROE)',  i.returnOnEquity,   R.roe(i.returnOnEquity)],
    ['Return on Assets (ROA)',  i.returnOnAssets,   R.roa(i.returnOnAssets)],
    ['Net Profit Margin',       i.profitMargins,    R.npm(i.profitMargins)],
    ['Operating Margin',        i.operatingMargins, ''],
    ['Revenue Growth YoY',      i.revenueGrowth,    ''],
    ['Earnings Growth YoY',     i.earningsGrowth,   '']
  ];

  var healthRows = [
    ['Current Ratio',   i.currentRatio,     R.cr(i.currentRatio)],
    ['Quick Ratio',     i.quickRatio,        ''],
    ['Debt to Equity',  i.debtToEquity,      R.de(i.debtToEquity)],
    ['Total Debt',      i.totalDebt,         ''],
    ['Total Cash',      i.totalCash,         ''],
    ['Free Cash Flow',  i.freeCashflow,      ''],
    ['Operating CF',    i.operatingCashflow, '']
  ];

  var divRows = [
    ['Dividend Yield',   i.dividendYield,  R.dy(i.dividendYield)],
    ['Dividend Rate',    i.dividendRate,    ''],
    ['Payout Ratio',     i.payoutRatio,     ''],
    ['Ex-Dividend Date', i.exDividendDate,  ''],
    ['Last Div. Value',  i.lastDividendValue, '']
  ];

  var tabsId = 'ftabs-' + Math.random().toString(36).slice(2, 8);
  return '<div id="' + tabsId + '">' +
    '<div class="tabs">' +
      '<div class="tab active" data-panel="' + tabsId + '-val">Valuasi</div>' +
      '<div class="tab" data-panel="' + tabsId + '-prof">Profitabilitas</div>' +
      '<div class="tab" data-panel="' + tabsId + '-health">Kesehatan</div>' +
      '<div class="tab" data-panel="' + tabsId + '-div">Dividen</div>' +
    '</div>' +
    '<div class="tab-content">' +
      '<div class="tab-panel active" id="' + tabsId + '-val">' + dtable(valRows) + '</div>' +
      '<div class="tab-panel" id="' + tabsId + '-prof">' + dtable(profRows) + '</div>' +
      '<div class="tab-panel" id="' + tabsId + '-health">' + dtable(healthRows) + '</div>' +
      '<div class="tab-panel" id="' + tabsId + '-div">' + dtable(divRows) + '</div>' +
    '</div>' +
  '</div>';
}

function renderFinancialTabs(d) {
  var IS = [['Total Revenue', 'Revenue'], ['Cost Of Revenue', 'Beban Pendapatan'],
    ['Gross Profit', 'Laba Kotor'], ['Operating Income', 'Laba Operasi'],
    ['EBITDA', 'EBITDA'], ['Net Income', 'Laba Bersih'], ['Diluted EPS', 'EPS Diluted']];
  var BS = [['Total Assets', 'Total Aset'],
    ['Total Liabilities Net Minority Interest', 'Total Liabilitas'],
    ['Stockholders Equity', 'Total Ekuitas'],
    ['Cash And Cash Equivalents', 'Kas & Setara'],
    ['Total Debt', 'Total Utang'], ['Net Debt', 'Net Debt'],
    ['Inventory', 'Persediaan'], ['Accounts Receivable', 'Piutang Usaha']];
  var CF = [['Operating Cash Flow', 'Arus Kas Operasi'],
    ['Investing Cash Flow', 'Arus Kas Investasi'],
    ['Financing Cash Flow', 'Arus Kas Pendanaan'],
    ['Free Cash Flow', 'Free Cash Flow'],
    ['Capital Expenditure', 'Capex'], ['Dividends Paid', 'Dividen Dibayar']];
  var QT = [['Total Revenue', 'Revenue'], ['Gross Profit', 'Laba Kotor'],
    ['Operating Income', 'Laba Operasi'], ['Net Income', 'Laba Bersih']];

  var tabsId = 'fintabs-' + Math.random().toString(36).slice(2, 8);
  return '<div id="' + tabsId + '">' +
    '<div class="tabs">' +
      '<div class="tab active" data-panel="' + tabsId + '-is">Income</div>' +
      '<div class="tab" data-panel="' + tabsId + '-bs">Balance Sheet</div>' +
      '<div class="tab" data-panel="' + tabsId + '-cf">Cash Flow</div>' +
      '<div class="tab" data-panel="' + tabsId + '-qt">Quarterly</div>' +
    '</div>' +
    '<div class="tab-content">' +
      '<div class="tab-panel active" id="' + tabsId + '-is">' + ftable(d.financials, IS) + '</div>' +
      '<div class="tab-panel" id="' + tabsId + '-bs">' + ftable(d.balance_sheet, BS) + '</div>' +
      '<div class="tab-panel" id="' + tabsId + '-cf">' + ftable(d.cashflow, CF) + '</div>' +
      '<div class="tab-panel" id="' + tabsId + '-qt">' + ftable(d.quarterly, QT) + '</div>' +
    '</div>' +
  '</div>';
}

function renderPiotroski(p) {
  if (!p) return '<p class="no-data">Data laporan keuangan tidak cukup untuk F-Score.</p>';
  var rCls = p.rating === 'KUAT' ? 'bg' : p.rating === 'CUKUP' ? 'by' : 'br';
  var trendBadge = '';
  if (p.trend) {
    var tCls = p.trend === 'NAIK' ? 'trend-up' : p.trend === 'TURUN' ? 'trend-down' : 'trend-stable';
    trendBadge = ' <span class="score-trend ' + tCls + '">' + p.trend + '</span>';
  }

  return '<div style="padding:16px 20px 8px;display:flex;align-items:center;gap:16px;">' +
    '<div class="score-num ' + (p.score >= 7 ? 'pos' : p.score >= 5 ? '' : 'neg') + '">' + p.score + '<span style="font-size:16px;color:var(--text-secondary)">/9</span></div>' +
    '<div>' +
      '<span class="score-badge badge ' + rCls + '">' + p.rating + '</span>' + trendBadge +
      '<div style="font-size:10px;color:var(--text-secondary);margin-top:6px;">Piotroski F-Score</div>' +
    '</div>' +
  '</div>' +
  '<div class="fscore-grid">' +
    Object.entries(p.details).map(function(e) {
      var f = e[1];
      return '<div class="fscore-item">' +
        '<div class="fscore-check ' + (f.pass ? 'fscore-pass' : 'fscore-fail') + '">' + (f.pass ? '\u2713' : '\u2717') + '</div>' +
        '<span class="fscore-label">' + f.label + '</span>' +
        '<span class="fscore-val">' + f.value + '</span>' +
      '</div>';
    }).join('') +
  '</div>';
}

function renderAltman(a) {
  if (!a) return '<p class="no-data">Data balance sheet tidak cukup untuk Altman Z-Score.</p>';
  var zCls = a.zone === 'AMAN' ? 'bg' : a.zone === 'WASPADA' ? 'by' : 'br';
  var sCls = a.zone === 'AMAN' ? 'pos' : a.zone === 'BAHAYA' ? 'neg' : '';
  return '<div class="altman-wrap">' +
    '<div>' +
      '<div class="altman-score ' + sCls + '">' + a.z_score + '</div>' +
      '<div class="score-badge badge ' + zCls + '" style="margin-top:8px;display:inline-block;">' + a.zone + '</div>' +
      '<div style="font-size:10px;color:var(--text-secondary);margin-top:6px;">' + a.desc + '</div>' +
    '</div>' +
    '<div class="altman-gauge">' +
      '<div class="altman-scale"><div class="altman-red"></div><div class="altman-yellow"></div><div class="altman-green"></div></div>' +
      '<div class="altman-labels"><span>0 Bahaya</span><span>1.1</span><span>2.6</span><span>5+ Aman</span></div>' +
      '<div style="margin-top:12px">' +
        Object.entries(a.components).map(function(e) {
          return '<div class="tech-row"><span class="tech-row-label">' + e[0] + '</span><span>' + e[1] + '</span></div>';
        }).join('') +
      '</div>' +
    '</div>' +
  '</div>';
}

function renderRiskAdj(fcf, sortino, sharpe) {
  var rows = [];
  if (fcf) {
    rows.push(['FCF Yield', fcf.yield * 100, fcf.signal === 'MENARIK' ? '\uD83D\uDFE2 Menarik' : fcf.signal === 'NETRAL' ? '\uD83D\uDFE1 Netral' : fcf.signal === 'RENDAH' ? '\uD83D\uDFE0 Rendah' : '\uD83D\uDD34 Negatif']);
    rows.push(['Free Cash Flow', fcf.fcf, '']);
  }
  if (sortino != null) rows.push(['Sortino Ratio', sortino, sortino >= 1 ? '\uD83D\uDFE2 Excellent' : sortino >= 0.5 ? '\uD83D\uDFE1 Bagus' : sortino >= 0 ? '\uD83D\uDFE0 Rendah' : '\uD83D\uDD34 Negatif']);
  if (sharpe != null)  rows.push(['Sharpe Ratio',  sharpe,  sharpe >= 1 ? '\uD83D\uDFE2 Excellent' : sharpe >= 0.5 ? '\uD83D\uDFE1 Bagus' : sharpe >= 0 ? '\uD83D\uDFE0 Rendah' : '\uD83D\uDD34 Negatif']);
  return rows.length ? dtable(rows) : '<p class="no-data">Data tidak tersedia.</p>';
}

function render(d) {
  var i = d.info;
  var ticker = d.ticker;
  var html = '';

  html += renderHero(d);
  html += sec('\uD83D\uDCCC', 'KEY METRICS', renderMetrics(d), true, true);

  html += '<div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;">';
  html += sec('\uD83C\uDFAF', 'TECHNICAL CONSENSUS', renderConsensus(d), true, true);
  html += sec('\uD83C\uDFC6', 'COMPOSITE SCORE', renderComposite(d.composite), true, true);
  html += sec('\uD83D\uDCCA', 'PIOTROSKI F-SCORE', renderPiotroski(d.piotroski), true, false);
  html += sec('\u26A0\uFE0F', 'ALTMAN Z-SCORE', renderAltman(d.altman), true, false);
  html += '</div>';

  html += sec('\uD83D\uDCBE', 'TECHNICAL \u2014 MACD, BB, RSI, MA & RVOL', renderTechnical(d.macd_bb, d.rsi, d.sma, d.rvol), true, true);
  html += sec('\uD83D\uDC8E', 'RISK-ADJUSTED RETURN', renderRiskAdj(d.fcf_yield, d.sortino, d.sharpe), true, false);
  html += sec('\uD83D\uDCB0', 'FUNDAMENTAL', renderFundamentalTabs(d), true, true);
  html += sec('\uD83D\uDCCB', 'FINANCIAL STATEMENTS', renderFinancialTabs(d), true, true);

  var desc = i.longBusinessSummary
    ? '<div style="padding:20px;font-size:12px;line-height:1.9;color:var(--text-secondary);">' + i.longBusinessSummary.substring(0, 600) + (i.longBusinessSummary.length > 600 ? '...' : '') + '</div>'
    : '';
  if (desc) {
    html += sec('\uD83C\uDFE2', 'PROFIL PERUSAHAAN', desc, false, true);
  }

  document.getElementById('result').innerHTML = html;
  show('result');

  initTabs();

  document.getElementById('result').scrollIntoView({ behavior: 'smooth', block: 'start' });

  fetchAIInsight(ticker, 'valuasi', {
    pe: i.trailingPE, pb: i.priceToBook, peg: i.pegRatio, ps: i.priceToSalesTrailing12Months
  });

  fetchAIInsight(ticker, 'composite', {
    score: d.composite ? d.composite.final : '',
    signal: d.composite ? d.composite.signal : '',
    fund: d.composite ? d.composite.components.Fundamental : '',
    tech: d.composite ? d.composite.components.Technical : '',
    risk: d.composite ? d.composite.components.Risk : '',
    mom: d.composite ? d.composite.components.Momentum : '',
    sent: d.composite ? d.composite.components.Sentiment : ''
  });

  fetchAIInsight(ticker, 'scoring', {
    fscore: d.piotroski ? d.piotroski.score : '',
    frating: d.piotroski ? d.piotroski.rating : '',
    zscore: d.altman ? d.altman.z_score : '',
    zzone: d.altman ? d.altman.zone : ''
  });

  fetchAIInsight(ticker, 'consensus', {
    buy_count: d.composite ? 'TODO' : '0',
    neut_count: '0',
    sell_count: '0',
    verdict: 'N/A',
    details: 'See consensus section'
  });

  fetchAIInsight(ticker, 'technical', {
    macd_signal: d.macd_bb ? d.macd_bb.macd.signal_label : '',
    rsi_val: d.rsi ? d.rsi.value : '',
    rsi_signal: d.rsi ? d.rsi.signal : '',
    bb_signal: d.macd_bb ? d.macd_bb.bb.signal : '',
    bb_pct: d.macd_bb ? (d.macd_bb.bb.pct_b * 100).toFixed(0) : '',
    bb_bw: d.macd_bb ? d.macd_bb.bb.bandwidth : '',
    sma50: d.sma ? d.sma.sma50 : '',
    gc: d.sma ? (d.sma.golden_cross ? 'Yes' : 'No') : ''
  });
}
