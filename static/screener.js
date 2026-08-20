/* IDX Screener — renders saved runs, triggers new ones, edits profiles.
   Talks only to /api/screener*; shares no state with app.js. */

var root = document.getElementById('scr-root');
// `active` is the results tab; `sActive` is the settings-modal tab. Sharing one
// variable made switching profiles in settings silently switch the results tab.
var state = { data: null, profiles: null, active: null, sActive: null, poll: null, admin: null };

function esc(s) {
  return String(s == null ? '' : s).replace(/[&<>"]/g, function (c) {
    return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c];
  });
}
function rp(v) {
  if (v == null) return '—';
  return 'Rp ' + Number(v).toLocaleString('id-ID', { maximumFractionDigits: 0 });
}
function pct(v) { return v == null ? '' : (v > 0 ? '+' : '') + v + '%'; }
function el(id) { return document.getElementById(id); }

/* ── cards ── */

function card(b) {
  var o = b.outlook || {};
  var levels = '';
  if (o.entry_mid != null) {
    levels =
      '<div class="scr-levels">' +
        '<div class="scr-lvl"><span class="scr-lvl-label">Entry</span>' +
          '<span class="scr-lvl-val">' + rp(o.entry_low) + '</span>' +
          '<span class="scr-lvl-sub">s/d ' + rp(o.entry_high) + '</span></div>' +
        '<div class="scr-lvl"><span class="scr-lvl-label">Stop</span>' +
          '<span class="scr-lvl-val neg">' + rp(o.stop_loss) + '</span>' +
          '<span class="scr-lvl-sub">−' + o.sl_pct + '%</span></div>' +
        '<div class="scr-lvl"><span class="scr-lvl-label">Target</span>' +
          '<span class="scr-lvl-val pos">' + rp(o.target1) + '</span>' +
          '<span class="scr-lvl-sub">' + pct(o.t1_pct) + ' · R:R ' + o.rr_ratio + '</span></div>' +
      '</div>';
  }
  var chips = (b.reasons || []).map(function (r) {
    var warn = r.indexOf('⚠') === 0 ? ' warn' : '';
    return '<span class="scr-chip' + warn + '">' + esc(r) + '</span>';
  }).join('');

  return '<div class="scr-card' + (b.signal === 'STRONG BUY' ? ' strong' : '') + '">' +
    '<div class="scr-card-top">' +
      '<a class="scr-tk" href="/?ticker=' + encodeURIComponent(b.ticker) + '">' + esc(b.ticker) + '</a>' +
      '<span class="scr-chip">' + esc(b.signal) + '</span>' +
      '<span class="scr-score">' + b.score + '<small>/100</small></span>' +
    '</div>' +
    '<div class="scr-name">' + esc(b.name || '') + ' · ' + rp(b.price) + '</div>' +
    levels +
    '<div class="scr-reasons">' + chips + '</div>' +
  '</div>';
}

/* ── page ── */

