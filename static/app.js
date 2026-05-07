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
    try {
      render(d);
    } catch (renderErr) {
      showErr('Render error: ' + (renderErr && renderErr.message ? renderErr.message : String(renderErr)));
      console.error('render() threw:', renderErr);
    }
  } catch (e) {
    hide('loading');
    document.getElementById('search-btn').disabled = false;
    showErr('Koneksi gagal atau limit tercapai. Tunggu beberapa saat.');
    console.error('fetch/parse error:', e);
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

function sec(icon, title, body, open) {
  var id = 's' + Math.random().toString(36).slice(2, 8);
  var iconHtml = icon ? '<div class="section-icon">' + icon + '</div>' : '';
  return '<div class="section glass' + (open ? '' : ' collapsed') + '" id="' + id + '">' +
    '<div class="section-header" onclick="document.getElementById(\'' + id + '\').classList.toggle(\'collapsed\')">' +
      iconHtml +
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

function fetchAllAIInsights(ticker, fullData) {
  var SECTIONS = ['key_metrics', 'valuasi', 'technical', 'piotroski', 'altman', 'composite', 'consensus', 'key_levels'];
  var cacheKey = 'ai_all_' + ticker;
  var cached = sessionStorage.getItem(cacheKey);

  var placeholderIds = {};
  SECTIONS.forEach(function(section) {
    var pid = 'ai-' + section + '-' + Math.random().toString(36).slice(2, 8);
    placeholderIds[section] = pid;
    insertAIBox(section, '<div class="ai-insight" id="' + pid + '"><div class="ai-label">\uD83E\uDD16 AI INSIGHT</div><div class="ai-text ai-loading">Memuat insight...</div></div>');
  });

  if (cached) {
    try {
      var insights = JSON.parse(cached);
      SECTIONS.forEach(function(section) {
        var el = document.getElementById(placeholderIds[section]);
        if (!el) return;
        if (insights[section]) {
          el.querySelector('.ai-text').classList.remove('ai-loading');
          typeText(el.querySelector('.ai-text'), insights[section]);
        } else {
          el.style.display = 'none';
        }
      });
      return;
    } catch(e) { sessionStorage.removeItem(cacheKey); }
  }

  fetch('/api/ai-insights', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ ticker: ticker, data: fullData })
  }).then(function(r) { return r.json(); }).then(function(res) {
    var insights = res.insights || {};
    if (Object.keys(insights).length > 0) {
      sessionStorage.setItem(cacheKey, JSON.stringify(insights));
    }
    SECTIONS.forEach(function(section) {
      var el = document.getElementById(placeholderIds[section]);
      if (!el) return;
      if (insights[section]) {
        el.querySelector('.ai-text').classList.remove('ai-loading');
        typeText(el.querySelector('.ai-text'), insights[section]);
      } else {
        el.style.display = 'none';
      }
    });
  }).catch(function() {
    SECTIONS.forEach(function(section) {
      var el = document.getElementById(placeholderIds[section]);
      if (el) el.style.display = 'none';
    });
  });
}

