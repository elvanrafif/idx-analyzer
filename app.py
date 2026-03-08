from flask import Flask, render_template_string, jsonify, request
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, timezone

app = Flask(__name__)

# ─── FRONTEND HTML ───
HTML = '''<!DOCTYPE html>
<html lang="id" data-theme="light">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>IDX Analyzer</title>
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>📊</text></svg>">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
<style>
[data-theme="light"] {
  --bg:#f0f2f5; --text:#2c3e50; --muted:#64748b; --strong:#1a202c;
  --sh-dark:#c8cdd6; --sh-light:#ffffff;
  --neu:5px 5px 10px #c8cdd6,-5px -5px 10px #ffffff;
  --neu-sm:3px 3px 6px #c8cdd6,-3px -3px 6px #ffffff;
  --neu-in:inset 3px 3px 6px #c8cdd6,inset -3px -3px 6px #ffffff;
  --pos:#059669; --neg:#dc2626; --warn:#d97706; --info:#2563eb; --accent:#2563eb;
  --surface:#f0f2f5; --card:#f0f2f5; --border:rgba(0,0,0,0.06);
}
[data-theme="dark"] {
  --bg:#1c2030; --text:#e2e8f0; --muted:#94a3b8; --strong:#f8fafc;
  --sh-dark:#111525; --sh-light:#27304a;
  --neu:5px 5px 10px #111525,-5px -5px 10px #27304a;
  --neu-sm:3px 3px 6px #111525,-3px -3px 6px #27304a;
  --neu-in:inset 3px 3px 6px #111525,inset -3px -3px 6px #27304a;
  --pos:#34d399; --neg:#f87171; --warn:#fbbf24; --info:#60a5fa; --accent:#60a5fa;
  --surface:#1c2030; --card:#1c2030; --border:rgba(255,255,255,0.04);
}
*{margin:0;padding:0;box-sizing:border-box;}
body{background:var(--bg);color:var(--text);font-family:'Plus Jakarta Sans',sans-serif;min-height:100vh;overflow-x:hidden;transition:background .3s,color .3s;}
.container{max-width:1100px;margin:0 auto;padding:0 24px 80px;}

/* HEADER */
.header{padding:40px 0 32px;display:flex;align-items:center;justify-content:space-between;gap:16px;}
.header-left{display:flex;align-items:center;gap:16px;}
.logo-mark{width:44px;height:44px;border-radius:12px;background:var(--bg);box-shadow:var(--neu);display:flex;align-items:center;justify-content:center;font-size:22px;flex-shrink:0;}
.header-text h1{font-size:24px;font-weight:800;letter-spacing:-.5px;color:var(--strong);}
.header-text h1 span{color:var(--accent);}
.header-text p{font-family:'JetBrains Mono',monospace;font-size:10px;color:var(--muted);margin-top:4px;letter-spacing:.5px;}

/* THEME TOGGLE */
.theme-toggle{display:flex;align-items:center;gap:10px;background:var(--bg);box-shadow:var(--neu-sm);border-radius:50px;padding:8px 16px 8px 12px;cursor:pointer;transition:all .2s;user-select:none;flex-shrink:0;}
.toggle-track{width:36px;height:20px;background:var(--muted);border-radius:10px;position:relative;transition:background .3s;box-shadow:var(--neu-in);}
[data-theme="light"] .toggle-track{background:var(--accent);}
.toggle-thumb{position:absolute;top:2px;left:2px;width:16px;height:16px;background:#fff;border-radius:50%;transition:transform .3s;box-shadow:0 1px 4px rgba(0,0,0,.25);}
[data-theme="light"] .toggle-thumb{transform:translateX(16px);}
.toggle-label{font-family:'JetBrains Mono',monospace;font-size:10px;color:var(--muted);letter-spacing:.5px;min-width:56px;}

/* SEARCH */
.search-wrap{display:flex;margin-bottom:32px;position:relative;width:100%;align-items:stretch;gap:0;}
.search-prefix{position:absolute;left:20px;top:50%;transform:translateY(-50%);font-family:'JetBrains Mono',monospace;font-size:13px;color:var(--accent);font-weight:600;z-index:1;pointer-events:none;}
#ticker-input{flex:1;background:var(--bg);box-shadow:var(--neu-in);border:none;color:var(--text);font-family:'JetBrains Mono',monospace;font-size:20px;font-weight:600;padding:18px 18px 18px 64px;outline:none;letter-spacing:3px;text-transform:uppercase;transition:box-shadow .2s,background .3s,color .3s;border-radius:16px 0 0 16px;min-width:0;}
#ticker-input::placeholder{color:var(--muted);letter-spacing:1px;font-size:14px;}
#search-btn{background:var(--accent);color:#fff;border:none;padding:18px 32px;font-family:'Plus Jakarta Sans',sans-serif;font-size:14px;font-weight:700;letter-spacing:.5px;cursor:pointer;transition:all .15s;border-radius:0 16px 16px 0;white-space:nowrap;box-shadow:4px 4px 8px rgba(0,0,0,.2);}
#search-btn:hover{filter:brightness(1.1);}
#search-btn:disabled{background:var(--muted);cursor:not-allowed;}

/* LOADING */
#loading{display:none;text-align:center;padding:80px 0;}
.spinner{width:40px;height:40px;border-radius:50%;background:var(--bg);box-shadow:var(--neu);position:relative;margin:0 auto 20px;animation:spin-neu .9s linear infinite;}
@keyframes spin-neu{to{transform:rotate(360deg);}}
.spinner::before{content:'';position:absolute;inset:5px;border-radius:50%;border:2px solid transparent;border-top-color:var(--accent);}
#loading p{font-family:'JetBrains Mono',monospace;font-size:11px;color:var(--muted);letter-spacing:1px;}
#error-box{display:none;background:var(--bg);box-shadow:var(--neu-sm);border-left:4px solid var(--neg);padding:16px 20px;border-radius:12px;font-family:'JetBrains Mono',monospace;font-size:13px;color:var(--neg);margin-bottom:24px;}
#result{display:none;}

/* STOCK HERO */
.stock-hero{background:var(--bg);box-shadow:var(--neu);border-radius:20px;padding:28px 32px;margin-bottom:20px;display:grid;grid-template-columns:1fr auto;gap:20px;align-items:center;animation:fadeUp .4s ease;}
@keyframes fadeUp{from{opacity:0;transform:translateY(16px);}to{opacity:1;transform:translateY(0);}}
.stock-ticker{font-size:11px;color:var(--muted);font-family:'JetBrains Mono',monospace;letter-spacing:1.5px;margin-bottom:6px;}
.stock-name{font-size:22px;font-weight:800;color:var(--strong);letter-spacing:-.3px;}
.stock-meta{display:flex;gap:8px;margin-top:10px;flex-wrap:wrap;}
.meta-tag{font-family:'JetBrains Mono',monospace;font-size:10px;color:var(--muted);background:var(--bg);box-shadow:var(--neu-sm);padding:4px 12px;border-radius:50px;letter-spacing:.5px;}
.price-block{text-align:right;}
.price-main{font-family:'JetBrains Mono',monospace;font-size:28px;font-weight:600;color:var(--accent);line-height:1;}
.price-change{font-family:'JetBrains Mono',monospace;font-size:13px;margin-top:6px;}
.up{color:var(--pos);} .down{color:var(--neg);} .neutral{color:var(--muted);}

/* SECTIONS GRID — 2-column */
.sections-grid{display:grid;grid-template-columns:1fr 1fr;gap:16px;}
.span2{grid-column:span 2;}
.section{background:var(--bg);box-shadow:var(--neu);border-radius:16px;overflow:hidden;animation:fadeUp .4s ease both;}
.section:nth-child(1){animation-delay:.04s}.section:nth-child(2){animation-delay:.08s}
.section:nth-child(3){animation-delay:.10s}.section:nth-child(4){animation-delay:.12s}
.section:nth-child(5){animation-delay:.14s}.section:nth-child(6){animation-delay:.16s}
.section:nth-child(7){animation-delay:.18s}.section:nth-child(8){animation-delay:.20s}
.section:nth-child(9){animation-delay:.22s}.section:nth-child(10){animation-delay:.24s}
.section-header{display:flex;align-items:center;gap:10px;padding:14px 20px;cursor:pointer;user-select:none;transition:opacity .15s;}
.section-header:hover{opacity:.8;}
.section-icon{font-size:14px;width:30px;height:30px;display:flex;align-items:center;justify-content:center;background:var(--bg);box-shadow:var(--neu-sm);border-radius:8px;flex-shrink:0;}
.section-title{font-size:11px;font-weight:700;letter-spacing:1px;text-transform:uppercase;flex:1;color:var(--strong);}
.section-toggle{font-size:12px;color:var(--muted);transition:transform .2s;}
.section.collapsed .section-toggle{transform:rotate(-90deg);}
.section.collapsed .section-body{display:none;}
.section-divider{height:1px;background:var(--border);margin:0 20px;}

/* DATA TABLE */
.data-table{width:100%;border-collapse:collapse;}
.data-table td{padding:10px 20px;font-size:12px;border-bottom:1px solid var(--border);vertical-align:middle;}
.data-table tr:last-child td{border-bottom:none;}
.td-label{color:var(--muted);font-family:'Plus Jakarta Sans',sans-serif;font-size:12px;font-weight:500;width:38%;}
.td-val{font-weight:600;font-family:'JetBrains Mono',monospace;font-size:12px;text-align:right;width:24%;}
.td-rating{width:38%;padding-left:12px;}
.badge{display:inline-block;font-size:10px;padding:3px 9px;border-radius:50px;font-family:'Plus Jakarta Sans',sans-serif;font-weight:600;}
.bg{background:rgba(5,150,105,0.12);color:var(--pos);}
.by{background:rgba(217,119,6,0.12);color:var(--warn);}
.bo{background:rgba(217,119,6,0.15);color:var(--warn);}
.br{background:rgba(220,38,38,0.12);color:var(--neg);}
.bb{background:rgba(37,99,235,0.12);color:var(--info);}

/* STATS GRID */
.stats-grid{display:grid;grid-template-columns:1fr 1fr;}
.stat-item{padding:11px 20px;border-bottom:1px solid var(--border);border-right:1px solid var(--border);display:flex;justify-content:space-between;align-items:center;}
.stat-item:nth-child(2n){border-right:none;}
.stat-item:nth-last-child(-n+2){border-bottom:none;}
.sl{font-family:'Plus Jakarta Sans',sans-serif;font-size:11px;color:var(--muted);font-weight:500;}
.sv{font-family:'JetBrains Mono',monospace;font-size:12px;font-weight:600;color:var(--strong);}

/* FINANCIAL TABLE */
.table-scroll{width:100%;overflow-x:auto;-webkit-overflow-scrolling:touch;}
.fin-table{width:100%;min-width:600px;border-collapse:collapse;}
.fin-table th,.fin-table td{padding:10px 16px;font-size:12px;border-bottom:1px solid var(--border);font-family:'JetBrains Mono',monospace;}
.fin-table th{color:var(--muted);font-size:10px;letter-spacing:.5px;text-transform:uppercase;text-align:right;font-weight:500;background:var(--bg);}
.fin-table th:first-child{text-align:left;color:var(--text);position:sticky;left:0;z-index:2;background:var(--bg);}
.fin-table td:first-child{color:var(--muted);font-size:11px;position:sticky;left:0;z-index:1;background:var(--bg);}
.fin-table td:not(:first-child){text-align:right;font-weight:600;}
.pos{color:var(--pos);} .neg{color:var(--neg);} .na{color:var(--muted);opacity:.4;}

/* ANALYST */
/* TECHNICAL CONSENSUS */
.consensus-wrap{padding:18px 20px;display:flex;gap:20px;flex-wrap:wrap;}
.consensus-verdict{display:flex;flex-direction:column;gap:8px;min-width:150px;}
.consensus-badge{font-size:13px;font-weight:800;padding:10px 16px;border-radius:10px;letter-spacing:1px;text-transform:uppercase;display:inline-block;box-shadow:var(--neu-sm);}
.consensus-counts{display:flex;gap:10px;font-family:'JetBrains Mono',monospace;font-size:11px;font-weight:600;flex-wrap:wrap;}
.consensus-list{flex:1;display:flex;flex-direction:column;}
.consensus-row{display:flex;align-items:center;gap:10px;padding:7px 0;border-bottom:1px solid var(--border);}
.consensus-row:last-child{border-bottom:none;}
.consensus-name{font-size:12px;font-weight:600;color:var(--text);width:120px;flex-shrink:0;}
.consensus-detail{font-family:'JetBrains Mono',monospace;font-size:11px;color:var(--muted);flex:1;}
.consensus-vote{font-size:13px;font-weight:700;width:18px;text-align:right;flex-shrink:0;}

.desc-text{padding:20px;font-size:13px;line-height:1.9;color:var(--muted);font-family:'Plus Jakarta Sans',sans-serif;}
.no-data{padding:20px;font-family:'Plus Jakarta Sans',sans-serif;font-size:12px;color:var(--muted);}
.caption-label{font-family:'Plus Jakarta Sans',sans-serif;font-size:11px;color:var(--muted);font-weight:500;}

.footer{margin-top:48px;padding-top:20px;border-top:1px solid var(--border);font-family:'JetBrains Mono',monospace;font-size:10px;color:var(--muted);letter-spacing:.5px;text-align:center;line-height:2.4;}

::-webkit-scrollbar{width:5px;height:5px;}
::-webkit-scrollbar-track{background:var(--bg);}
::-webkit-scrollbar-thumb{background:var(--muted);border-radius:3px;opacity:.4;}

/* COMPOSITE SCORE */
.composite-card{padding:24px;display:flex;align-items:center;gap:24px;flex-wrap:wrap;}
.composite-score-num{font-family:'JetBrains Mono',monospace;font-size:54px;font-weight:600;line-height:1;}
.composite-info{flex:1;min-width:160px;}
.composite-signal{font-size:13px;font-weight:700;letter-spacing:1px;text-transform:uppercase;padding:6px 16px;border-radius:50px;display:inline-block;margin-bottom:10px;box-shadow:var(--neu-sm);}
.c-sb{background:rgba(5,150,105,0.12);color:var(--pos);}
.c-b{background:rgba(5,150,105,0.08);color:var(--pos);}
.c-h{background:rgba(217,119,6,0.10);color:var(--warn);}
.c-s{background:rgba(220,38,38,0.10);color:var(--neg);}
.c-ss{background:rgba(220,38,38,0.14);color:var(--neg);}
.composite-bars{display:grid;gap:8px;flex:2;min-width:220px;}
.cbar-row{display:flex;align-items:center;gap:8px;}
.cbar-label{font-family:'Plus Jakarta Sans',sans-serif;font-size:11px;font-weight:500;color:var(--muted);width:100px;flex-shrink:0;}
.cbar-track{flex:1;height:6px;background:var(--bg);border-radius:3px;overflow:hidden;box-shadow:var(--neu-in);}
.cbar-fill{height:100%;border-radius:3px;background:linear-gradient(90deg,var(--neg),var(--warn) 50%,var(--pos));transition:width .5s ease;}
.cbar-val{font-family:'JetBrains Mono',monospace;font-size:10px;color:var(--muted);width:28px;text-align:right;}

/* PIOTROSKI */
.fscore-header{display:flex;align-items:center;gap:16px;padding:16px 20px 8px;}
.fscore-num{font-family:'JetBrains Mono',monospace;font-size:42px;font-weight:600;line-height:1;}
.fscore-rating{font-size:11px;font-weight:700;padding:4px 12px;border-radius:50px;letter-spacing:.5px;box-shadow:var(--neu-sm);}
.fscore-kuat{background:rgba(5,150,105,0.12);color:var(--pos);}
.fscore-cukup{background:rgba(217,119,6,0.12);color:var(--warn);}
.fscore-lemah{background:rgba(220,38,38,0.12);color:var(--neg);}
.fscore-grid{display:grid;grid-template-columns:1fr 1fr;padding:0 20px 16px;gap:0;}
.fscore-item{display:flex;align-items:center;gap:8px;padding:7px 0;border-bottom:1px solid var(--border);font-size:11px;}
.fscore-item:nth-child(odd){border-right:1px solid var(--border);padding-right:12px;}
.fscore-item:nth-child(even){padding-left:12px;}
.fscore-check{width:18px;height:18px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:9px;flex-shrink:0;box-shadow:var(--neu-sm);}
.fscore-pass{background:rgba(5,150,105,0.12);color:var(--pos);}
.fscore-fail{background:rgba(220,38,38,0.10);color:var(--neg);}
.fscore-label{font-family:'Plus Jakarta Sans',sans-serif;font-size:11px;font-weight:500;color:var(--muted);flex:1;}
.fscore-val{font-family:'JetBrains Mono',monospace;font-size:10px;color:var(--text);}

/* ALTMAN Z */
.altman-wrap{padding:20px;display:flex;align-items:center;gap:20px;flex-wrap:wrap;}
.altman-score{font-family:'JetBrains Mono',monospace;font-size:46px;font-weight:600;line-height:1;}
.altman-zone{font-size:11px;font-weight:700;padding:4px 12px;border-radius:50px;letter-spacing:.5px;margin-top:8px;display:inline-block;box-shadow:var(--neu-sm);}
.altman-aman{background:rgba(5,150,105,0.12);color:var(--pos);}
.altman-waspada{background:rgba(217,119,6,0.12);color:var(--warn);}
.altman-bahaya{background:rgba(220,38,38,0.12);color:var(--neg);}
.altman-gauge{flex:1;min-width:200px;}
.altman-scale{display:flex;height:8px;border-radius:4px;overflow:hidden;margin:8px 0 4px;box-shadow:var(--neu-in);}
.altman-red{background:var(--neg);flex:1.1;}.altman-yellow{background:var(--warn);flex:1.5;}.altman-green{background:var(--pos);flex:2.5;}
.altman-labels{display:flex;justify-content:space-between;font-family:'JetBrains Mono',monospace;font-size:9px;color:var(--muted);}

/* TECHNICAL CARDS */
.tech-wrap{padding:16px;display:grid;grid-template-columns:1fr 1fr;gap:12px;}
.tech-card{background:var(--bg);border-radius:12px;padding:16px;box-shadow:var(--neu-sm);}
.tech-card-title{font-family:'Plus Jakarta Sans',sans-serif;font-size:11px;font-weight:600;color:var(--muted);letter-spacing:.5px;margin-bottom:10px;text-transform:uppercase;}
.tech-sig{font-size:11px;font-weight:700;padding:4px 12px;border-radius:50px;letter-spacing:.5px;display:inline-block;margin-bottom:10px;box-shadow:var(--neu-sm);}
.sig-bullish{background:rgba(5,150,105,0.12);color:var(--pos);}
.sig-bearish{background:rgba(220,38,38,0.10);color:var(--neg);}
.sig-overbought{background:rgba(217,119,6,0.12);color:var(--warn);}
.sig-oversold{background:rgba(37,99,235,0.12);color:var(--info);}
.sig-netral{background:var(--bg);color:var(--muted);box-shadow:var(--neu-sm);}
.sig-golden{background:rgba(5,150,105,0.15);color:var(--pos);}
.sig-death{background:rgba(220,38,38,0.12);color:var(--neg);}
.tech-row{display:flex;justify-content:space-between;font-family:'JetBrains Mono',monospace;font-size:11px;padding:4px 0;border-bottom:1px solid var(--border);}
.tech-row:last-child{border-bottom:none;}
.tech-row-label{color:var(--muted);font-family:'Plus Jakarta Sans',sans-serif;font-size:11px;font-weight:500;}

/* RSI BAR */
.rsi-bar-wrap{margin:10px 0;}
.rsi-bar-track{height:8px;border-radius:4px;background:var(--bg);box-shadow:var(--neu-in);position:relative;overflow:hidden;}
.rsi-bar-fill{height:100%;border-radius:4px;transition:width .5s ease;}
.rsi-zones{display:flex;justify-content:space-between;font-family:'JetBrains Mono',monospace;font-size:8px;color:var(--muted);margin-top:3px;}
.rsi-zones span{flex:1;text-align:center;}

/* RVOL */
.rvol-wrap{padding:20px;display:flex;align-items:center;gap:20px;flex-wrap:wrap;}
.rvol-num{font-family:'JetBrains Mono',monospace;font-size:50px;font-weight:600;line-height:1;}
.rvol-bar-wrap{flex:1;}
.rvol-bar-track{height:8px;border-radius:4px;background:var(--bg);box-shadow:var(--neu-in);overflow:hidden;margin:8px 0;}
.rvol-bar-fill{height:100%;background:linear-gradient(90deg,var(--info),var(--pos));border-radius:4px;transition:width .5s ease;}
.rvol-sig{font-size:11px;font-weight:700;padding:3px 10px;border-radius:50px;letter-spacing:.5px;display:inline-block;box-shadow:var(--neu-sm);}

@media(max-width:680px){
  .sections-grid{grid-template-columns:1fr;}
  .span2{grid-column:span 1;}
  .header{flex-direction:column;align-items:flex-start;gap:20px;}
  .header-left{width:100%;justify-content:space-between;}
  .search-wrap{flex-direction:column;gap:12px;}
  .search-prefix{top:18px;transform:none;}
  #ticker-input{border-radius:12px!important;width:100%;}
  #search-btn{border-radius:12px!important;width:100%;}
  .stock-hero{grid-template-columns:1fr;padding:20px;}
  .price-block{text-align:left;}
  .stats-grid{grid-template-columns:1fr;}
  .stat-item{border-right:none;}
  .stat-item:nth-last-child(-n+2){border-bottom:1px solid var(--border);}
  .stat-item:last-child{border-bottom:none;}
  .td-label{width:50%;}
  .td-val{width:50%;}
  .td-rating{display:none;}
  .tech-wrap{grid-template-columns:1fr;}
  .fscore-grid{grid-template-columns:1fr;}
  .fscore-item:nth-child(odd){border-right:none;}
  .composite-card{flex-direction:column;align-items:flex-start;}
  .analyst-wrap div:last-child{text-align:left!important;flex:none;width:100%;}
}
</style>
</head>
<body>
<div class="container">

  <div class="header">
    <div class="header-left">
      <div class="logo-mark">📊</div>
      <div class="header-text">
        <h1>IDX <span>ANALYZER</span></h1>
        <p>Laporan Keuangan &amp; Fundamental — Bursa Efek Indonesia</p>
      </div>
    </div>
    <div style="display:flex;align-items:center;gap:12px;">
      <div style="font-family:'JetBrains Mono',monospace;font-size:12px;font-weight:600;color:var(--muted);letter-spacing:.5px;">by <span style="color:var(--accent)">ElvanRafif</span></div>
      <div class="theme-toggle" onclick="toggleTheme()">
        <span id="t-icon" style="font-size:14px;">🌙</span>
        <div class="toggle-track"><div class="toggle-thumb"></div></div>
        <span class="toggle-label" id="t-label">Dark Mode</span>
      </div>
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
const themes = {
  light: { icon:'🌙', label:'Dark Mode',  next:'dark'  },
  dark:  { icon:'☀️', label:'Light Mode', next:'light' }
};
function applyTheme(t) {
  document.documentElement.setAttribute('data-theme', t);
  document.getElementById('t-icon').textContent  = themes[t].icon;
  document.getElementById('t-label').textContent = themes[t].label;
  localStorage.setItem('idx-theme', t);
}
function toggleTheme() {
  const cur = document.documentElement.getAttribute('data-theme') || 'light';
  applyTheme(themes[cur].next);
}
applyTheme(localStorage.getItem('idx-theme') || 'light');

const inp = document.getElementById('ticker-input');
inp.addEventListener('keydown', e => { if(e.key==='Enter') analyze(); });
inp.addEventListener('input',   () => { inp.value = inp.value.toUpperCase(); });

async function analyze() {
  const ticker = inp.value.trim().toUpperCase();
  if(!ticker) return;
  hide('error-box'); hide('result'); show('loading');
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
    showErr('Koneksi gagal atau limit tercapai. Tunggu beberapa saat.');
  }
}
function show(id){ document.getElementById(id).style.display='block'; }
function hide(id){ document.getElementById(id).style.display='none'; }
function showErr(m){ const el=document.getElementById('error-box'); el.textContent='⚠ '+m; el.style.display='block'; }

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
function sec(icon, title, body, open=true, wide=false) {
  const id='s'+Math.random().toString(36).slice(2,8);
  return `<div class="section${open?'':' collapsed'}${wide?' span2':''}" id="${id}">
    <div class="section-header" onclick="document.getElementById('${id}').classList.toggle('collapsed')">
      <div class="section-icon">${icon}</div>
      <div class="section-title">${title}</div>
      <div class="section-toggle">▼</div>
    </div>
    <div class="section-divider"></div>
    <div class="section-body">${body}</div>
  </div>`;
}
function dtable(rows) {
  return '<table class="data-table">'+rows.map(([l,v,r])=>
    `<tr><td class="td-label">${l}</td><td class="td-val">${fval(v)}</td><td class="td-rating">${r?badge(r):''}</td></tr>`
  ).join('')+'</table>';
}
function ftable(data, metrics) {
  if(!data?.columns?.length) return '<p class="no-data">Data tidak tersedia.</p>';
  const cols = data.columns.slice(0,4);
  return `<div class="table-scroll"><table class="fin-table">
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
  </table></div>`;
}
function renderConsensus(d) {
  const votes = [];
  if (d.macd_bb) {
    const sig = d.macd_bb.macd.signal_label;
    const v = sig==='BULLISH' ? 1 : -1;
    votes.push({name:'MACD (12,26,9)', label:sig, cls:v===1?'sig-bullish':'sig-bearish', vote:v, detail:`hist ${d.macd_bb.macd.hist}`});
  }
  if (d.macd_bb) {
    const sig = d.macd_bb.bb.signal;
    const v = (sig==='BULLISH'||sig==='OVERSOLD') ? 1 : (sig==='BEARISH'||sig==='OVERBOUGHT') ? -1 : 0;
    const cls = sig==='OVERBOUGHT'?'sig-overbought':sig==='OVERSOLD'?'sig-oversold':v===1?'sig-bullish':v===-1?'sig-bearish':'sig-netral';
    votes.push({name:'Bollinger Bands', label:sig, cls, vote:v, detail:`%B ${(d.macd_bb.bb.pct_b*100).toFixed(0)}%`});
  }
  if (d.rsi) {
    const v = d.rsi.signal==='OVERSOLD' ? 1 : d.rsi.signal==='OVERBOUGHT' ? -1 : 0;
    const cls = d.rsi.signal==='OVERSOLD'?'sig-oversold':d.rsi.signal==='OVERBOUGHT'?'sig-overbought':'sig-netral';
    votes.push({name:'RSI (14)', label:d.rsi.signal, cls, vote:v, detail:`RSI ${d.rsi.value}`});
  }
  if (d.piotroski) {
    const v = d.piotroski.rating==='KUAT' ? 1 : d.piotroski.rating==='LEMAH' ? -1 : 0;
    const cls = d.piotroski.rating==='KUAT'?'sig-bullish':d.piotroski.rating==='LEMAH'?'sig-bearish':'sig-netral';
    votes.push({name:'Piotroski F-Score', label:d.piotroski.rating, cls, vote:v, detail:`${d.piotroski.score}/9 poin`});
  }
  if (d.altman) {
    const v = d.altman.zone==='AMAN' ? 1 : d.altman.zone==='BAHAYA' ? -1 : 0;
    const cls = d.altman.zone==='AMAN'?'sig-bullish':d.altman.zone==='BAHAYA'?'sig-bearish':'sig-netral';
    votes.push({name:'Altman Z-Score', label:d.altman.zone, cls, vote:v, detail:`Z ${d.altman.z_score}`});
  }
  if (d.rvol) {
    const v = (d.rvol.signal==='SANGAT TINGGI'||d.rvol.signal==='TINGGI') ? 1 : d.rvol.signal==='RENDAH' ? -1 : 0;
    const cls = v===1?'sig-bullish':v===-1?'sig-bearish':'sig-netral';
    votes.push({name:'Rel. Volume', label:d.rvol.signal, cls, vote:v, detail:`${d.rvol.rvol}x avg`});
  }
  if (votes.length===0) return '<p class="no-data">Data tidak cukup untuk konsensus.</p>';
  const buyCount=votes.filter(v=>v.vote===1).length;
  const sellCount=votes.filter(v=>v.vote===-1).length;
  const neutCount=votes.filter(v=>v.vote===0).length;
  const score=buyCount-sellCount;
  let verdict,vcls;
  if(score>=4)      {verdict='STRONG BUY'; vcls='c-sb';}
  else if(score>=2) {verdict='BUY';        vcls='c-b';}
  else if(score>=-1){verdict='HOLD';       vcls='c-h';}
  else if(score>=-3){verdict='SELL';       vcls='c-s';}
  else              {verdict='STRONG SELL';vcls='c-ss';}
  const rows=votes.map(v=>{
    const arrow=v.vote===1?`<span class="consensus-vote pos">▲</span>`:v.vote===-1?`<span class="consensus-vote neg">▼</span>`:`<span class="consensus-vote neutral">—</span>`;
    return `<div class="consensus-row">
      <span class="consensus-name">${v.name}</span>
      <span class="tech-sig ${v.cls}" style="font-size:10px;padding:2px 8px;margin:0">${v.label}</span>
      <span class="consensus-detail">${v.detail}</span>
      ${arrow}
    </div>`;
  }).join('');
  return `<div class="consensus-wrap">
    <div class="consensus-verdict">
      <div class="consensus-badge ${vcls}">${verdict}</div>
      <div class="consensus-counts">
        <span class="pos">▲ ${buyCount} Beli</span>
        <span style="color:var(--muted)">— ${neutCount} Netral</span>
        <span class="neg">▼ ${sellCount} Jual</span>
      </div>
      <div class="caption-label" style="margin-top:2px">${votes.length} indikator</div>
    </div>
    <div class="consensus-list">${rows}</div>
  </div>`;
}
function renderComposite(c) {
  if (!c) return '<p class="no-data">Data composite tidak tersedia.</p>';
  const weights = {Fundamental:'30%',Technical:'25%',Risk:'20%',Momentum:'15%',Sentiment:'10%'};
  return `<div class="composite-card">
    <div>
      <div class="composite-score-num ${c.final>=70?'pos':c.final<35?'neg':''}">${c.final}</div>
      <div class="caption-label" style="margin-top:4px;">/ 100</div>
    </div>
    <div class="composite-info">
      <div class="composite-signal ${c.cls}">${c.signal}</div>
      <div class="caption-label">Skor Keputusan Komprehensif</div>
    </div>
    <div class="composite-bars">
      ${Object.entries(c.components).map(([name,val])=>`<div class="cbar-row">
        <span class="cbar-label">${name} <span style="opacity:.5">${weights[name]||''}</span></span>
        <div class="cbar-track"><div class="cbar-fill" style="width:${val}%"></div></div>
        <span class="cbar-val">${val}</span>
      </div>`).join('')}
    </div>
  </div>`;
}
function renderPiotroski(p) {
  if (!p) return '<p class="no-data">Data laporan keuangan tidak cukup untuk F-Score.</p>';
  const rCls = p.rating==='KUAT'?'fscore-kuat':p.rating==='CUKUP'?'fscore-cukup':'fscore-lemah';
  return `<div class="fscore-header">
    <div class="fscore-num ${p.score>=7?'pos':p.score>=5?'':'neg'}">${p.score}<span style="font-size:18px;color:var(--muted)">/9</span></div>
    <div>
      <div class="fscore-rating ${rCls}">${p.rating}</div>
      <div class="caption-label" style="margin-top:6px;">Piotroski F-Score</div>
    </div>
  </div>
  <div class="fscore-grid">
    ${Object.entries(p.details).map(([k,f])=>`<div class="fscore-item">
      <div class="fscore-check ${f.pass?'fscore-pass':'fscore-fail'}">${f.pass?'✓':'✗'}</div>
      <span class="fscore-label">${f.label}</span>
      <span class="fscore-val">${f.value}</span>
    </div>`).join('')}
  </div>`;
}
function renderAltman(a) {
  if (!a) return '<p class="no-data">Data balance sheet tidak cukup untuk Altman Z-Score.</p>';
  const zCls = a.zone==='AMAN'?'altman-aman':a.zone==='WASPADA'?'altman-waspada':'altman-bahaya';
  const sCls = a.zone==='AMAN'?'pos':a.zone==='BAHAYA'?'neg':'';
  return `<div class="altman-wrap">
    <div>
      <div class="altman-score ${sCls}">${a.z_score}</div>
      <div class="altman-zone ${zCls}">${a.zone}</div>
      <div class="caption-label" style="margin-top:6px;">${a.desc}</div>
    </div>
    <div class="altman-gauge">
      <div class="altman-scale"><div class="altman-red"></div><div class="altman-yellow"></div><div class="altman-green"></div></div>
      <div class="altman-labels"><span>0 Bahaya</span><span>1.1</span><span>2.6</span><span>5+ Aman</span></div>
      <div style="margin-top:12px">
        ${Object.entries(a.components).map(([k,v])=>`<div class="tech-row"><span class="tech-row-label">${k}</span><span>${v}</span></div>`).join('')}
      </div>
    </div>
  </div>`;
}
function renderTechnical(mb, rsi, sma) {
  if (!mb && !rsi && !sma) return '<p class="no-data">Data historis tidak cukup.</p>';
  const cards = [];
  if (mb) {
    const m=mb.macd, b=mb.bb;
    const ms=(m.signal_label||'').toLowerCase(), bs=(b.signal||'').toLowerCase();
    const sc={bullish:'sig-bullish',bearish:'sig-bearish',overbought:'sig-overbought',oversold:'sig-oversold',netral:'sig-netral'};
    const cross = m.cross ? `<div class="tech-sig ${m.cross.includes('GOLDEN')?'sig-golden':'sig-death'}" style="margin-top:6px;font-size:10px;">${m.cross}</div>` : '';
    cards.push(`<div class="tech-card">
      <div class="tech-card-title">MACD (12,26,9)</div>
      <div class="tech-sig ${sc[ms]||'sig-netral'}">${m.signal_label}</div>${cross}
      <div class="tech-row"><span class="tech-row-label">MACD Line</span><span>${m.line}</span></div>
      <div class="tech-row"><span class="tech-row-label">Signal Line</span><span>${m.signal}</span></div>
      <div class="tech-row"><span class="tech-row-label">Histogram</span><span class="${m.hist>0?'pos':'neg'}">${m.hist}</span></div>
    </div>`);
    cards.push(`<div class="tech-card">
      <div class="tech-card-title">Bollinger Bands (20,2)</div>
      <div class="tech-sig ${sc[bs]||'sig-netral'}">${b.signal}</div>
      <div class="tech-row"><span class="tech-row-label">Upper Band</span><span class="neg">Rp ${b.upper.toLocaleString('id')}</span></div>
      <div class="tech-row"><span class="tech-row-label">Middle (SMA20)</span><span>Rp ${b.mid.toLocaleString('id')}</span></div>
      <div class="tech-row"><span class="tech-row-label">Lower Band</span><span class="pos">Rp ${b.lower.toLocaleString('id')}</span></div>
      <div class="tech-row"><span class="tech-row-label">%B Position</span><span>${(b.pct_b*100).toFixed(0)}%</span></div>
    </div>`);
  }
  if (rsi) {
    const rsiColor = rsi.value>70?'var(--warn)':rsi.value<30?'var(--info)':'var(--pos)';
    const rsiSigCls = rsi.signal==='OVERBOUGHT'?'sig-overbought':rsi.signal==='OVERSOLD'?'sig-oversold':'sig-netral';
    cards.push(`<div class="tech-card">
      <div class="tech-card-title">RSI (14)</div>
      <div class="tech-sig ${rsiSigCls}">${rsi.signal}</div>
      <div style="font-family:'JetBrains Mono',monospace;font-size:28px;font-weight:600;color:${rsiColor};margin:6px 0;">${rsi.value}</div>
      <div class="rsi-bar-wrap">
        <div class="rsi-bar-track">
          <div class="rsi-bar-fill" style="width:${rsi.value}%;background:${rsiColor};"></div>
        </div>
        <div class="rsi-zones">
          <span style="color:var(--info);">0 Oversold</span>
          <span>30</span>
          <span>50</span>
          <span>70</span>
          <span style="color:var(--warn);">100 Overbought</span>
        </div>
      </div>
    </div>`);
  }
  if (sma) {
    const gcls = sma.golden_cross===true?'sig-golden':sma.golden_cross===false?'sig-death':'sig-netral';
    const glabel = sma.golden_cross===true?'Golden Cross':sma.golden_cross===false?'Death Cross':'N/A';
    cards.push(`<div class="tech-card">
      <div class="tech-card-title">Moving Averages</div>
      <div class="tech-sig ${gcls}" style="margin-bottom:10px;">${glabel}</div>
      <div class="tech-row"><span class="tech-row-label">Harga</span><span>Rp ${sma.price.toLocaleString('id')}</span></div>
      <div class="tech-row"><span class="tech-row-label">EMA 20</span><span class="${sma.price>sma.ema20?'pos':'neg'}">Rp ${sma.ema20.toLocaleString('id')}</span></div>
      <div class="tech-row"><span class="tech-row-label">SMA 50</span><span class="${sma.above_sma50?'pos':'neg'}">Rp ${sma.sma50.toLocaleString('id')}</span></div>
      <div class="tech-row"><span class="tech-row-label">SMA 200</span><span>${sma.sma200?'Rp '+sma.sma200.toLocaleString('id'):'<span class="na">—</span>'}</span></div>
    </div>`);
  }
  return `<div class="tech-wrap">${cards.join('')}</div>`;
}
function renderRvol(rv) {
  if (!rv) return '<p class="no-data">Data volume tidak tersedia.</p>';
  const sc = rv.signal==='SANGAT TINGGI'?'bg':rv.signal==='TINGGI'?'by':rv.signal==='NORMAL'?'bb':'br';
  const barW = Math.min(100, rv.rvol/4*100);
  return `<div class="rvol-wrap">
    <div>
      <div class="rvol-num ${rv.rvol>=2?'pos':rv.rvol<0.7?'neg':''}">${rv.rvol}x</div>
      <div class="rvol-sig badge ${sc}" style="margin-top:8px">${rv.signal}</div>
    </div>
    <div class="rvol-bar-wrap">
      <div class="caption-label">Relative Volume vs 20d Avg</div>
      <div class="rvol-bar-track"><div class="rvol-bar-fill" style="width:${barW}%"></div></div>
      <div class="tech-row"><span class="tech-row-label">Volume Hari Ini</span><span>${(rv.today/1e6).toFixed(2)}M</span></div>
      <div class="tech-row"><span class="tech-row-label">Avg 20 Hari</span><span>${(rv.avg/1e6).toFixed(2)}M</span></div>
    </div>
  </div>`;
}
function renderRiskAdj(fcf, sortino, sharpe) {
  const rows = [];
  if (fcf) {
    rows.push(['FCF Yield', fcf.yield*100, fcf.signal==='MENARIK'?'🟢 Menarik':fcf.signal==='NETRAL'?'🟡 Netral':fcf.signal==='RENDAH'?'🟠 Rendah':'🔴 Negatif']);
    rows.push(['Free Cash Flow', fcf.fcf, '']);
  }
  if (sortino!=null) rows.push(['Sortino Ratio', sortino, sortino>=1?'🟢 Excellent':sortino>=0.5?'🟡 Bagus':sortino>=0?'🟠 Rendah':'🔴 Negatif']);
  if (sharpe!=null)  rows.push(['Sharpe Ratio',  sharpe,  sharpe>=1?'🟢 Excellent':sharpe>=0.5?'🟡 Bagus':sharpe>=0?'🟠 Rendah':'🔴 Negatif']);
  return rows.length ? dtable(rows) : '<p class="no-data">Data tidak tersedia.</p>';
}

function render(d) {
  const i = d.info;
  const price = i.regularMarketPrice || i.currentPrice;
  const prev  = i.regularMarketPreviousClose;
  const chg   = prev ? (price-prev)/prev*100 : null;
  const chgCls = chg>0?'up':chg<0?'down':'neutral';
  const chgStr = chg!==null ? (chg>=0?'+':'')+chg.toFixed(2)+'%' : '—';
  const upside = (i.targetMeanPrice&&price) ? ((i.targetMeanPrice-price)/price*100).toFixed(1) : null;

  // 52-week position
  const wk52pos = (i.fiftyTwoWeekLow && i.fiftyTwoWeekHigh && price)
    ? ((price - i.fiftyTwoWeekLow) / (i.fiftyTwoWeekHigh - i.fiftyTwoWeekLow) * 100).toFixed(1) + '%'
    : null;

  const statsHTML = `<div class="stats-grid">${[
    ['Market Cap',            fnum(i.marketCap,'idr')],
    ['Shares Outstanding',    fnum(i.sharesOutstanding)],
    ['52wk High',             `<span class="pos">${fnum(i.fiftyTwoWeekHigh,'idr')}</span>`],
    ['52wk Low',              `<span class="neg">${fnum(i.fiftyTwoWeekLow,'idr')}</span>`],
    ['52wk Position',         wk52pos ? `<span>${wk52pos}</span>` : '<span class="na">—</span>'],
    ['Volume Hari Ini',       fnum(i.regularMarketVolume)],
    ['Avg Volume 10d',        fnum(i.averageVolume10days)],
    ['Beta',                  fnum(i.beta)],
    ['Float Shares',          fnum(i.floatShares)],
    ['Insider Holdings',      i.heldPercentInsiders!=null ? (i.heldPercentInsiders*100).toFixed(2)+'%' : '<span class="na">—</span>'],
    ['Institution Holdings',  i.heldPercentInstitutions!=null ? (i.heldPercentInstitutions*100).toFixed(2)+'%' : '<span class="na">—</span>'],
    ['Short Ratio',           fnum(i.shortRatio)],
    ['Short % of Float',      i.shortPercentOfFloat!=null ? (i.shortPercentOfFloat*100).toFixed(2)+'%' : '<span class="na">—</span>'],
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
  const recKey = (i.recommendationKey||'na').toLowerCase();
  const recMap = {strongbuy:'SB',buy:'B',hold:'H',neutral:'N',sell:'S',strongsell:'SS'};
  const recCls = recMap[recKey.replace('_','')] || 'NA2';
  const recLabel = (i.recommendationKey||'N/A').toUpperCase().replace('_',' ');

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
    <div class="stock-hero span2">
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
      ${sec('📌','KEY STATISTICS', statsHTML, true, true)}
      ${sec('🎯','TECHNICAL CONSENSUS', renderConsensus(d), true, true)}
      ${sec('🏆','COMPOSITE SCORE', renderComposite(d.composite), true, true)}
      ${sec('📊','PIOTROSKI F-SCORE', renderPiotroski(d.piotroski), true, false)}
      ${sec('⚠️','ALTMAN Z-SCORE', renderAltman(d.altman), true, false)}
      ${sec('📉','TECHNICAL — MACD, BB, RSI & MA', renderTechnical(d.macd_bb, d.rsi, d.sma), true, true)}
      ${sec('📦','RELATIVE VOLUME', renderRvol(d.rvol), true, false)}
      ${sec('💎','RISK-ADJUSTED RETURN', renderRiskAdj(d.fcf_yield, d.sortino, d.sharpe), true, false)}
      ${sec('💰','VALUASI', valHTML, true, false)}
      ${sec('📈','PROFITABILITAS', profHTML, true, false)}
      ${sec('🏦','KESEHATAN KEUANGAN', healthHTML, true, false)}
      ${sec('💵','DIVIDEN', divHTML, true, false)}
      ${sec('📋','INCOME STATEMENT — Tahunan', ftable(d.financials,IS), false, true)}
      ${sec('🏛️','BALANCE SHEET — Tahunan', ftable(d.balance_sheet,BS), false, true)}
      ${sec('💸','CASH FLOW — Tahunan', ftable(d.cashflow,CF), false, true)}
      ${sec('📅','QUARTERLY — 4 Kuartal Terakhir', ftable(d.quarterly,QT), false, true)}
      ${desc ? sec('🏢','PROFIL PERUSAHAAN', desc, false, true) : ''}
    </div>`;
  show('result');
  document.getElementById('result').scrollIntoView({behavior:'smooth',block:'start'});
}
</script>
</body>
</html>'''

