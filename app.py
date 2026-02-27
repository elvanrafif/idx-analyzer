from flask import Flask, render_template_string, jsonify, request
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, timezone

app = Flask(__name__)

# ─── FRONTEND HTML ───
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
@keyframes pulse{0%,100%{opacity:1;transform:scaleY(1);}50%{opacity:.7;transform:scaleY(0.9);}}
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
.search-wrap{display:flex;margin-bottom:36px;position:relative;width:100%;align-items:stretch;}
.search-prefix{position:absolute;left:18px;top:50%;transform:translateY(-50%);font-family:'Space Mono',monospace;font-size:13px;color:var(--accent);font-weight:700;z-index:1;pointer-events:none;transition:color .3s;}
#ticker-input{flex:1;background:var(--surface);border:1.5px solid var(--border);border-right:none;color:var(--text);font-family:'Space Mono',monospace;font-size:20px;font-weight:700;padding:18px 18px 18px 62px;outline:none;letter-spacing:3px;text-transform:uppercase;transition:border-color .2s,background .3s,color .3s;border-radius:4px 0 0 4px;min-width:0;}
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
.section-header:hover{background:rgba(128,128,255,0.04);}
.section-icon{font-size:14px;width:28px;height:28px;display:flex;align-items:center;justify-content:center;background:var(--surface2);border-radius:4px;flex-shrink:0;transition:background .3s;}
.section-title{font-size:11px;font-weight:700;letter-spacing:2px;text-transform:uppercase;flex:1;}
.section-toggle{font-size:13px;color:var(--muted);transition:transform .2s;}
.section.collapsed .section-toggle{transform:rotate(-90deg);}
.section.collapsed .section-body{display:none;}