function insertAIBox(section, html) {
  function byTitle(keyword) {
    var sections = document.querySelectorAll('.section');
    for (var i = 0; i < sections.length; i++) {
      var t = sections[i].querySelector('.section-title');
      if (t && t.textContent.indexOf(keyword) >= 0) {
        sections[i].querySelector('.section-body').insertAdjacentHTML('beforeend', html);
        return;
      }
    }
  }
  var targets = {
    'key_metrics':  function() { byTitle('KEY METRICS'); },
    'valuasi':      function() {
      var panels = document.querySelectorAll('.tab-panel');
      if (panels.length > 0) panels[0].insertAdjacentHTML('beforeend', html);
    },
    'composite':    function() { byTitle('COMPOSITE'); },
    'consensus':    function() { byTitle('CONSENSUS'); },
    'piotroski':    function() { byTitle('PIOTROSKI'); },
    'altman':       function() { byTitle('ALTMAN'); },
    'technical':    function() { byTitle('TEKNIKAL'); },
    'key_levels':   function() { byTitle('KEY LEVEL'); },
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

function renderTechnical(mb, rsi, sma, rvol, adx, avwap) {
  if (!mb && !rsi && !sma && !rvol && !adx && !avwap) return '<p class="no-data">Data historis tidak cukup.</p>';
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
      '<div class="tech-row"><span class="tech-row-label">Upper Band</span><span class="neg">' + (b.upper != null ? 'Rp ' + b.upper.toLocaleString('id') : '—') + '</span></div>' +
      '<div class="tech-row"><span class="tech-row-label">Middle (SMA20)</span><span>' + (b.mid != null ? 'Rp ' + b.mid.toLocaleString('id') : '—') + '</span></div>' +
      '<div class="tech-row"><span class="tech-row-label">Lower Band</span><span class="pos">' + (b.lower != null ? 'Rp ' + b.lower.toLocaleString('id') : '—') + '</span></div>' +
      '<div class="tech-row"><span class="tech-row-label">%B Position</span><span>' + (b.pct_b != null ? (b.pct_b * 100).toFixed(0) + '%' : '—') + '</span></div>' +
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
    var glabel = sma.golden_cross === true ? 'Golden Cross (EMA50>EMA200)' : sma.golden_cross === false ? 'Death Cross (EMA50<EMA200)' : 'N/A';
    var fmtEma = function(v) { return v ? 'Rp ' + v.toLocaleString('id') : '<span class="na">\u2014</span>'; };
    cards.push('<div class="tech-card">' +
      '<div class="tech-card-title">EMA \u2014 Moving Averages</div>' +
      '<div class="tech-sig ' + gcls + '" style="margin-bottom:10px;">' + glabel + '</div>' +
      '<div class="tech-row"><span class="tech-row-label">Harga</span><span>' + (sma.price != null ? 'Rp ' + sma.price.toLocaleString('id') : '—') + '</span></div>' +
      '<div class="tech-row"><span class="tech-row-label">EMA 9 <span style="font-size:9px;opacity:.6;">(short)</span></span><span class="' + (sma.price > sma.ema9 ? 'pos' : 'neg') + '">' + fmtEma(sma.ema9) + '</span></div>' +
      '<div class="tech-row"><span class="tech-row-label">EMA 21 <span style="font-size:9px;opacity:.6;">(entry)</span></span><span class="' + (sma.price > sma.ema21 ? 'pos' : 'neg') + '">' + fmtEma(sma.ema21) + '</span></div>' +
      '<div class="tech-row"><span class="tech-row-label">EMA 50 <span style="font-size:9px;opacity:.6;">(stoploss)</span></span><span class="' + (sma.above_ema50 ? 'pos' : 'neg') + '">' + fmtEma(sma.ema50) + '</span></div>' +
      '<div class="tech-row"><span class="tech-row-label">EMA 200 <span style="font-size:9px;opacity:.6;">(trend)</span></span><span class="' + (sma.above_ema200 === true ? 'pos' : sma.above_ema200 === false ? 'neg' : '') + '">' + fmtEma(sma.ema200) + '</span></div>' +
    '</div>');
  }

  if (avwap) {
    var avwapSigCls = avwap.signal === 'BULLISH' ? 'sig-bullish' : 'sig-bearish';
    var avwapDiff = avwap.pct_diff != null ? (avwap.pct_diff > 0 ? '+' + avwap.pct_diff + '%' : avwap.pct_diff + '%') : '—';
    cards.push('<div class="tech-card">' +
      '<div class="tech-card-title">AVWAP <span style="font-size:9px;opacity:.6;">(Anchored VWAP)</span></div>' +
      '<div class="tech-sig ' + avwapSigCls + '">' + avwap.signal + '</div>' +
      '<div class="tech-row"><span class="tech-row-label">AVWAP</span><span>' + (avwap.value != null ? 'Rp ' + avwap.value.toLocaleString('id') : '—') + '</span></div>' +
      '<div class="tech-row"><span class="tech-row-label">Harga vs AVWAP</span><span class="' + (avwap.pct_diff != null && avwap.pct_diff > 0 ? 'pos' : 'neg') + '">' + avwapDiff + '</span></div>' +
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

  if (adx) {
    var adxStrCls = adx.strength === 'STRONG' ? 'sig-bullish' : adx.strength === 'MODERATE' ? 'sig-netral' : 'sig-bearish';
    var adxDirCls = adx.direction === 'BULLISH' ? 'pos' : 'neg';
    var adxBarW = Math.min(100, adx.adx / 50 * 100);
    cards.push('<div class="tech-card">' +
      '<div class="tech-card-title">ADX (14) — Trend Strength</div>' +
      '<div class="tech-sig ' + adxStrCls + '">' + adx.strength + '</div>' +
      '<div style="font-family:\'JetBrains Mono\',monospace;font-size:28px;font-weight:600;line-height:1;margin:6px 0;" class="' + adxStrCls.replace('sig-', '') + '">' + adx.adx + '</div>' +
      '<div style="height:6px;border-radius:3px;overflow:hidden;background:rgba(255,255,255,0.04);margin:8px 0;">' +
        '<div style="height:100%;border-radius:3px;width:' + adxBarW + '%;background:linear-gradient(90deg,var(--info),var(--warn));transition:width .5s;"></div>' +
      '</div>' +
      '<div class="tech-row"><span class="tech-row-label">Arah Tren</span><span class="' + adxDirCls + '">' + adx.direction + '</span></div>' +
      '<div class="tech-row"><span class="tech-row-label">+DI (bullish)</span><span class="pos">' + adx.plus_di + '</span></div>' +
      '<div class="tech-row"><span class="tech-row-label">-DI (bearish)</span><span class="neg">' + adx.minus_di + '</span></div>' +
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

function rpFmt(x) {
  if (x == null) return '—';
  var s = x % 1 === 0 ? x.toLocaleString('id') : x.toFixed(1).replace('.', ',');
  return 'Rp ' + s;
}

function pctFmt(x, plus) {
  if (x == null) return '—';
  return (plus && x > 0 ? '+' : '') + x.toFixed(1) + '%';
}

function renderKeyLevels(kl) {
  if (!kl) return '<p class="no-data">Data tidak tersedia.</p>';
  var cur = kl.current;
  var min = kl.s3, max = kl.r3, range = max - min;

  function pct(v) {
    var d = ((v - cur) / cur * 100);
    return (d >= 0 ? '+' : '') + d.toFixed(1) + '%';
  }
  function bar(v, type) {
    var w = range > 0 ? Math.min(100, Math.abs(v - cur) / range * 80 + 10) : 50;
    var color = type === 'r' ? 'var(--pos)' : type === 's' ? 'var(--neg)' : 'var(--accent)';
    return '<div style="flex:1;height:4px;border-radius:2px;background:rgba(255,255,255,0.06);overflow:hidden;">' +
      '<div style="height:100%;border-radius:2px;width:' + w + '%;background:' + color + ';opacity:0.5;"></div></div>';
  }
  function row(label, val, type, bold) {
    var isCur = type === 'cur';
    return '<div style="display:flex;align-items:center;gap:10px;padding:' + (isCur ? '10px 16px' : '6px 16px') + ';' +
      (isCur ? 'background:var(--badge-info-bg);border-radius:6px;margin:4px 0;' : '') + '">' +
      '<span style="font-family:\'JetBrains Mono\',monospace;font-size:10px;color:var(--text-secondary);width:42px;text-align:right;">' + label + '</span>' +
      (isCur ? '' : bar(val, type)) +
      '<span style="font-family:\'JetBrains Mono\',monospace;font-size:' + (isCur ? '14px' : '12px') + ';font-weight:' + (isCur ? '700' : '400') + ';color:' +
        (isCur ? 'var(--accent)' : type === 'r' ? 'var(--pos)' : type === 's' ? 'var(--neg)' : 'var(--text-secondary)') + ';min-width:90px;">' +
        rpFmt(val) + '</span>' +
      '<span style="font-family:\'JetBrains Mono\',monospace;font-size:10px;color:var(--text-secondary);min-width:52px;">' +
        (isCur ? '◉ CURRENT' : pct(val)) + '</span>' +
    '</div>';
  }

  return '<div style="padding:8px 0;">' +
    row('R3', kl.r3, 'r') + row('R2', kl.r2, 'r') + row('R1', kl.r1, 'r') +
    row('CURRENT', cur, 'cur') +
    row('S1', kl.s1, 's') + row('S2', kl.s2, 's') + row('S3', kl.s3, 's') +
  '</div>';
}

function renderOutlook(ol) {
  if (!ol) return '<p class="no-data">Data tidak tersedia.</p>';
  var actionBadge = ol.action_cls === 'bull' ? 'bg' : ol.action_cls === 'bear' ? 'br' : 'by';
  var actionColor = ol.action_cls === 'bull' ? 'var(--pos)' : ol.action_cls === 'bear' ? 'var(--neg)' : 'var(--warn)';

  function scenario(icon, label, color, text) {
    return '<div style="display:flex;align-items:flex-start;gap:10px;padding:10px 0;border-bottom:1px solid var(--border);">' +
      '<span style="font-size:13px;line-height:1.4;flex-shrink:0;">' + icon + '</span>' +
      '<div>' +
        '<div style="font-size:11px;font-weight:700;color:' + color + ';margin-bottom:2px;">' + label + '</div>' +
        '<div style="font-size:11px;color:var(--text-secondary);line-height:1.5;">' + text + '</div>' +
      '</div>' +
    '</div>';
  }

  var left = '<div style="flex:1;min-width:0;">' +
    scenario('🟢', 'BULL', 'var(--pos)', ol.bull) +
    scenario('🔴', 'BEAR', 'var(--neg)', ol.bear) +
    '<div style="display:flex;align-items:center;gap:10px;padding:10px 0;">' +
      '<span style="font-size:13px;">⚡</span>' +
      '<div>' +
        '<div style="font-size:11px;font-weight:700;color:' + actionColor + ';margin-bottom:4px;">AKSI</div>' +
        '<span class="badge ' + actionBadge + '">' + ol.action + '</span>' +
        '<span style="font-size:11px;color:var(--text-secondary);margin-left:8px;">di zona ' + rpFmt(ol.entry_low) + ' – ' + rpFmt(ol.entry_high) + '</span>' +
      '</div>' +
    '</div>' +
  '</div>';

  function drow(label, val, note, valColor) {
    return '<div style="display:flex;justify-content:space-between;align-items:center;padding:8px 0;border-bottom:1px solid var(--border);">' +
      '<span class="td-label" style="width:auto;margin-right:8px;">' + label + '</span>' +
      '<div style="text-align:right;">' +
        '<span style="font-family:\'JetBrains Mono\',monospace;font-size:12px;font-weight:600;color:' + (valColor || 'var(--text)') + ';">' + val + '</span>' +
        (note ? '<span style="font-size:10px;color:var(--text-secondary);margin-left:6px;">' + note + '</span>' : '') +
      '</div>' +
    '</div>';
  }
  var rrColor = ol.rr_ratio >= 2 ? 'var(--pos)' : ol.rr_ratio >= 1 ? 'var(--warn)' : 'var(--neg)';
  var right = '<div style="min-width:200px;padding-left:24px;border-left:1px solid var(--border);">' +
    drow('Entry', rpFmt(ol.entry_low) + ' – ' + rpFmt(ol.entry_high)) +
    drow('Stop Loss', rpFmt(ol.stop_loss), pctFmt(-ol.sl_pct), 'var(--neg)') +
    drow('Target 1',  rpFmt(ol.target1),  pctFmt(ol.t1_pct, true), 'var(--pos)') +
    drow('Target 2',  rpFmt(ol.target2),  pctFmt(ol.t2_pct, true), 'var(--pos)') +
    '<div style="display:flex;justify-content:space-between;align-items:center;padding:8px 0;">' +
      '<span class="td-label" style="width:auto;">R/R Ratio</span>' +
      '<span style="font-family:\'JetBrains Mono\',monospace;font-size:14px;font-weight:700;color:' + rrColor + ';">1 : ' + ol.rr_ratio + '</span>' +
    '</div>' +
  '</div>';

  return '<div style="display:flex;gap:0;padding:4px 20px 4px;">' + left + right + '</div>';
}

function renderSignalStrip(d) {
  var votes = [];
  if (d.macd_bb) {
    var msig = d.macd_bb.macd.signal_label;
    votes.push({ name: 'MACD', v: msig === 'BULLISH' ? 1 : -1, label: msig });
    var bsig = d.macd_bb.bb.signal;
    var bv = (bsig === 'BULLISH' || bsig === 'OVERSOLD') ? 1 : (bsig === 'BEARISH' || bsig === 'OVERBOUGHT') ? -1 : 0;
    votes.push({ name: 'BB', v: bv, label: bsig });
  }
  if (d.rsi) {
    var rv = d.rsi.signal === 'OVERSOLD' ? 1 : d.rsi.signal === 'OVERBOUGHT' ? -1 : 0;
    votes.push({ name: 'RSI', v: rv, label: String(d.rsi.value) });
  }
  if (d.sma) {
    var sv = d.sma.golden_cross === true ? 1 : d.sma.golden_cross === false ? -1 : 0;
    votes.push({ name: 'EMA', v: sv, label: d.sma.golden_cross === true ? 'GOLDEN' : d.sma.golden_cross === false ? 'DEATH' : 'NETRAL' });
  }
  if (d.adx) {
    var adxv = (d.adx.direction === 'BULLISH' && d.adx.strength !== 'WEAK') ? 1 : (d.adx.direction === 'BEARISH' && d.adx.strength !== 'WEAK') ? -1 : 0;
    votes.push({ name: 'ADX', v: adxv, label: d.adx.strength });
  }
  if (d.piotroski) {
    var pv = d.piotroski.rating === 'KUAT' ? 1 : d.piotroski.rating === 'LEMAH' ? -1 : 0;
    votes.push({ name: 'PIOS', v: pv, label: d.piotroski.score + '/9' });
  }
  if (d.altman) {
    var altv = d.altman.zone === 'AMAN' ? 1 : d.altman.zone === 'BAHAYA' ? -1 : 0;
    votes.push({ name: 'ALTM', v: altv, label: 'Z ' + d.altman.z_score });
  }
  if (d.rvol) {
    var rvolv = (d.rvol.signal === 'SANGAT TINGGI' || d.rvol.signal === 'TINGGI') ? 1 : d.rvol.signal === 'RENDAH' ? -1 : 0;
    votes.push({ name: 'RVOL', v: rvolv, label: d.rvol.rvol + 'x' });
  }

  var buyCount  = votes.filter(function(x) { return x.v === 1; }).length;
  var sellCount = votes.filter(function(x) { return x.v === -1; }).length;
  var neutCount = votes.filter(function(x) { return x.v === 0; }).length;
  var score = buyCount - sellCount;
  var verdict, vcls;
  if (score >= 4)       { verdict = 'BELI KUAT'; vcls = 'c-sb'; }
  else if (score >= 2)  { verdict = 'BELI';       vcls = 'c-b'; }
  else if (score >= -1) { verdict = 'HOLD';       vcls = 'c-h'; }
  else if (score >= -3) { verdict = 'JUAL';       vcls = 'c-s'; }
  else                  { verdict = 'JUAL KUAT';  vcls = 'c-ss'; }

  var c = d.composite;
  var cscore = c ? c.final : null;
  var scoreSection = c ? (
    '<div class="strip-mid">' +
      '<div class="strip-score-row">' +
        '<span class="strip-score-label">COMPOSITE SCORE</span>' +
        '<span class="strip-score-val ' + (cscore >= 70 ? 'pos' : cscore < 35 ? 'neg' : '') + '">' + cscore + '<span style="font-weight:400;opacity:.5">/100</span></span>' +
      '</div>' +
      '<div class="strip-bar-wrap"><div class="strip-bar-fill" style="width:' + cscore + '%"></div></div>' +
      '<div class="strip-signal-label">' + (c.signal || '') + '</div>' +
    '</div>'
  ) : '';

  var quickList = votes.map(function(vt) {
    var arrow = vt.v === 1 ? '<span class="pos">\u25B2</span>' : vt.v === -1 ? '<span class="neg">\u25BC</span>' : '<span class="neutral" style="color:var(--text-secondary)">\u2500</span>';
    return '<div class="strip-quick-row">' +
      '<span class="strip-quick-name">' + vt.name + '</span>' +
      arrow +
      '<span class="strip-quick-val">' + vt.label + '</span>' +
    '</div>';
  }).join('');

  return '<div class="signal-strip glass">' +
    '<div class="strip-verdict">' +
      '<div class="strip-verdict-badge ' + vcls + '">' + verdict + '</div>' +
      '<div class="strip-counts">' +
        '<span class="pos">\u25B2 ' + buyCount + ' Beli</span>' +
        '<span style="color:var(--text-secondary)">\u2500 ' + neutCount + '</span>' +
        '<span class="neg">\u25BC ' + sellCount + ' Jual</span>' +
      '</div>' +
    '</div>' +
    scoreSection +
    '<div class="strip-quick">' + quickList + '</div>' +
  '</div>';
}

function render(d) {
  var i = d.info;
  var ticker = d.ticker;
  var html = '';

  html += renderHero(d);
  html += renderSignalStrip(d);

  html += '<div class="layout-pair">';
  html += sec('', 'KEY LEVELS', renderKeyLevels(d.key_levels), true);
  html += sec('', 'TRADING OUTLOOK', renderOutlook(d.outlook), true);
  html += '</div>';

  html += sec('', 'INDIKATOR TEKNIKAL', renderTechnical(d.macd_bb, d.rsi, d.sma, d.rvol, d.adx, d.avwap), true);

  html += '<div class="layout-pair">';
  html += sec('', 'PIOTROSKI F-SCORE', renderPiotroski(d.piotroski), true);
  html += sec('', 'ALTMAN Z-SCORE', renderAltman(d.altman), true);
  html += '</div>';

  html += '<div class="layout-pair">';
  html += sec('', 'TECHNICAL CONSENSUS', renderConsensus(d), false);
  html += sec('', 'COMPOSITE SCORE', renderComposite(d.composite), false);
  html += '</div>';

  html += '<div class="layout-pair">';
  html += sec('', 'KEY METRICS', renderMetrics(d), false);
  html += sec('', 'RISK-ADJUSTED RETURN', renderRiskAdj(d.fcf_yield, d.sortino, d.sharpe), false);
  html += '</div>';

  html += sec('', 'FUNDAMENTAL', renderFundamentalTabs(d), false);
  html += sec('', 'LAPORAN KEUANGAN', renderFinancialTabs(d), false);

  var desc = i.longBusinessSummary
    ? '<div style="padding:16px 18px;font-size:12px;line-height:1.9;color:var(--text-secondary);">' + i.longBusinessSummary.substring(0, 600) + (i.longBusinessSummary.length > 600 ? '...' : '') + '</div>'
    : '';
  if (desc) html += sec('', 'PROFIL PERUSAHAAN', desc, false);

  document.getElementById('result').innerHTML = html;
  show('result');
  initTabs();
  document.getElementById('result').scrollIntoView({ behavior: 'smooth', block: 'start' });
  fetchAllAIInsights(ticker, d);
}