# ─── INDICATOR FUNCTIONS ───

def calculate_piotroski(ticker):
    """Piotroski F-Score (0-9)"""
    try:
        stock = yf.Ticker(f"{ticker}.JK")
        bs, fs, cf = stock.balance_sheet, stock.financials, stock.cashflow
        if bs is None or bs.empty or fs is None or fs.empty or cf is None or cf.empty: return None
        if len(bs.columns) < 2 or len(fs.columns) < 2: return None

        def bsv(ci, *keys):
            if ci >= len(bs.columns): return None
            col = bs.columns[ci]
            for key in keys:
                for idx in bs.index:
                    if key.lower() in str(idx).lower():
                        try: v = bs.loc[idx, col]; return None if pd.isna(v) else float(v)
                        except: pass
            return None
        def fsv(ci, *keys):
            if ci >= len(fs.columns): return None
            col = fs.columns[ci]
            for key in keys:
                for idx in fs.index:
                    if key.lower() in str(idx).lower():
                        try: v = fs.loc[idx, col]; return None if pd.isna(v) else float(v)
                        except: pass
            return None
        def cfv(ci, *keys):
            if ci >= len(cf.columns): return None
            col = cf.columns[ci]
            for key in keys:
                for idx in cf.index:
                    if key.lower() in str(idx).lower():
                        try: v = cf.loc[idx, col]; return None if pd.isna(v) else float(v)
                        except: pass
            return None

        ta0=bsv(0,'total assets'); ta1=bsv(1,'total assets')
        ni0=fsv(0,'net income');   ni1=fsv(1,'net income')
        ocf0=cfv(0,'operating cash flow')
        ltd0=bsv(0,'long term debt'); ltd1=bsv(1,'long term debt')
        ca0=bsv(0,'current assets'); cl0=bsv(0,'current liabilities')
        ca1=bsv(1,'current assets'); cl1=bsv(1,'current liabilities')
        sh0=bsv(0,'ordinary shares','common stock'); sh1=bsv(1,'ordinary shares','common stock')
        gp0=fsv(0,'gross profit'); rev0=fsv(0,'total revenue')
        gp1=fsv(1,'gross profit'); rev1=fsv(1,'total revenue')

        score = 0; details = {}
        roa0 = ni0/ta0 if ni0 and ta0 else None
        roa1 = ni1/ta1 if ni1 and ta1 else None

        f1=1 if roa0 and roa0>0 else 0; score+=f1
        details['F1']={'label':'ROA Positif','pass':bool(f1),'value':f'{roa0*100:.1f}%' if roa0 else '—'}
        f2=1 if ocf0 and ocf0>0 else 0; score+=f2
        details['F2']={'label':'Arus Kas Operasi > 0','pass':bool(f2),'value':f'Rp {ocf0/1e9:.1f}M' if ocf0 else '—'}
        f3=1 if roa0 and roa1 and roa0>roa1 else 0; score+=f3
        details['F3']={'label':'ROA Meningkat YoY','pass':bool(f3),'value':f'{roa0*100:.1f}% vs {roa1*100:.1f}%' if (roa0 and roa1) else '—'}
        ocf_ta=ocf0/ta0 if ocf0 and ta0 else None
        f4=1 if ocf_ta and roa0 and ocf_ta>roa0 else 0; score+=f4
        details['F4']={'label':'Kualitas Laba (OCF>NI)','pass':bool(f4),'value':f'{ocf_ta*100:.1f}% vs {roa0*100:.1f}%' if (ocf_ta and roa0) else '—'}
        lev0=ltd0/ta0 if ltd0 is not None and ta0 else None
        lev1=ltd1/ta1 if ltd1 is not None and ta1 else None
        f5=1 if lev0 is not None and lev1 is not None and lev0<=lev1 else 0; score+=f5
        details['F5']={'label':'Leverage Tidak Naik','pass':bool(f5),'value':f'{lev0*100:.1f}% vs {lev1*100:.1f}%' if (lev0 is not None and lev1 is not None) else '—'}
        cr0=ca0/cl0 if ca0 and cl0 else None; cr1=ca1/cl1 if ca1 and cl1 else None
        f6=1 if cr0 and cr1 and cr0>=cr1 else 0; score+=f6
        details['F6']={'label':'Current Ratio Tidak Turun','pass':bool(f6),'value':f'{cr0:.2f} vs {cr1:.2f}' if (cr0 and cr1) else '—'}
        f7=1 if sh0 and sh1 and sh0<=sh1*1.02 else 0; score+=f7
        details['F7']={'label':'Tidak Ada Dilusi Saham','pass':bool(f7),'value':f'{sh0/1e9:.2f}B vs {sh1/1e9:.2f}B' if (sh0 and sh1) else '—'}
        gm0=gp0/rev0 if gp0 and rev0 else None; gm1=gp1/rev1 if gp1 and rev1 else None
        f8=1 if gm0 and gm1 and gm0>=gm1 else 0; score+=f8
        details['F8']={'label':'Gross Margin Tidak Turun','pass':bool(f8),'value':f'{gm0*100:.1f}% vs {gm1*100:.1f}%' if (gm0 and gm1) else '—'}
        at0=rev0/ta0 if rev0 and ta0 else None; at1=rev1/ta1 if rev1 and ta1 else None
        f9=1 if at0 and at1 and at0>=at1 else 0; score+=f9
        details['F9']={'label':'Asset Turnover Tidak Turun','pass':bool(f9),'value':f'{at0:.2f}x vs {at1:.2f}x' if (at0 and at1) else '—'}

        rating='KUAT' if score>=7 else 'CUKUP' if score>=5 else 'LEMAH'
        return {'score':score,'max':9,'rating':rating,'details':details}
    except: return None