function profileBlock(name) {
  var b = state.data.profiles[name];
  if (!b) return '<div class="scr-empty">Profil ini tidak ikut di run tersebut.</div>';
  var s = b.settings || {};

  var warn = b.warn ? '<div class="scr-warn">⚠ ' + esc(b.warn) + '</div>' : '';
  var w = s.weights || {};
  var wsum = Object.keys(w).reduce(function (a, k) { return a + w[k]; }, 0) || 1;
  var wbar = ['fundamental', 'technical', 'risk', 'momentum', 'sentiment']
    .filter(function (k) { return w[k] > 0; })
    .map(function (k) {
      return '<span class="scr-wtag">' + k.slice(0, 4) + ' ' +
        Math.round(w[k] / wsum * 100) + '%</span>';
    }).join('');

  var funnel =
    '<div class="scr-subbar">' +
      '<span class="scr-desc">' + esc(b.desc || '') + '</span>' +
      '<span class="scr-funnel"><b>' + b.eligible + '</b> lolos filter → <b>' +
        b.prescreened + '</b> lolos gate → <b>' +
        (b.total_buys > b.buys.length
          ? b.buys.length + '</b> dari <b>' + b.total_buys
          : b.buys.length) + '</b> BUY</span>' +
      '<span class="scr-wtags">' + wbar +
        '<span class="scr-wtag osc">' + esc(s.oscillator || '') + '</span></span>' +
    '</div>';

  var capped = b.total_buys > b.buys.length
    ? '<div class="scr-capped">Menampilkan ' + b.buys.length + ' teratas dari ' +
      b.total_buys + ' yang lolos ambang. Naikkan <b>Maks hasil</b> di Setelan ' +
      'untuk melihat sisanya.</div>'
    : '';
  var body = b.buys.length
    ? capped + '<div class="scr-grid">' + b.buys.map(card).join('') + '</div>'
    : '<div class="scr-empty">Tidak ada emiten yang lolos ambang ' +
      (s.min_score != null ? s.min_score : '') + ' pada profil ini.</div>';

  var dropped = '';
  if (b.dropped && b.dropped.length) {
    var changed = b.dropped[0] && b.dropped[0].settings_changed;
    dropped = '<div class="scr-dropped"><h3>Keluar dari daftar BUY' +
      (changed ? ' <em>— setelan berubah sejak run sebelumnya, jadi ini belum tentu karena melemah</em>' : '') +
      '</h3><div class="scr-dropped-list">' +
      b.dropped.map(function (x) {
        return '<span class="scr-drop">' + esc(x.ticker) + ' <s>' +
          (x.prev_score != null ? x.prev_score : '—') + '</s> → ' +
          (x.score != null ? x.score : '—') + '</span>';
      }).join('') + '</div></div>';
  }
  return warn + funnel + body + dropped;
}

function render() {
  var d = state.data;
  if (!d || d.error) {
    root.innerHTML = '<div class="scr-empty">' + esc((d && d.error) || 'Gagal memuat.') + '</div>';
    return;
  }
  var names = Object.keys(d.profiles || {});
  if (!state.active || names.indexOf(state.active) < 0) state.active = names[0];

  var picker = (d.available_dates || []).length > 1
    ? '<select class="scr-picker" id="scr-date">' + d.available_dates.map(function (dt) {
        return '<option value="' + esc(dt) + '"' + (dt === d.date ? ' selected' : '') +
          '>' + esc(dt) + '</option>';
      }).join('') + '</select>'
    : esc(d.date);

  var meta =
    '<div class="scr-meta">' +
      '<div class="scr-meta-item"><span class="scr-meta-label">Tanggal</span>' +
        '<span class="scr-meta-val">' + picker + '</span></div>' +
      '<div class="scr-meta-item"><span class="scr-meta-label">Universe</span>' +
        '<span class="scr-meta-val">' + d.universe + '</span></div>' +
      '<div class="scr-meta-item"><span class="scr-meta-label">Dianalisis</span>' +
        '<span class="scr-meta-val">' + d.analysed + '</span></div>' +
      '<div class="scr-meta-item"><span class="scr-meta-label">Durasi</span>' +
        '<span class="scr-meta-val">' + d.elapsed_sec + 's</span></div>' +
      (d.failed && d.failed.length
        ? '<div class="scr-meta-item"><span class="scr-meta-label">Gagal</span>' +
          '<span class="scr-meta-val neg">' + d.failed.length + '</span></div>' : '') +
    '</div>';

  var tabs = '<div class="scr-tabs">' + names.map(function (n) {
    var b = d.profiles[n];
    return '<button class="scr-tab' + (n === state.active ? ' active' : '') +
      '" data-p="' + esc(n) + '">' + esc(b.label) +
      '<span class="scr-tab-n">' + b.buys.length + '</span></button>';
  }).join('') + '</div>';

  root.innerHTML = meta + tabs + '<div id="scr-body">' + profileBlock(state.active) + '</div>';

  Array.prototype.forEach.call(root.querySelectorAll('.scr-tab'), function (t) {
    t.addEventListener('click', function () {
      state.active = t.getAttribute('data-p');
      render();
    });
  });
  var sel = el('scr-date');
  if (sel) sel.addEventListener('change', function () { load(sel.value); });
}

