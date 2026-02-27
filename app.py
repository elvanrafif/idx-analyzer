from flask import Flask, render_template_string, jsonify, request
import yfinance as yf
import pandas as pd
from datetime import datetime
import requests
from requests import Session

app = Flask(__name__)

HTML = '''<!DOCTYPE html>
<html lang="id" data-theme="dark">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>IDX Analyzer</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=Syne:wght@400;600;700;800&display=swap" rel="stylesheet">
<style>
[data-theme="dark"] {
  --bg:#0a0a0f; --surface:#111118; --surface2:#1a1a24; --card:#13131e;
  --border:#2a2a3a; --text:#e8e8f0; --muted:#6b6b80;
  --accent:#00ff88; --accent2:#0088ff; --warn:#ff6b35; --red:#ff3355;
  --shadow:rgba(0,0,0,0.5); --grid-op:0.3;
}
[data-theme="light"] {
  --bg:#f0f2f7; --surface:#ffffff; --surface2:#e8ecf4; --card:#ffffff;
  --border:#d0d5e8; --text:#1a1a2e; --muted:#6b7280;
  --accent:#0055cc; --accent2:#0088ff; --warn:#e05a00; --red:#cc0033;
  --shadow:rgba(0,0,0,0.08); --grid-op:0.12;
}
*{margin:0;padding:0;box-sizing:border-box;}
body{background:var(--bg);color:var(--text);font-family:'Syne',sans-serif;min-height:100vh;overflow-x:hidden;transition:background .3s,color .3s;}
body::before{content:'';position:fixed;inset:0;background-image:linear-gradient(var(--border) 1px,transparent 1px),linear-gradient(90deg,var(--border) 1px,transparent 1px);background-size:48px 48px;opacity:var(--grid-op);pointer-events:none;z-index:0;transition:opacity .3s;}
.container{position:relative;z-index:1;max-width:1100px;margin:0 auto;padding:0 24px 80px;}

/* HEADER */
.header{padding:48px 0 36px;display:flex;align-items:flex-end;justify-content:space-between;gap:16px;}
.header-left{display:flex;align-items:flex-end;gap:18px;}
.logo-mark{width:44px;height:44px;background:var(--accent);clip-path:polygon(0 100%,50% 0,100% 100%);flex-shrink:0;animation:pulse 3s ease-in-out infinite;transition:background .3s;}
@keyframes pulse{0%,100%{opacity:1;transform:scaleY(1);}50%{opacity:.7;transform:scaleY(.9);}}
.header-text h1{font-size:26px;font-weight:800;letter-spacing:-.5px;line-height:1;}
.header-text h1 span{color:var(--accent);transition:color .3s;}
.header-text p{font-family:'Space Mono',monospace;font-size:10px;color:var(--muted);margin-top:6px;letter-spacing:1px;text-transform:uppercase;}

/* THEME TOGGLE */
.theme-toggle{display:flex;align-items:center;gap:10px;background:var(--surface2);border:1.5px solid var(--border);border-radius:50px;padding:7px 14px 7px 10px;cursor:pointer;transition:all .2s;user-select:none;flex-shrink:0;}
.theme-toggle:hover{border-color:var(--accent);}
.toggle-track{width:36px;height:20px;background:var(--border);border-radius:10px;position:relative;transition:background .3s;}
[data-theme="light"] .toggle-track{background:var(--accent);}
.toggle-thumb{position:absolute;top:2px;left:2px;width:16px;height:16px;background:#fff;border-radius:50%;transition:transform .3s;box-shadow:0 1px 4px rgba(0,0,0,.3);}
[data-theme="light"] .toggle-thumb{transform:translateX(16px);}
.toggle-icon{font-size:14px;line-height:1;}
.toggle-label{font-family:'Space Mono',monospace;font-size:10px;color:var(--muted);letter-spacing:1px;text-transform:uppercase;min-width:30px;}

/* SEARCH */
.search-wrap{display:flex;margin-bottom:36px;position:relative;}
.search-prefix{position:absolute;left:18px;top:50%;transform:translateY(-50%);font-family:'Space Mono',monospace;font-size:13px;color:var(--accent);font-weight:700;z-index:1;pointer-events:none;transition:color .3s;}
#ticker-input{flex:1;background:var(--surface);border:1.5px solid var(--border);border-right:none;color:var(--text);font-family:'Space Mono',monospace;font-size:20px;font-weight:700;padding:18px 18px 18px 62px;outline:none;letter-spacing:3px;text-transform:uppercase;transition:border-color .2s,background .3s,color .3s;border-radius:4px 0 0 4px;}
#ticker-input:focus{border-color:var(--accent);}
#ticker-input::placeholder{color:var(--muted);letter-spacing:1px;font-size:14px;}
#search-btn{background:var(--accent);color:#000;border:none;padding:18px 32px;font-family:'Syne',sans-serif;font-size:14px;font-weight:800;letter-spacing:1px;text-transform:uppercase;cursor:pointer;transition:all .15s;border-radius:0 4px 4px 0;white-space:nowrap;}
#search-btn:hover{filter:brightness(1.1);transform:translateX(2px);}
#search-btn:disabled{background:var(--muted);cursor:not-allowed;transform:none;}

/* LOADING */
#loading{display:none;text-align:center;padding:80px 0;}
.spinner{width:40px;height:40px;border:2px solid var(--border);border-top-color:var(--accent);border-radius:50%;animation:spin .7s linear infinite;margin:0 auto 20px;}
@keyframes spin{to{transform:rotate(360deg);}}
#loading p{font-family:'Space Mono',monospace;font-size:11px;color:var(--muted);letter-spacing:2px;text-transform:uppercase;}
#error-box{display:none;background:rgba(255,51,85,.08);border:1px solid var(--red);border-left:4px solid var(--red);padding:16px 20px;border-radius:4px;font-family:'Space Mono',monospace;font-size:13px;color:var(--red);margin-bottom:24px;}
#result{display:none;}

/* STOCK HERO */
.stock-hero{background:var(--card);border:1px solid var(--border);border-top:3px solid var(--accent);padding:28px 32px;margin-bottom:20px;display:grid;grid-template-columns:1fr auto;gap:20px;align-items:center;animation:fadeUp .4s ease;box-shadow:0 4px 24px var(--shadow);transition:background .3s,border-color .3s,box-shadow .3s;}
@keyframes fadeUp{from{opacity:0;transform:translateY(16px);}to{opacity:1;transform:translateY(0);}}
.stock-ticker{font-size:11px;color:var(--muted);font-family:'Space Mono',monospace;letter-spacing:2px;text-transform:uppercase;margin-bottom:5px;}
.stock-name{font-size:24px;font-weight:800;letter-spacing:-.5px;}
.stock-meta{display:flex;gap:10px;margin-top:10px;flex-wrap:wrap;}
.meta-tag{font-family:'Space Mono',monospace;font-size:10px;color:var(--muted);background:var(--surface2);padding:4px 10px;border-radius:2px;letter-spacing:1px;text-transform:uppercase;transition:background .3s;}
.price-block{text-align:right;}
.price-main{font-family:'Space Mono',monospace;font-size:30px;font-weight:700;color:var(--accent);line-height:1;transition:color .3s;}
.price-change{font-family:'Space Mono',monospace;font-size:13px;margin-top:6px;}
.up{color:var(--accent);} .down{color:var(--red);} .neutral{color:var(--muted);}

/* SECTIONS */
.sections-grid{display:grid;gap:14px;}
.section{background:var(--card);border:1px solid var(--border);overflow:hidden;box-shadow:0 2px 12px var(--shadow);transition:background .3s,border-color .3s,box-shadow .3s;animation:fadeUp .4s ease both;}
.section:nth-child(1){animation-delay:.04s}.section:nth-child(2){animation-delay:.08s}.section:nth-child(3){animation-delay:.12s}.section:nth-child(4){animation-delay:.16s}.section:nth-child(5){animation-delay:.20s}.section:nth-child(6){animation-delay:.24s}.section:nth-child(7){animation-delay:.28s}.section:nth-child(8){animation-delay:.32s}
.section-header{display:flex;align-items:center;gap:10px;padding:13px 20px;border-bottom:1px solid var(--border);cursor:pointer;user-select:none;transition:background .15s;}
.section-header:hover{background:rgba(128,128,255,.04);}
.section-icon{font-size:14px;width:28px;height:28px;display:flex;align-items:center;justify-content:center;background:var(--surface2);border-radius:4px;flex-shrink:0;transition:background .3s;}
.section-title{font-size:11px;font-weight:700;letter-spacing:2px;text-transform:uppercase;flex:1;}
.section-toggle{font-size:13px;color:var(--muted);transition:transform .2s;}
.section.collapsed .section-toggle{transform:rotate(-90deg);}
.section.collapsed .section-body{display:none;}

/* DATA TABLE */
.data-table{width:100%;border-collapse:collapse;}
.data-table td{padding:10px 20px;font-size:12px;border-bottom:1px solid rgba(128,128,128,.07);vertical-align:middle;transition:background .15s;}
.data-table tr:last-child td{border-bottom:none;}
.data-table tr:hover td{background:rgba(128,128,255,.04);}
.td-label{color:var(--muted);font-family:'Space Mono',monospace;font-size:11px;letter-spacing:.5px;width:38%;}
.td-val{font-weight:600;font-family:'Space Mono',monospace;font-size:12px;text-align:right;width:24%;}
.td-rating{width:38%;padding-left:12px;}
.badge{display:inline-block;font-size:10px;padding:3px 8px;border-radius:2px;font-family:'Syne',sans-serif;font-weight:600;}
.bg{background:rgba(0,200,100,.12);color:var(--accent);}
.by{background:rgba(255,200,0,.12);color:#cc9900;}
.bo{background:rgba(255,107,53,.12);color:var(--warn);}
.br{background:rgba(255,51,85,.12);color:var(--red);}
.bb{background:rgba(0,136,255,.12);color:var(--accent2);}

/* STATS GRID */
.stats-grid{display:grid;grid-template-columns:1fr 1fr;}
.stat-item{padding:11px 20px;border-bottom:1px solid rgba(128,128,128,.07);border-right:1px solid rgba(128,128,128,.07);display:flex;justify-content:space-between;align-items:center;transition:background .15s;}
.stat-item:nth-child(2n){border-right:none;}
.stat-item:nth-last-child(-n+2){border-bottom:none;}
.stat-item:hover{background:rgba(128,128,255,.04);}
.sl{font-family:'Space Mono',monospace;font-size:10px;color:var(--muted);letter-spacing:.5px;}
.sv{font-family:'Space Mono',monospace;font-size:12px;font-weight:700;}

/* FIN TABLE */
.fin-table{width:100%;border-collapse:collapse;}
.fin-table th,.fin-table td{padding:10px 16px;font-size:12px;border-bottom:1px solid rgba(128,128,128,.07);font-family:'Space Mono',monospace;}
.fin-table th{background:var(--surface2);color:var(--muted);font-size:10px;letter-spacing:1px;text-transform:uppercase;text-align:right;font-weight:400;transition:background .3s;}
.fin-table th:first-child{text-align:left;color:var(--text);}
.fin-table td:first-child{color:var(--muted);font-size:11px;}
.fin-table td:not(:first-child){text-align:right;font-weight:600;}
.fin-table tr:hover td{background:rgba(128,128,255,.04);}
.pos{color:var(--accent);} .neg{color:var(--red);} .na{color:var(--muted);opacity:.4;}

/* ANALYST */
.analyst-wrap{padding:20px;display:flex;align-items:center;gap:16px;flex-wrap:wrap;}
.rec-badge{font-size:15px;font-weight:800;padding:10px 18px;border-radius:4px;letter-spacing:1px;text-transform:uppercase;}
.SB,.STRONGBUY{background:rgba(0,255,136,.1);color:var(--accent);border:1px solid var(--accent);}
.B{background:rgba(0,200,100,.1);color:#00cc66;border:1px solid #00cc66;}
.H,.N{background:rgba(255,200,0,.1);color:#cc9900;border:1px solid #cc9900;}
.S{background:rgba(255,51,85,.1);color:var(--red);border:1px solid var(--red);}
.SS{background:rgba(180,0,30,.1);color:#ff0033;border:1px solid #ff0033;}
.NA2{background:var(--surface2);color:var(--muted);border:1px solid var(--border);}
.rec-info{font-family:'Space Mono',monospace;font-size:11px;color:var(--muted);line-height:2.2;}

.desc-text{padding:20px;font-size:13px;line-height:1.8;color:var(--muted);}
.no-data{padding:20px;font-family:'Space Mono',monospace;font-size:11px;color:var(--muted);letter-spacing:.5px;}

.footer{margin-top:48px;padding-top:20px;border-top:1px solid var(--border);font-family:'Space Mono',monospace;font-size:10px;color:var(--muted);letter-spacing:1px;text-align:center;line-height:2.2;transition:border-color .3s;}

::-webkit-scrollbar{width:5px;}
::-webkit-scrollbar-track{background:var(--bg);}
::-webkit-scrollbar-thumb{background:var(--border);border-radius:3px;}

@media(max-width:640px){
  .stock-hero{grid-template-columns:1fr;}
  .price-block{text-align:left;}
  .stats-grid{grid-template-columns:1fr;}
  .stat-item{border-right:none;}
  .stat-item:nth-last-child(-n+2){border-bottom:1px solid rgba(128,128,128,.07);}
  .stat-item:last-child{border-bottom:none;}
  .header{flex-wrap:wrap;}
}
</style>
</head>
<body>
<div class="container">

  <div class="header">
    <div class="header-left">
      <div class="logo-mark"></div>
      <div class="header-text">
        <h1>IDX <span>ANALYZER</span></h1>
        <p>Laporan Keuangan & Fundamental — Bursa Efek Indonesia</p>
      </div>
    </div>
    <div class="theme-toggle" onclick="toggleTheme()">
      <span class="toggle-icon" id="t-icon">☀️</span>
      <div class="toggle-track"><div class="toggle-thumb"></div></div>
      <span class="toggle-label" id="t-label">DARK</span>
    </div>
  </div>

  <div class="search-wrap">
    <span class="search-prefix">IDX:</span>
    <input type="text" id="ticker-input" placeholder="Ketik ticker... contoh: BBCA" maxlength="10" autocomplete="off" spellcheck="false">
    <button id="search-btn" onclick="analyze()">ANALISIS →</button>
  </div>

  <div id="error-box"></div>
  <div id="loading"><div class="spinner"></div><p>Mengambil data dari Yahoo Finance...</p></div>
  <div id="result"></div>

  <div class="footer">
    IDX ANALYZER · DATA DARI YAHOO FINANCE · DELAY ~15 MENIT<br>
    HANYA UNTUK REFERENSI — BUKAN REKOMENDASI INVESTASI
  </div>
</div>

<script>
// ── THEME ──
const themes = {
  dark:  { icon:'☀️', label:'DARK',  next:'light' },
  light: { icon:'🌙', label:'LIGHT', next:'dark'  }
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

// Restore on load
applyTheme(localStorage.getItem('idx-theme') || 'dark');

// ── SEARCH ──
const inp = document.getElementById('ticker-input');
inp.addEventListener('keydown', e => { if(e.key==='Enter') analyze(); });
inp.addEventListener('input',   () => { inp.value = inp.value.toUpperCase(); });

async function analyze() {
  const ticker = inp.value.trim().toUpperCase();
  if(!ticker) return;
  hide('error-box'); hide('result');
  show('loading');
  document.getElementById('search-btn').disabled = true;
  try {
    const r = await fetch('/api/analyze?ticker=' + ticker);
    const d = await r.json();
    hide('loading');
    document.getElementById('search-btn').disabled = false;
    if(d.error) { showErr(d.error); return; }
    render(d);
  } catch(e) {
    hide('loading');
    document.getElementById('search-btn').disabled = false;
    showErr('Koneksi gagal. Pastikan server berjalan.');
  }
}

function show(id){ document.getElementById(id).style.display='block'; }
function hide(id){ document.getElementById(id).style.display='none'; }
function showErr(m){ const el=document.getElementById('error-box'); el.textContent='⚠ '+m; el.style.display='block'; }

// ── FORMAT ──
function fnum(v, type) {
  if(v===null||v===undefined||v!==v) return '<span class="na">—</span>';
  const n = parseFloat(v);
  if(isNaN(n)) return String(v);
  const abs = Math.abs(n), sign = n<0;
  let s;
  if(type==='idr') {
    if(abs>=1e12) s='Rp '+(n/1e12).toFixed(2)+'T';
    else if(abs>=1e9)  s='Rp '+(n/1e9).toFixed(2)+'M';
    else if(abs>=1e6)  s='Rp '+(n/1e6).toFixed(2)+'Jt';
    else s='Rp '+n.toLocaleString('id');
  } else if(type==='pct') {
    s=(n*100).toFixed(2)+'%';
  } else {
    if(abs>=1e12) s=(n/1e12).toFixed(2)+'T';
    else if(abs>=1e9) s=(n/1e9).toFixed(2)+'B';
    else if(abs>=1e6) s=(n/1e6).toFixed(2)+'M';
    else s=n.toLocaleString('id',{maximumFractionDigits:2});
  }
  return sign ? `<span class="neg">${s}</span>` : s;
}

function fval(v) { return fnum(v, typeof v==='number'&&Math.abs(v)>5000?'idr':'num'); }

// ── RATING BADGES ──
const R = {
  pe:  v=>!v?'':v<10?'🟢 Murah':v<20?'🟡 Wajar':v<30?'🟠 Mahal':'🔴 Sangat Mahal',
  pb:  v=>!v?'':v<1?'🟢 Di Bawah Book':v<2?'🟡 Wajar':v<4?'🟠 Premium':'🔴 Sangat Mahal',
  de:  v=>!v?'':v<50?'🟢 Rendah':v<100?'🟡 Sedang':v<200?'🟠 Tinggi':'🔴 Sangat Tinggi',
  roe: v=>!v?'':(p=>p>=20?'🟢 Excellent':p>=15?'🟡 Bagus':p>=10?'🟠 Sedang':p>0?'🔴 Rendah':'🔴 Rugi')(v*100),
  roa: v=>!v?'':(p=>p>=10?'🟢 Excellent':p>=7?'🟡 Bagus':p>=5?'🟠 Sedang':p>0?'🔴 Rendah':'🔴 Rugi')(v*100),
  npm: v=>!v?'':(p=>p>=20?'🟢 Tinggi':p>=10?'🟡 Sedang':p>=5?'🟠 Tipis':p>0?'🔴 Sangat Tipis':'🔴 Rugi')(v*100),
  cr:  v=>!v?'':v>=2?'🟢 Sangat Sehat':v>=1.5?'🟡 Sehat':v>=1?'🟠 Cukup':'🔴 Rawan',
  dy:  v=>!v?'':(p=>p>=5?'🟢 Tinggi':p>=3?'🟡 Menarik':p>=1?'🟠 Rendah':'🔘 Sangat Rendah')(v*100),
};

function badge(txt) {
  if(!txt) return '';
  const m={'🟢':'bg','🟡':'by','🟠':'bo','🔴':'br','🔘':'bb','✅':'bg'};
  return `<span class="badge ${m[txt[0]]||'bb'}">${txt}</span>`;
}

// ── BUILDERS ──
function sec(icon, title, body, open=true) {
  const id='s'+Math.random().toString(36).slice(2,8);
  return `<div class="section${open?'':' collapsed'}" id="${id}">
    <div class="section-header" onclick="document.getElementById('${id}').classList.toggle('collapsed')">
      <div class="section-icon">${icon}</div>
      <div class="section-title">${title}</div>
      <div class="section-toggle">▼</div>
    </div>
    <div class="section-body">${body}</div>
  </div>`;
}

function dtable(rows) {
  return '<table class="data-table">'+rows.map(([l,v,r])=>
    `<tr><td class="td-label">${l}</td><td class="td-val">${fval(v)}</td><td class="td-rating">${r?badge(r):''}</td></tr>`
  ).join('')+'</table>';
}

function ftable(data, metrics) {
  if(!data?.columns?.length) return '<p class="no-data">Data tidak tersedia dari Yahoo Finance untuk emiten ini.</p>';
  const cols = data.columns.slice(0,4);
  return `<table class="fin-table">
    <thead><tr><th>Metrik</th>${cols.map(c=>`<th>${c}</th>`).join('')}</tr></thead>
    <tbody>${metrics.map(([key,label])=>{
      const row=data.data[key];
      if(!row) return `<tr><td>${label}</td>${cols.map(()=>'<td class="na">—</td>').join('')}</tr>`;
      return `<tr><td>${label}</td>${cols.map(c=>{
        const v=row[c];
        if(v===null||v===undefined) return '<td class="na">—</td>';
        return `<td class="${v<0?'neg':''}">${fnum(v,'idr')}</td>`;
      }).join('')}</tr>`;
    }).join('')}</tbody>
  </table>`;
}

// ── RENDER ──
function render(d) {
  const i = d.info;
  const price = i.regularMarketPrice || i.currentPrice;
  const prev  = i.regularMarketPreviousClose;
  const chg   = prev ? (price-prev)/prev*100 : null;
  const chgCls = chg>0?'up':chg<0?'down':'neutral';
  const chgStr = chg!==null ? (chg>=0?'+':'')+chg.toFixed(2)+'%' : '—';
  const upside = (i.targetMeanPrice&&price) ? ((i.targetMeanPrice-price)/price*100).toFixed(1) : null;

  // Key Stats
  const statsHTML = `<div class="stats-grid">${[
    ['Market Cap',       fnum(i.marketCap,'idr')],
    ['Shares Outstanding',fnum(i.sharesOutstanding)],
    ['52wk High',        `<span class="pos">${fnum(i.fiftyTwoWeekHigh,'idr')}</span>`],
    ['52wk Low',         `<span class="neg">${fnum(i.fiftyTwoWeekLow,'idr')}</span>`],
    ['Volume Hari Ini',  fnum(i.regularMarketVolume)],
    ['Avg Volume 10d',   fnum(i.averageVolume10days)],
    ['Beta',             fnum(i.beta)],
    ['Float Shares',     fnum(i.floatShares)],
  ].map(([l,v])=>`<div class="stat-item"><span class="sl">${l}</span><span class="sv">${v}</span></div>`).join('')}</div>`;

  const valHTML = dtable([
    ['P/E Ratio (Trailing)',  i.trailingPE,                   R.pe(i.trailingPE)],
    ['P/E Ratio (Forward)',   i.forwardPE,                    R.pe(i.forwardPE)],
    ['Price to Book (P/BV)',  i.priceToBook,                  R.pb(i.priceToBook)],
    ['Price to Sales',        i.priceToSalesTrailing12Months, ''],
    ['PEG Ratio',             i.pegRatio,                     ''],
    ['EV / EBITDA',           i.enterpriseToEbitda,           ''],
    ['EV / Revenue',          i.enterpriseToRevenue,          ''],
    ['EPS Trailing',          i.trailingEps,                  ''],
    ['EPS Forward',           i.forwardEps,                   ''],
    ['Book Value per Share',  i.bookValue,                    ''],
  ]);

  const profHTML = dtable([
    ['Return on Equity (ROE)',  i.returnOnEquity,   R.roe(i.returnOnEquity)],
    ['Return on Assets (ROA)',  i.returnOnAssets,   R.roa(i.returnOnAssets)],
    ['Net Profit Margin',       i.profitMargins,    R.npm(i.profitMargins)],
    ['Gross Profit Margin',     i.grossMargins,     ''],
    ['Operating Margin',        i.operatingMargins, ''],
    ['EBITDA Margin',           i.ebitdaMargins,    ''],
    ['Revenue (TTM)',           i.totalRevenue,     ''],
    ['Gross Profit',            i.grossProfits,     ''],
    ['EBITDA',                  i.ebitda,           ''],
    ['Net Income (TTM)',        i.netIncomeToCommon,''],
    ['Revenue Growth YoY',      i.revenueGrowth,    ''],
    ['Earnings Growth YoY',     i.earningsGrowth,   ''],
  ]);

  const healthHTML = dtable([
    ['Current Ratio',       i.currentRatio,     R.cr(i.currentRatio)],
    ['Quick Ratio',         i.quickRatio,        ''],
    ['Debt to Equity',      i.debtToEquity,      R.de(i.debtToEquity)],
    ['Total Debt',          i.totalDebt,         ''],
    ['Total Cash',          i.totalCash,         ''],
    ['Cash per Share',      i.totalCashPerShare, ''],
    ['Free Cash Flow',      i.freeCashflow,      ''],
    ['Operating Cash Flow', i.operatingCashflow, ''],
  ]);

  const divHTML = dtable([
    ['Dividend Yield',        i.dividendYield,            R.dy(i.dividendYield)],
    ['Dividend Rate',         i.dividendRate,             ''],
    ['Payout Ratio',          i.payoutRatio,              ''],
    ['5Y Avg Dividend Yield', i.fiveYearAvgDividendYield, ''],
    ['Ex-Dividend Date',      i.exDividendDate,           ''],
    ['Last Dividend Value',   i.lastDividendValue,        ''],
  ]);

  // Analyst recommendation class mapping
  const recKey = (i.recommendationKey||'na').toLowerCase();
  const recMap = {strongbuy:'SB',buy:'B',hold:'H',neutral:'N',sell:'S',strongsell:'SS'};
  const recCls = recMap[recKey.replace('_','')] || 'NA2';
  const recLabel = (i.recommendationKey||'N/A').toUpperCase().replace('_',' ');

  const analystHTML = `<div class="analyst-wrap">
    <div class="rec-badge ${recCls}">${recLabel}</div>
    <div class="rec-info">
      <strong>${i.numberOfAnalystOpinions||'?'}</strong> Analis<br>
      Target Mean: ${fnum(i.targetMeanPrice,'idr')}<br>
      ${upside ? `Upside: <span class="${parseFloat(upside)>=0?'pos':'neg'}">${upside}%</span>` : ''}
    </div>
    <div class="rec-info" style="margin-left:auto">
      High: ${fnum(i.targetHighPrice,'idr')}<br>
      Low:  ${fnum(i.targetLowPrice,'idr')}
    </div>
  </div>`;

  const IS = [['Total Revenue','Revenue'],['Cost Of Revenue','Beban Pendapatan'],
    ['Gross Profit','Laba Kotor'],['Operating Income','Laba Operasi'],
    ['EBITDA','EBITDA'],['Net Income','Laba Bersih'],['Diluted EPS','EPS Diluted']];
  const BS = [['Total Assets','Total Aset'],
    ['Total Liabilities Net Minority Interest','Total Liabilitas'],
    ['Stockholders Equity','Total Ekuitas'],
    ['Cash And Cash Equivalents','Kas & Setara'],
    ['Total Debt','Total Utang'],['Net Debt','Net Debt'],
    ['Inventory','Persediaan'],['Accounts Receivable','Piutang Usaha']];
  const CF = [['Operating Cash Flow','Arus Kas Operasi'],
    ['Investing Cash Flow','Arus Kas Investasi'],
    ['Financing Cash Flow','Arus Kas Pendanaan'],
    ['Free Cash Flow','Free Cash Flow'],
    ['Capital Expenditure','Capex'],['Dividends Paid','Dividen Dibayar']];
  const QT = [['Total Revenue','Revenue'],['Gross Profit','Laba Kotor'],
    ['Operating Income','Laba Operasi'],['Net Income','Laba Bersih']];

  const desc = i.longBusinessSummary
    ? `<div class="desc-text">${i.longBusinessSummary.substring(0,600)}${i.longBusinessSummary.length>600?'...':''}</div>`
    : '';

  document.getElementById('result').innerHTML = `
    <div class="stock-hero">
      <div>
        <div class="stock-ticker">${d.ticker} · IDX · ${d.updated}</div>
        <div class="stock-name">${i.longName||i.shortName||d.ticker}</div>
        <div class="stock-meta">
          <span class="meta-tag">${i.sector||'N/A'}</span>
          <span class="meta-tag">${i.industry||'N/A'}</span>
        </div>
      </div>
      <div class="price-block">
        <div class="price-main">Rp ${price?price.toLocaleString('id'):'—'}</div>
        <div class="price-change ${chgCls}">${chgStr} hari ini</div>
      </div>
    </div>
    <div class="sections-grid">
      ${sec('📌','KEY STATISTICS', statsHTML)}
      ${sec('💰','VALUASI', valHTML)}
      ${sec('📈','PROFITABILITAS & PERTUMBUHAN', profHTML)}
      ${sec('🏦','KESEHATAN KEUANGAN', healthHTML)}
      ${sec('💵','DIVIDEN', divHTML)}
      ${sec('🎯','REKOMENDASI ANALIS', analystHTML)}
      ${sec('📋','INCOME STATEMENT — Tahunan', ftable(d.financials,IS), false)}
      ${sec('🏛️','BALANCE SHEET — Tahunan', ftable(d.balance_sheet,BS), false)}
      ${sec('💸','CASH FLOW — Tahunan', ftable(d.cashflow,CF), false)}
      ${sec('📅','QUARTERLY — 4 Kuartal Terakhir', ftable(d.quarterly,QT), false)}
      ${desc ? sec('🏢','PROFIL PERUSAHAAN', desc, false) : ''}
    </div>`;

  show('result');
  document.getElementById('result').scrollIntoView({behavior:'smooth',block:'start'});
}
</script>
</body>
</html>'''