def calculate_altman_z(ticker):
    """Modified Altman Z-Score for non-manufacturing"""
    try:
        stock = yf.Ticker(f"{ticker}.JK")
        bs, fs = stock.balance_sheet, stock.financials
        if bs is None or bs.empty or fs is None or fs.empty: return None

        def bsv(*keys):
            col=bs.columns[0]
            for key in keys:
                for idx in bs.index:
                    if key.lower() in str(idx).lower():
                        try: v=bs.loc[idx,col]; return None if pd.isna(v) else float(v)
                        except: pass
            return None
        def fsv(*keys):
            col=fs.columns[0]
            for key in keys:
                for idx in fs.index:
                    if key.lower() in str(idx).lower():
                        try: v=fs.loc[idx,col]; return None if pd.isna(v) else float(v)
                        except: pass
            return None

        ta=bsv('total assets'); ca=bsv('current assets'); cl=bsv('current liabilities')
        re=bsv('retained earnings'); te=bsv('stockholders equity','total equity')
        tl=bsv('total liabilities'); ebit=fsv('operating income','ebit')
        if not all([ta,ca,cl,te,tl]) or ta==0 or tl==0: return None

        X1=(ca-cl)/ta; X2=(re or 0)/ta; X3=(ebit or 0)/ta; X4=te/tl
        z=6.56*X1+3.26*X2+6.72*X3+1.05*X4
        zone='AMAN' if z>2.6 else 'WASPADA' if z>1.1 else 'BAHAYA'
        descs={'AMAN':'Risiko kebangkrutan rendah','WASPADA':'Grey zone — perlu monitoring','BAHAYA':'Risiko kebangkrutan tinggi'}
        return {'z_score':round(z,2),'zone':zone,'desc':descs[zone],
                'components':{'X1 (Working Capital/TA)':round(X1,3),'X2 (Retained Earn/TA)':round(X2,3),'X3 (EBIT/TA)':round(X3,3),'X4 (Equity/Liab)':round(X4,3)}}
    except: return None