/* ── run + progress ── */

function applyAdmin(isAdmin) {
  if (state.admin === isAdmin) return;
  state.admin = isAdmin;
  ['scr-run', 'scr-settings'].forEach(function (id) {
    var b = el(id);
    if (!b) return;
    b.disabled = !isAdmin;
    b.title = isAdmin ? '' :
      'Hanya bisa dari server itu sendiri. Pakai SSH tunnel: ' +
      'ssh -L 8080:127.0.0.1:8080 user@vps';
  });
  var note = el('scr-readonly');
  if (note) note.style.display = isAdmin ? 'none' : 'block';
}

function setRunning(on, text) {
  var btn = el('scr-run');
  if (!btn) return;
  if (!state.admin) { btn.disabled = true; return; }
  btn.disabled = on;
  btn.textContent = on ? (text || 'Berjalan…') : '▶ Jalankan';
  var bar = el('scr-progress');
  if (bar) bar.style.display = on ? 'block' : 'none';
}

function pollStatus() {
  fetch('/api/screener/status').then(function (r) { return r.json(); }).then(function (s) {
    applyAdmin(!!s.admin);
    if (s.state === 'running') {
      var label = s.stage === 'analyse' && s.total
        ? 'Analisis ' + s.done + '/' + s.total + (s.ticker ? ' · ' + s.ticker : '')
        : s.stage === 'prescreen' && s.total
          ? 'Prescreen ' + s.done + '/' + s.total
          : 'Tahap: ' + (s.stage || '…');
      setRunning(true, label);
      var fill = el('scr-progress-fill');
      if (fill && s.total) fill.style.width = Math.round(s.done / s.total * 100) + '%';
      return;
    }
    clearInterval(state.poll); state.poll = null;
    setRunning(false);
    if (s.state === 'error') {
      alertBar('Run gagal: ' + (s.error || s.stage), true);
    } else if (s.state === 'done') {
      alertBar('Selesai dalam ' + s.elapsed_sec + 's.', false);
      load();
    }
  }).catch(function () { /* keep polling; a blip is not a failure */ });
}

function startPolling() {
  if (state.poll) return;
  state.poll = setInterval(pollStatus, 2000);
  pollStatus();
}

function alertBar(msg, isErr) {
  var a = el('scr-alert');
  if (!a) return;
  a.textContent = msg;
  a.className = 'scr-alert' + (isErr ? ' err' : ' ok');
  a.style.display = 'block';
  setTimeout(function () { a.style.display = 'none'; }, 8000);
}

function runNow() {
  setRunning(true, 'Memulai…');
  fetch('/api/screener/run', {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({})
  }).then(function (r) { return r.json().then(function (d) { return { ok: r.ok, d: d }; }); })
    .then(function (res) {
      if (!res.ok) {
        setRunning(false);
        applyAdmin(res.d.hint ? false : state.admin);
        alertBar((res.d.error || 'Gagal.') + (res.d.hint ? ' ' + res.d.hint : ''), true);
        return;
      }
      startPolling();
    }).catch(function (e) { setRunning(false); alertBar('Gagal: ' + e.message, true); });
}

/* ── settings ── */

var W_KEYS = ['fundamental', 'technical', 'risk', 'momentum', 'sentiment'];

function num(v) { return v == null || v === '' ? null : Number(v); }