def df_to_dict(df):
    if df is None or df.empty: return None
    try:
        cols = [f"Q{c.quarter} {c.year}" if hasattr(c,'quarter') else str(c.year)
                for c in df.columns[:4]]
        data = {}
        for idx in df.index:
            row = {}
            for j, col in enumerate(df.columns[:4]):
                try:
                    v = df.loc[idx, col]
                    row[cols[j]] = None if pd.isna(v) else float(v)
                except: row[cols[j]] = None
            data[str(idx)] = row
        return {"columns": cols, "data": data}
    except: return None


@app.route('/')
def index():
    return render_template_string(HTML)

session = Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36'
})

@app.route('/')
def index():
    return render_template_string(HTML)

@app.route('/api/analyze')
def analyze():
    ticker = request.args.get('ticker', '').strip().upper()
    if not ticker:
        return jsonify({"error": "Ticker tidak boleh kosong."})
    
    print(f"DEBUG: Menganalisa ticker {ticker}")
    
    try:
        stock = yf.Ticker(f"{ticker}.JK", session=session)
        info = stock.info
        
        if not info or not (info.get('regularMarketPrice') or info.get('currentPrice')):
            return jsonify({"error": f"Data tidak ditemukan untuk {ticker}. Pastikan emiten terdaftar di IHSG."})
        
        clean = {k: (None if isinstance(v, float) and pd.isna(v) else v) for k, v in info.items()}
        
        return jsonify({
            "ticker":        ticker,
            "updated":       datetime.now().strftime("%d/%m/%Y %H:%M"),
            "info":          clean,
            "financials":    df_to_dict(stock.financials),
            "balance_sheet": df_to_dict(stock.balance_sheet),
            "cashflow":      df_to_dict(stock.cashflow),
            "quarterly":     df_to_dict(stock.quarterly_financials),
        })
    except Exception as e:
        print(f"ERROR: {str(e)}")
        return jsonify({"error": f"Gagal mengambil data: {str(e)}"})


if __name__ == '__main__':
    print("=" * 50)
    print("  📊 IDX STOCK ANALYZER — Web App")
    print("  Buka: http://localhost:8080")
    print("  Stop: Ctrl+C")
    print("=" * 50)
    app.run(debug=False, host='0.0.0.0', port=8080)