def calculate_macd_bb(ticker):
    """MACD + Bollinger Bands"""
    try:
        stock = yf.Ticker(f"{ticker}.JK")
        hist = stock.history(period='6mo')['Close']
        if len(hist) < 30: return None
        ema12=hist.ewm(span=12,adjust=False).mean()
        ema26=hist.ewm(span=26,adjust=False).mean()
        macd=ema12-ema26; sig=macd.ewm(span=9,adjust=False).mean(); hst=macd-sig
        sma20=hist.rolling(20).mean(); std20=hist.rolling(20).std()
        upper=sma20+2*std20; lower=sma20-2*std20
        cp=float(hist.iloc[-1]); cm=float(macd.iloc[-1]); cs=float(sig.iloc[-1])
        ch=float(hst.iloc[-1]); ph=float(hst.iloc[-2])
        cu=float(upper.iloc[-1]); cl=float(lower.iloc[-1]); csma=float(sma20.iloc[-1])
        bb_pct=(cp-cl)/(cu-cl) if (cu-cl)!=0 else 0.5
        msig='BULLISH' if cm>cs else 'BEARISH'
        cross='GOLDEN CROSS' if ch>0 and ph<=0 else 'DEATH CROSS' if ch<0 and ph>=0 else None
        bsig='OVERBOUGHT' if cp>cu else 'OVERSOLD' if cp<cl else ('BULLISH' if cp>csma else 'BEARISH')
        return {'macd':{'line':round(cm,2),'signal':round(cs,2),'hist':round(ch,2),'signal_label':msig,'cross':cross},
                'bb':{'upper':round(cu,0),'mid':round(csma,0),'lower':round(cl,0),'pct_b':round(bb_pct,2),'signal':bsig}}
    except: return None