function settingsForm(name, p) {
  var u = p.universe || {}, g = p.prescreen || {}, w = p.weights || {};
  function row(label, hint, input) {
    return '<label class="scr-field"><span class="scr-field-label">' + label +
      (hint ? '<em>' + hint + '</em>' : '') + '</span>' + input + '</label>';
  }
  function inp(id, val, attrs) {
    return '<input id="' + id + '" value="' + (val == null ? '' : val) + '" ' +
      (attrs || 'type="number"') + '>';
  }
  return '<div class="scr-form" data-p="' + esc(name) + '">' +
    '<div class="scr-form-grid">' +
      row('Likuiditas min', 'Rp miliar/hari', inp('f-turn', Math.round((u.min_turnover || 0) / 1e9)) ) +
      row('Harga min', 'kosong = bebas', inp('f-pmin', u.min_price)) +
      row('Harga maks', 'kosong = bebas', inp('f-pmax', u.max_price)) +
      row('Skor min', '0-100', inp('f-score', p.min_score)) +
      row('Maks hasil', '', inp('f-max', p.max_results)) +
      row('Gate EMA', '50 / 200 / kosong',
        '<select id="f-ema">' +
        ['', '50', '200'].map(function (v) {
          var lbl = v === '' ? 'mati' : 'di atas EMA' + v;
          return '<option value="' + v + '"' +
            (String(g.above_ema == null ? '' : g.above_ema) === v ? ' selected' : '') +
            '>' + lbl + '</option>';
        }).join('') + '</select>') +
      row('Gate RSI maks', 'buang yang sudah terlalu tinggi', inp('f-rsi', g.rsi_max)) +
      row('Kurva osilator', 'cara membaca RSI/Stoch/%B',
        '<select id="f-osc">' +
        [['mean_reversion', 'mean reversion — puncak di RSI 65'],
         ['momentum', 'momentum — makin tinggi makin baik']].map(function (o) {
          return '<option value="' + o[0] + '"' + (p.oscillator === o[0] ? ' selected' : '') +
            '>' + o[1] + '</option>';
        }).join('') + '</select>') +
    '</div>' +
    '<div class="scr-form-w"><span class="scr-field-label">Bobot pilar<em>0 = diabaikan; dinormalisasi otomatis</em></span>' +
      '<div class="scr-wgrid">' + W_KEYS.map(function (k) {
        return '<label class="scr-wcell"><span>' + k.slice(0, 4) + '</span>' +
          '<input id="f-w-' + k + '" type="number" step="0.01" min="0" value="' +
          (w[k] != null ? w[k] : 0) + '"></label>';
      }).join('') + '</div>' +
      '<div class="scr-wsum" id="f-wsum"></div>' +
    '</div>' +
    '<div class="scr-form-actions">' +
      '<button class="scr-btn ghost" id="f-reset">Kembalikan bawaan</button>' +
      '<button class="scr-btn" id="f-save">Simpan</button>' +
    '</div>' +
  '</div>';
}

function openSettings() {
  fetch('/api/screener/profiles').then(function (r) { return r.json(); }).then(function (d) {
    if (d.error) { alertBar(d.error, true); return; }
    state.profiles = d.profiles;
    var names = Object.keys(d.profiles);
    state.sActive = names.indexOf(state.active) >= 0 ? state.active : names[0];
    var m = el('scr-modal');
    m.innerHTML =
      '<div class="scr-modal-box">' +
        '<div class="scr-modal-head"><h2>Setelan Profil</h2>' +
          '<button class="scr-x" id="f-close">✕</button></div>' +
        '<div class="scr-tabs inner">' + names.map(function (n) {
          return '<button class="scr-tab' + (n === state.sActive ? ' active' : '') +
            '" data-p="' + esc(n) + '">' + esc(d.profiles[n].label) + '</button>';
        }).join('') + '</div>' +
        '<div id="f-body">' + settingsForm(state.sActive, d.profiles[state.sActive]) + '</div>' +
      '</div>';
    m.style.display = 'flex';
    wireSettings();
  });
}