/* DATA TABLE */
.data-table{width:100%;border-collapse:collapse;}
.data-table td{padding:10px 20px;font-size:12px;border-bottom:1px solid rgba(128,128,128,0.07);vertical-align:middle;transition:background .15s;}
.data-table tr:last-child td{border-bottom:none;}
.data-table tr:hover td{background:rgba(128,128,255,0.04);}
.td-label{color:var(--muted);font-family:'Space Mono',monospace;font-size:11px;letter-spacing:0.5px;width:38%;}
.td-val{font-weight:600;font-family:'Space Mono',monospace;font-size:12px;text-align:right;width:24%;}
.td-rating{width:38%;padding-left:12px;}
.badge{display:inline-block;font-size:10px;padding:3px 8px;border-radius:2px;font-family:'Syne',sans-serif;font-weight:600;}
.bg{background:rgba(0,200,100,0.12);color:var(--accent);}
.by{background:rgba(255,200,0,0.12);color:#cc9900;}
.bo{background:rgba(255,107,53,0.12);color:var(--warn);}
.br{background:rgba(255,51,85,0.12);color:var(--red);}
.bb{background:rgba(0,136,255,0.12);color:var(--accent2);}

/* STATS GRID */
.stats-grid{display:grid;grid-template-columns:1fr 1fr;}
.stat-item{padding:11px 20px;border-bottom:1px solid rgba(128,128,128,0.07);border-right:1px solid rgba(128,128,128,0.07);display:flex;justify-content:space-between;align-items:center;transition:background .15s;}
.stat-item:nth-child(2n){border-right:none;}
.stat-item:nth-last-child(-n+2){border-bottom:none;}
.stat-item:hover{background:rgba(128,128,255,0.04);}
.sl{font-family:'Space Mono',monospace;font-size:10px;color:var(--muted);letter-spacing:0.5px;}
.sv{font-family:'Space Mono',monospace;font-size:12px;font-weight:700;}

/* FIN TABLE & SCROLL WRAPPER */
.table-scroll {
  width: 100%;
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
}
.fin-table{width: 100%; min-width: 600px; border-collapse:collapse;}
.fin-table th,.fin-table td{padding:10px 16px;font-size:12px;border-bottom:1px solid rgba(128,128,128,0.07);font-family:'Space Mono',monospace;}
.fin-table th{background:var(--surface2);color:var(--muted);font-size:10px;letter-spacing:1px;text-transform:uppercase;text-align:right;font-weight:400;transition:background .3s;}
.fin-table th:first-child{text-align:left;color:var(--text); position: sticky; left: 0; z-index: 2; background: var(--surface2);}
.fin-table td:first-child{color:var(--muted);font-size:11px; position: sticky; left: 0; z-index: 1; background: var(--card);}
.fin-table td:not(:first-child){text-align:right;font-weight:600;}
.fin-table tr:hover td{background:rgba(128,128,255,0.04);}
.pos{color:var(--accent);} .neg{color:var(--red);} .na{color:var(--muted);opacity:0.4;}

/* ANALYST */
.analyst-wrap{padding:20px;display:flex;align-items:center;gap:16px;flex-wrap:wrap;justify-content:space-between;}
.rec-badge{font-size:15px;font-weight:800;padding:10px 18px;border-radius:4px;letter-spacing:1px;text-transform:uppercase;}
.SB,.STRONGBUY{background:rgba(0,255,136,0.1);color:var(--accent);border:1px solid var(--accent);}
.B{background:rgba(0,200,100,0.1);color:#00cc66;border:1px solid #00cc66;}
.H,.N{background:rgba(255,200,0,0.1);color:#cc9900;border:1px solid #cc9900;}
.S{background:rgba(255,51,85,0.1);color:var(--red);border:1px solid var(--red);}
.SS{background:rgba(180,0,30,0.1);color:#ff0033;border:1px solid #ff0033;}
.NA2{background:var(--surface2);color:var(--muted);border:1px solid var(--border);}
.rec-info{font-family:'Space Mono',monospace;font-size:11px;color:var(--muted);line-height:2.2;}

.desc-text{padding:20px;font-size:13px;line-height:1.8;color:var(--muted);}
.no-data{padding:20px;font-family:'Space Mono',monospace;font-size:11px;color:var(--muted);letter-spacing:0.5px;}

.footer{margin-top:48px;padding-top:20px;border-top:1px solid var(--border);font-family:'Space Mono',monospace;font-size:10px;color:var(--muted);letter-spacing:1px;text-align:center;line-height:2.2;transition:border-color .3s;}

::-webkit-scrollbar{width:5px; height: 5px;}
::-webkit-scrollbar-track{background:var(--bg);}
::-webkit-scrollbar-thumb{background:var(--border);border-radius:3px;}

@media(max-width:640px){
  .header{flex-direction: column; align-items: flex-start; gap: 24px;}
  .header-left { width: 100%; justify-content: space-between; }
  
  .search-wrap { flex-direction: column; gap: 12px; }
  .search-prefix { top: 18px; transform: none; } 
  #ticker-input { 
    border-right: 1.5px solid var(--border) !important; 
    border-radius: 4px !important; 
    padding: 18px 18px 18px 62px;
    width: 100%; 
  }
  #search-btn { border-radius: 4px !important; width: 100%; transform: none !important; }

  .analyst-wrap { gap: 12px; }
  .analyst-wrap div:last-child { text-align: left !important; flex: none; width: 100%; }

  .stock-hero{grid-template-columns:1fr; padding: 20px;}
  .price-block{text-align:left;}
  .stats-grid{grid-template-columns:1fr;}
  .stat-item{border-right:none;}
  .stat-item:nth-last-child(-n+2){border-bottom:1px solid rgba(128,128,128,0.07);}
  .stat-item:last-child{border-bottom:none;}
  
  .td-label { width: 50%; }
  .td-val { width: 50%; }
  .td-rating { display: none; }
  .tech-wrap{grid-template-columns:1fr;}
  .fscore-grid{grid-template-columns:1fr;}
  .fscore-item:nth-child(odd){border-right:none;}
  .composite-card{flex-direction:column;align-items:flex-start;}
}
/* COMPOSITE SCORE */
.composite-card{padding:24px 20px;display:flex;align-items:center;gap:24px;flex-wrap:wrap;}
.composite-score-num{font-family:'Space Mono',monospace;font-size:56px;font-weight:700;line-height:1;}
.composite-info{flex:1;min-width:160px;}
.composite-signal{font-size:14px;font-weight:800;letter-spacing:2px;text-transform:uppercase;padding:6px 14px;border-radius:4px;display:inline-block;margin-bottom:10px;}
.c-sb{background:rgba(0,255,136,0.15);color:var(--accent);border:1px solid var(--accent);}
.c-b{background:rgba(0,200,100,0.12);color:#00cc66;border:1px solid #00cc66;}
.c-h{background:rgba(255,200,0,0.12);color:#cc9900;border:1px solid #cc9900;}
.c-s{background:rgba(255,51,85,0.10);color:var(--red);border:1px solid var(--red);}
.c-ss{background:rgba(180,0,30,0.12);color:#ff0033;border:1px solid #ff0033;}
.composite-bars{display:grid;gap:6px;flex:2;min-width:220px;}
.cbar-row{display:flex;align-items:center;gap:8px;}
.cbar-label{font-family:'Space Mono',monospace;font-size:10px;color:var(--muted);width:90px;flex-shrink:0;}
.cbar-track{flex:1;height:6px;background:var(--surface2);border-radius:3px;overflow:hidden;}
.cbar-fill{height:100%;border-radius:3px;background:linear-gradient(90deg,var(--red),var(--warn) 50%,var(--accent));transition:width .4s;}
.cbar-val{font-family:'Space Mono',monospace;font-size:10px;color:var(--muted);width:28px;text-align:right;}
/* PIOTROSKI */
.fscore-header{display:flex;align-items:center;gap:16px;padding:16px 20px 8px;}
.fscore-num{font-family:'Space Mono',monospace;font-size:44px;font-weight:700;line-height:1;}
.fscore-rating{font-size:11px;font-weight:700;padding:4px 10px;border-radius:2px;letter-spacing:1px;}
.fscore-kuat{background:rgba(0,255,136,0.12);color:var(--accent);}
.fscore-cukup{background:rgba(255,200,0,0.12);color:#cc9900;}
.fscore-lemah{background:rgba(255,51,85,0.12);color:var(--red);}
.fscore-grid{display:grid;grid-template-columns:1fr 1fr;padding:0 20px 16px;gap:0;}
.fscore-item{display:flex;align-items:center;gap:8px;padding:7px 0;border-bottom:1px solid rgba(128,128,128,0.07);font-size:11px;}
.fscore-item:nth-child(odd){border-right:1px solid rgba(128,128,128,0.07);padding-right:12px;}
.fscore-item:nth-child(even){padding-left:12px;}
.fscore-check{width:16px;height:16px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:9px;flex-shrink:0;}
.fscore-pass{background:rgba(0,255,136,0.15);color:var(--accent);}
.fscore-fail{background:rgba(255,51,85,0.10);color:var(--red);}
.fscore-label{font-family:'Space Mono',monospace;font-size:10px;color:var(--muted);flex:1;}
.fscore-val{font-family:'Space Mono',monospace;font-size:10px;color:var(--text);}
/* ALTMAN Z */
.altman-wrap{padding:20px;display:flex;align-items:center;gap:20px;flex-wrap:wrap;}
.altman-score{font-family:'Space Mono',monospace;font-size:48px;font-weight:700;line-height:1;}
.altman-zone{font-size:11px;font-weight:700;padding:4px 10px;border-radius:2px;letter-spacing:1px;margin-top:6px;display:inline-block;}
.altman-aman{background:rgba(0,255,136,0.12);color:var(--accent);}
.altman-waspada{background:rgba(255,200,0,0.12);color:#cc9900;}
.altman-bahaya{background:rgba(255,51,85,0.12);color:var(--red);}
.altman-gauge{flex:1;min-width:200px;}
.altman-scale{display:flex;height:10px;border-radius:5px;overflow:hidden;margin:8px 0 4px;}
.altman-red{background:var(--red);flex:1.1;}.altman-yellow{background:#cc9900;flex:1.5;}.altman-green{background:var(--accent);flex:2.5;}
.altman-labels{display:flex;justify-content:space-between;font-family:'Space Mono',monospace;font-size:9px;color:var(--muted);}
/* MACD + BB */
.tech-wrap{padding:16px 20px 20px;display:grid;grid-template-columns:1fr 1fr;gap:16px;}
.tech-card{background:var(--surface2);border-radius:4px;padding:14px;}
.tech-card-title{font-family:'Space Mono',monospace;font-size:10px;color:var(--muted);letter-spacing:1px;margin-bottom:10px;text-transform:uppercase;}
.tech-sig{font-size:12px;font-weight:700;padding:4px 10px;border-radius:2px;letter-spacing:1px;display:inline-block;margin-bottom:8px;}
.sig-bullish{background:rgba(0,255,136,0.12);color:var(--accent);}
.sig-bearish{background:rgba(255,51,85,0.10);color:var(--red);}
.sig-overbought{background:rgba(255,107,53,0.12);color:var(--warn);}
.sig-oversold{background:rgba(0,136,255,0.12);color:var(--accent2);}
.sig-netral{background:var(--surface);color:var(--muted);}
.sig-golden{background:rgba(0,255,136,0.15);color:var(--accent);border:1px solid var(--accent);}
.sig-death{background:rgba(255,51,85,0.12);color:var(--red);border:1px solid var(--red);}
.tech-row{display:flex;justify-content:space-between;font-family:'Space Mono',monospace;font-size:11px;padding:3px 0;border-bottom:1px solid rgba(128,128,128,0.07);}
.tech-row:last-child{border-bottom:none;}
.tech-row-label{color:var(--muted);}
/* RVOL */
.rvol-wrap{padding:20px;display:flex;align-items:center;gap:20px;}
.rvol-num{font-family:'Space Mono',monospace;font-size:52px;font-weight:700;line-height:1;}
.rvol-bar-wrap{flex:1;}
.rvol-bar-track{height:8px;background:var(--surface2);border-radius:4px;overflow:hidden;margin:8px 0;}
.rvol-bar-fill{height:100%;background:linear-gradient(90deg,var(--accent2),var(--accent));border-radius:4px;transition:width .4s;}
.rvol-sig{font-size:11px;font-weight:700;padding:3px 8px;border-radius:2px;letter-spacing:1px;display:inline-block;}
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
applyTheme(localStorage.getItem('idx-theme') || 'dark');
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
function renderComposite(c) {
  if (!c) return '<p class="no-data">Data composite tidak tersedia.</p>';
  const weights = {Fundamental:'30%',Technical:'25%',Risk:'20%',Momentum:'15%',Sentiment:'10%'};
  return `<div class="composite-card">
    <div>
      <div class="composite-score-num ${c.final>=70?'pos':c.final<35?'neg':''}">${c.final}</div>
      <div style="font-family:'Space Mono',monospace;font-size:10px;color:var(--muted);margin-top:4px;">/ 100</div>
    </div>
    <div class="composite-info">
      <div class="composite-signal ${c.cls}">${c.signal}</div>
      <div style="font-family:'Space Mono',monospace;font-size:10px;color:var(--muted);">Skor Keputusan Komprehensif</div>
    </div>
    <div class="composite-bars">
      ${Object.entries(c.components).map(([name,val])=>`<div class="cbar-row">
        <span class="cbar-label">${name.toUpperCase()} <span style="opacity:.5">${weights[name]||''}</span></span>
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
    <div class="fscore-num ${p.score>=7?'pos':p.score>=5?'':'neg'}">${p.score}<span style="font-size:20px;color:var(--muted)">/9</span></div>
    <div>
      <div class="fscore-rating ${rCls}">${p.rating}</div>
      <div style="font-family:'Space Mono',monospace;font-size:10px;color:var(--muted);margin-top:4px;">Piotroski F-Score</div>
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
      <div style="font-family:'Space Mono',monospace;font-size:10px;color:var(--muted);margin-top:6px;">${a.desc}</div>
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
function renderMacdBb(mb) {
  if (!mb) return '<p class="no-data">Data historis tidak cukup.</p>';
  const m=mb.macd, b=mb.bb;
  const ms=(m.signal_label||'').toLowerCase(), bs=(b.signal||'').toLowerCase();
  const sc={bullish:'sig-bullish',bearish:'sig-bearish',overbought:'sig-overbought',oversold:'sig-oversold',netral:'sig-netral'};
  const cross = m.cross ? `<div class="tech-sig ${m.cross.includes('GOLDEN')?'sig-golden':'sig-death'}" style="margin-top:6px">${m.cross}</div>` : '';
  return `<div class="tech-wrap">
    <div class="tech-card">
      <div class="tech-card-title">MACD (12,26,9)</div>
      <div class="tech-sig ${sc[ms]||'sig-netral'}">${m.signal_label}</div>${cross}
      <div class="tech-row"><span class="tech-row-label">MACD Line</span><span>${m.line}</span></div>
      <div class="tech-row"><span class="tech-row-label">Signal Line</span><span>${m.signal}</span></div>
      <div class="tech-row"><span class="tech-row-label">Histogram</span><span class="${m.hist>0?'pos':'neg'}">${m.hist}</span></div>
    </div>
    <div class="tech-card">
      <div class="tech-card-title">Bollinger Bands (20,2)</div>
      <div class="tech-sig ${sc[bs]||'sig-netral'}">${b.signal}</div>
      <div class="tech-row"><span class="tech-row-label">Upper Band</span><span class="neg">Rp ${b.upper.toLocaleString('id')}</span></div>
      <div class="tech-row"><span class="tech-row-label">Middle (SMA20)</span><span>Rp ${b.mid.toLocaleString('id')}</span></div>
      <div class="tech-row"><span class="tech-row-label">Lower Band</span><span class="pos">Rp ${b.lower.toLocaleString('id')}</span></div>
      <div class="tech-row"><span class="tech-row-label">%B Position</span><span>${(b.pct_b*100).toFixed(0)}%</span></div>
    </div>
  </div>`;
}
function renderRvol(rv) {
  if (!rv) return '<p class="no-data">Data volume tidak tersedia.</p>';
  const sc = rv.signal==='SANGAT TINGGI'?'bg':rv.signal==='TINGGI'?'by':rv.signal==='NORMAL'?'bb':'br';
  const barW = Math.min(100, rv.rvol/4*100);
  return `<div class="rvol-wrap">
    <div>
      <div class="rvol-num ${rv.rvol>=2?'pos':rv.rvol<0.7?'neg':''}">${rv.rvol}x</div>
      <div class="rvol-sig badge ${sc}" style="margin-top:6px">${rv.signal}</div>
    </div>
    <div class="rvol-bar-wrap">
      <div style="font-family:'Space Mono',monospace;font-size:10px;color:var(--muted)">Relative Volume vs 20d Avg</div>
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
    <div class="rec-info" style="flex: 1; text-align: right; min-width: 100px;">
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
      ${sec('🏆','COMPOSITE SCORE — Skor Keputusan Investasi', renderComposite(d.composite))}
      ${sec('📊','PIOTROSKI F-SCORE — Kekuatan Finansial (0–9)', renderPiotroski(d.piotroski))}
      ${sec('⚠️','ALTMAN Z-SCORE — Risiko Kebangkrutan', renderAltman(d.altman))}
      ${sec('📉','TECHNICAL — MACD & Bollinger Bands', renderMacdBb(d.macd_bb))}
      ${sec('📦','RELATIVE VOLUME — Deteksi Akumulasi/Distribusi', renderRvol(d.rvol))}
      ${sec('💎','RISK-ADJUSTED RETURN — FCF Yield, Sharpe & Sortino', renderRiskAdj(d.fcf_yield, d.sortino, d.sharpe))}
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
        rvol      = calculate_rvol(ticker)
        fcf_yield = calculate_fcf_yield(ticker)
        composite = calculate_composite(ticker, info, piotroski, altman, sharpe, sortino, rvol)

        return jsonify({
            "ticker":        ticker,
            "updated":       datetime.now(timezone(timedelta(hours=7))).strftime("%d/%m/%Y %H:%M"),
            "info":          clean,
            "financials":    df_to_dict(stock.financials),
            "balance_sheet": df_to_dict(stock.balance_sheet),
            "cashflow":      df_to_dict(stock.cashflow),
            "quarterly":     df_to_dict(stock.quarterly_financials),
            "piotroski":     piotroski,
            "altman":        altman,
            "macd_bb":       macd_bb,
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