def calculate_rsi(ticker):
    """RSI (14-day)"""
    try:
        hist = yf.Ticker(f"{ticker}.JK").history(period='3mo')['Close']
        if len(hist) < 15: return None
        delta = hist.diff()
        gain = delta.clip(lower=0).rolling(14).mean()
        loss = (-delta.clip(upper=0)).rolling(14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        val = round(float(rsi.iloc[-1]), 1)
        signal = 'OVERBOUGHT' if val > 70 else 'OVERSOLD' if val < 30 else 'NEUTRAL'
        return {'value': val, 'signal': signal}
    except: return None

def calculate_sma(ticker):
    """EMA20, SMA50, SMA200 + Golden/Death Cross"""
    try:
        hist = yf.Ticker(f"{ticker}.JK").history(period='1y')['Close']
        if len(hist) < 50: return None
        price = float(hist.iloc[-1])
        ema20 = round(float(hist.ewm(span=20, adjust=False).mean().iloc[-1]), 0)
        sma50 = round(float(hist.rolling(50).mean().iloc[-1]), 0)
        sma200 = round(float(hist.rolling(200).mean().iloc[-1]), 0) if len(hist) >= 200 else None
        golden_cross = bool(sma50 > sma200) if sma200 else None
        return {
            'price': round(price, 0),
            'ema20': ema20, 'sma50': sma50, 'sma200': sma200,
            'above_sma50': price > sma50,
            'golden_cross': golden_cross
        }
    except: return None

def calculate_sortino(ticker):
    """Sortino Ratio"""
    try:
        hist=yf.Ticker(f"{ticker}.JK").history(period='1y')['Close']
        ret=hist.pct_change().dropna()
        if len(ret)==0: return None
        ann_ret=ret.mean()*252; down=ret[ret<0]
        down_std=down.std()*np.sqrt(252) if len(down)>0 else 0
        return round((ann_ret-0.065)/down_std,3) if down_std else None
    except: return None

def calculate_sharpe(ticker):
    """Sharpe Ratio"""
    try:
        hist=yf.Ticker(f"{ticker}.JK").history(period='1y')['Close']
        ret=hist.pct_change().dropna()
        if len(ret)==0: return None
        ann_ret=ret.mean()*252; ann_std=ret.std()*np.sqrt(252)
        return round((ann_ret-0.065)/ann_std,3) if ann_std else None
    except: return None

def calculate_rvol(ticker):
    """Relative Volume vs 20-day average"""
    try:
        hist=yf.Ticker(f"{ticker}.JK").history(period='3mo')
        if len(hist)<21: return None
        avg=float(hist['Volume'].iloc[:-1].tail(20).mean())
        today=float(hist['Volume'].iloc[-1])
        if avg==0: return None
        rvol=today/avg
        sig='SANGAT TINGGI' if rvol>3 else 'TINGGI' if rvol>2 else 'NORMAL' if rvol>0.7 else 'RENDAH'
        return {'rvol':round(rvol,2),'today':int(today),'avg':int(avg),'signal':sig}
    except: return None

def calculate_fcf_yield(ticker):
    """FCF Yield = Free Cash Flow / Market Cap"""
    try:
        info=yf.Ticker(f"{ticker}.JK").info
        fcf=info.get('freeCashflow'); mcap=info.get('marketCap')
        if not fcf or not mcap or mcap==0: return None
        fcf,mcap=float(fcf),float(mcap); y=fcf/mcap
        sig='MENARIK' if y>0.05 else 'NETRAL' if y>0.02 else ('RENDAH' if y>0 else 'NEGATIF')
        return {'fcf':fcf,'mcap':mcap,'yield':round(y,4),'signal':sig}
    except: return None

def calculate_composite(ticker, info, piotroski, altman, sharpe, sortino, rvol_data):
    """Composite Investment Score 0-100"""
    try:
        pe=min(float(info.get('trailingPE') or 50),100)
        pb=min(float(info.get('priceToBook') or 5),20)
        roe=float(info.get('returnOnEquity') or 0)*100
        cr=float(info.get('currentRatio') or 1)
        de=float(info.get('debtToEquity') or 100)
        val_sc=max(0,min(30,(50-pe)/50*30)) if pe>0 else 0
        prof_sc=min(25,roe*0.8) if roe>0 else 0
        hlth_sc=max(0,min(20,cr/3*20)-(de/100-1)*5 if cr>0 else 0)
        f_base=(val_sc+prof_sc+hlth_sc)/75*100
        p_bonus=(piotroski['score']/9*100) if piotroski else 50
        fund=f_base*0.5+p_bonus*0.5

        mb=calculate_macd_bb(ticker)
        tech=50
        if mb:
            bb_t=max(0,100-mb['bb']['pct_b']*100)
            macd_t=70 if mb['macd']['signal_label']=='BULLISH' else 30
            tech=bb_t*0.5+macd_t*0.5

        risk=50
        if sharpe is not None: risk=max(0,min(80,40+sharpe*15))
        if sortino is not None:
            sor=max(0,min(80,40+sortino*15))
            risk=(risk+sor)/2
        if altman:
            if altman['zone']=='AMAN':   risk=min(100,risk+15)
            elif altman['zone']=='BAHAYA': risk=max(0,risk-30)

        try:
            h=yf.Ticker(f"{ticker}.JK").history(period='1y')['Close']
            m1=(h.iloc[-1]/h.iloc[-22]-1)*100 if len(h)>22 else 0
            m3=(h.iloc[-1]/h.iloc[-66]-1)*100 if len(h)>66 else 0
            m6=(h.iloc[-1]/h.iloc[-126]-1)*100 if len(h)>126 else 0
            mom=max(0,min(100,50+m1*0.3+m3*0.4+m6*0.3))
        except: mom=50

        sent=50
        if rvol_data: sent=max(0,min(90,50+(rvol_data['rvol']-1)*20))
        rec=(info.get('recommendationKey') or '').lower().replace('_','')
        boosts={'strongbuy':20,'buy':10,'hold':0,'neutral':0,'sell':-15,'strongsell':-25}
        sent=max(0,min(100,sent+boosts.get(rec,0)))

        final=round(min(100,max(0,fund*0.30+tech*0.25+risk*0.20+mom*0.15+sent*0.10)),1)
        if   final>=70: sig,cls='STRONG BUY','c-sb'
        elif final>=60: sig,cls='BUY','c-b'
        elif final>=45: sig,cls='HOLD','c-h'
        elif final>=35: sig,cls='SELL','c-s'
        else:           sig,cls='STRONG SELL','c-ss'
        return {'final':final,'signal':sig,'cls':cls,
                'components':{'Fundamental':round(fund,1),'Technical':round(tech,1),'Risk':round(risk,1),'Momentum':round(mom,1),'Sentiment':round(sent,1)}}
    except: return None

# ─── HELPER FUNCTIONS ───
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

# ─── ROUTES ───
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
        stock = yf.Ticker(f"{ticker}.JK")
        info = stock.info

        if not info or not (info.get('regularMarketPrice') or info.get('currentPrice')):
            return jsonify({"error": f"Data emiten {ticker} tidak ditemukan di IHSG."})

        clean = {k: (None if isinstance(v, float) and pd.isna(v) else v) for k, v in info.items()}

        sharpe    = calculate_sharpe(ticker)
        sortino   = calculate_sortino(ticker)
        piotroski = calculate_piotroski(ticker)
        altman    = calculate_altman_z(ticker)
        macd_bb   = calculate_macd_bb(ticker)
        rsi       = calculate_rsi(ticker)
        sma       = calculate_sma(ticker)
        rvol      = calculate_rvol(ticker)
        fcf_yield = calculate_fcf_yield(ticker)
        composite = calculate_composite(ticker, info, piotroski, altman, sharpe, sortino, rvol)

        return jsonify({
            "ticker":        ticker,
            "updated":       datetime.now(timezone(timedelta(hours=7))).strftime("%d/%m/%Y %H:%M WIB"),
            "info":          clean,
            "financials":    df_to_dict(stock.financials),
            "balance_sheet": df_to_dict(stock.balance_sheet),
            "cashflow":      df_to_dict(stock.cashflow),
            "quarterly":     df_to_dict(stock.quarterly_financials),
            "piotroski":     piotroski,
            "altman":        altman,
            "macd_bb":       macd_bb,
            "rsi":           rsi,
            "sma":           sma,
            "rvol":          rvol,
            "fcf_yield":     fcf_yield,
            "sharpe":        sharpe,
            "sortino":       sortino,
            "composite":     composite,
        })
    except Exception as e:
        print(f"ERROR: {str(e)}")
        return jsonify({"error": f"Error teknis: {str(e)}"})

# ─── MAIN ───
if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=8080)