function wireSettings() {
  var m = el('scr-modal');
  el('f-close').onclick = function () { m.style.display = 'none'; };
  m.onclick = function (e) { if (e.target === m) m.style.display = 'none'; };
  Array.prototype.forEach.call(m.querySelectorAll('.scr-tab'), function (t) {
    t.onclick = function () {
      state.sActive = t.getAttribute('data-p');
      el('f-body').innerHTML = settingsForm(state.sActive, state.profiles[state.sActive]);
      Array.prototype.forEach.call(m.querySelectorAll('.scr-tab'), function (x) {
        x.className = 'scr-tab' + (x.getAttribute('data-p') === state.sActive ? ' active' : '');
      });
      wireForm();
    };
  });
  wireForm();
}

function readForm() {
  var w = {};
  W_KEYS.forEach(function (k) { w[k] = Number(el('f-w-' + k).value) || 0; });
  var ema = el('f-ema').value;
  return {
    universe: {
      min_turnover: (Number(el('f-turn').value) || 0) * 1e9,
      min_price: num(el('f-pmin').value),
      max_price: num(el('f-pmax').value)
    },
    prescreen: { above_ema: ema === '' ? null : Number(ema), rsi_max: num(el('f-rsi').value) },
    weights: w,
    oscillator: el('f-osc').value,
    min_score: Number(el('f-score').value),
    max_results: Number(el('f-max').value)
  };
}

function showSum() {
  var t = 0;
  W_KEYS.forEach(function (k) { t += Number(el('f-w-' + k).value) || 0; });
  var out = el('f-wsum');
  if (t <= 0) { out.innerHTML = '<span class="neg">Total bobot nol — skor tidak terdefinisi.</span>'; return; }
  out.innerHTML = W_KEYS.map(function (k) {
    var v = Number(el('f-w-' + k).value) || 0;
    return k.slice(0, 4) + ' <b>' + Math.round(v / t * 100) + '%</b>';
  }).join(' · ');
}

function wireForm() {
  W_KEYS.forEach(function (k) { el('f-w-' + k).oninput = showSum; });
  showSum();
  el('f-save').onclick = function (e) {
    e.preventDefault();
    var patch = {}; patch[state.sActive] = readForm();
    fetch('/api/screener/profiles', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(patch)
    }).then(function (r) { return r.json().then(function (d) { return { ok: r.ok, d: d }; }); })
      .then(function (res) {
        if (!res.ok) {
          alertBar((res.d.error || 'Gagal menyimpan.') + (res.d.hint ? ' ' + res.d.hint : ''), true);
          return;
        }
        state.profiles = res.d.profiles;
        alertBar('Setelan "' + state.sActive + '" tersimpan. Jalankan ulang untuk melihat efeknya.', false);
        el('scr-modal').style.display = 'none';
      });
  };
  el('f-reset').onclick = function (e) {
    e.preventDefault();
    var patch = {}; patch[state.sActive] = {};
    fetch('/api/screener/profiles', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(patch)
    }).then(function (r) { return r.json(); }).then(function (d) {
      if (d.error) { alertBar(d.error, true); return; }
      state.profiles = d.profiles;
      el('f-body').innerHTML = settingsForm(state.sActive, d.profiles[state.sActive]);
      wireForm();
      alertBar('Profil "' + state.sActive + '" dikembalikan ke bawaan.', false);
    });
  };
}

/* ── boot ── */

function load(date) {
  root.innerHTML = '<p class="no-data">Memuat…</p>';
  fetch('/api/screener' + (date ? '?date=' + encodeURIComponent(date) : ''))
    .then(function (r) { return r.json(); })
    .then(function (d) { state.data = d; render(); })
    .catch(function (e) {
      root.innerHTML = '<div class="scr-empty">Gagal memuat: ' + esc(e.message) + '</div>';
    });
}

el('scr-run').addEventListener('click', runNow);
el('scr-settings').addEventListener('click', openSettings);
load();
// A run started from cron or another tab should show up here too.
fetch('/api/screener/status').then(function (r) { return r.json(); }).then(function (s) {
  applyAdmin(!!s.admin);
  if (s.state === 'running') startPolling();
});
