"""Screener profiles — named strategies, not loose knobs.

Each profile answers four questions with one coherent set of numbers:

  universe   which stocks are even eligible
  prescreen  which of those are worth the expensive fundamental fetch
  weights    how much each pillar moves the score
  oscillator how to read RSI/Stochastic/MFI/%R/%B

The last one matters more than it looks. `mean_reversion` peaks at RSI 65 and
punishes anything above 80; `momentum` does the opposite. A momentum profile
running the mean_reversion curve would vote against every stock it is meant to
find, so weights alone cannot express these strategies.

User edits land in profiles.json (gitignored) and are merged over these
defaults, so a bad edit degrades to shipped behaviour instead of crashing.
"""
import copy
import json
from pathlib import Path

OVERRIDES_PATH = Path(__file__).parent / 'profiles.json'

BUILTIN = {
    'default': {
        'label': 'Default',
        'desc': 'Seimbang. Fundamental dan teknikal sama-sama dihitung.',
        'order': 1,
        'universe': {
            'min_turnover': 10e9,   # Rp/hari
            'min_price': None,
            'max_price': None,
            'exclude_sectors': [],
            'exclude_tickers': [],
        },
        'prescreen': {'above_ema': 50, 'rsi_max': 78, 'min_rvol': None},
        'weights': {
            'fundamental': 0.28, 'technical': 0.32, 'risk': 0.20,
            'momentum': 0.13, 'sentiment': 0.07,
        },
        'oscillator': 'mean_reversion',
        'min_score': 60,
        'max_results': 40,
    },

    'value': {
        'label': 'Value',
        'desc': 'Untuk investor. Fundamental dominan, momentum hampir diabaikan.',
        'order': 2,
        'universe': {
            'min_turnover': 5e9,
            'min_price': 100,       # gocap tidak masuk tesis value
            'max_price': None,
            'exclude_sectors': [],
            'exclude_tickers': [],
        },
        # No trend gate: a cheap healthy company below its EMA50 is exactly
        # what this profile wants to see.
        'prescreen': {'above_ema': None, 'rsi_max': 70, 'min_rvol': None},
        'weights': {
            'fundamental': 0.55, 'technical': 0.10, 'risk': 0.25,
            'momentum': 0.05, 'sentiment': 0.05,
        },
        'oscillator': 'mean_reversion',
        'min_score': 62,
        'max_results': 40,
        # Quality gate: no F-Score, no verdict -- EXCEPT for banks/insurers,
        # where Piotroski is undefined by construction. Requiring it outright
        # would silently lock every IDX bank out of the value screen.
        'require': ['fundamental_quality'],
    },

    'breakout': {
        'label': 'Breakout',
        'desc': 'Momentum di saham likuid. Tanpa batas harga.',
        'order': 3,
        'universe': {
            'min_turnover': 10e9,
            'min_price': None,
            'max_price': None,
            'exclude_sectors': [],
            'exclude_tickers': [],
        },
        # min_rvol is the false-breakout filter: a move with no volume behind
        # it does not get scored at all. Measured as the highest RVOL of the
        # last 5 sessions, so a breakout that fired days ago still counts.
        'prescreen': {'above_ema': 50, 'rsi_max': 95, 'min_rvol': 1.5},
        'weights': {
            'fundamental': 0.10, 'technical': 0.40, 'risk': 0.05,
            'momentum': 0.35, 'sentiment': 0.10,
        },
        'oscillator': 'momentum',
        'min_score': 62,
        'max_results': 40,
    },

    'gorengan': {
        'label': 'Gorengan',
        'desc': 'Spekulatif. Fundamental & risk dimatikan, momentum dominan.',
        'order': 4,
        'universe': {
            'min_turnover': 2e9,    # jauh lebih rendah; ini saham kecil
            'min_price': 50,        # di bawah gocap tidak bisa ditransaksikan normal
            'max_price': 500,
            'exclude_sectors': [],
            'exclude_tickers': [],
        },
        'prescreen': {'above_ema': 50, 'rsi_max': 95, 'min_rvol': 1.5},
        # Risk is Sharpe/Sortino/Altman -- all of which measure the very
        # volatility this profile is hunting, so it is switched off rather
        # than left to fight the momentum term.
        'weights': {
            'fundamental': 0.0, 'technical': 0.35, 'risk': 0.0,
            'momentum': 0.45, 'sentiment': 0.20,
        },
        'oscillator': 'momentum',
        'min_score': 60,
        'max_results': 40,
        'warn': 'Sinyal di sini adalah saham yang sedang dipompa. Indikator '
                'tidak bisa membedakan awal kenaikan dari puncak sebelum ARB.',
    },
}

WEIGHT_KEYS = ('fundamental', 'technical', 'risk', 'momentum', 'sentiment')


def _deep_merge(base, over):
    out = copy.deepcopy(base)
    for k, v in (over or {}).items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _deep_merge(out[k], v)
        else:
            out[k] = v
    return out


def validate(p, name='?'):
    """Raise on a profile that would silently produce nonsense."""
    w = p.get('weights') or {}
    missing = [k for k in WEIGHT_KEYS if k not in w]
    if missing:
        raise ValueError(f"profil '{name}': bobot hilang: {missing}")
    for k in WEIGHT_KEYS:
        if not isinstance(w[k], (int, float)) or w[k] < 0:
            raise ValueError(f"profil '{name}': bobot '{k}' harus angka >= 0")
    if sum(w[k] for k in WEIGHT_KEYS) <= 0:
        raise ValueError(f"profil '{name}': total bobot nol, skor tidak terdefinisi")
    if p.get('oscillator') not in ('mean_reversion', 'momentum'):
        raise ValueError(f"profil '{name}': oscillator harus mean_reversion atau momentum")
    u = p.get('universe') or {}
    lo, hi = u.get('min_price'), u.get('max_price')
    if lo is not None and hi is not None and lo > hi:
        raise ValueError(f"profil '{name}': min_price > max_price")
    if not (0 <= float(p.get('min_score', 60)) <= 100):
        raise ValueError(f"profil '{name}': min_score harus 0-100")
    mr = (p.get('prescreen') or {}).get('min_rvol')
    if mr is not None and (not isinstance(mr, (int, float)) or mr < 0):
        raise ValueError(f"profil '{name}': min_rvol harus angka >= 0 atau kosong")
    return p


def load():
    """Built-ins merged with profiles.json. Returns {name: profile}."""
    profiles = copy.deepcopy(BUILTIN)
    if OVERRIDES_PATH.exists():
        try:
            over = json.loads(OVERRIDES_PATH.read_text())
        except Exception as e:
            print(f"profiles.json unreadable, using built-ins: {e}")
            over = {}
        for name, patch in (over or {}).items():
            base = profiles.get(name, BUILTIN['default'])
            merged = _deep_merge(base, patch)
            try:
                profiles[name] = validate(merged, name)
            except ValueError as e:
                print(f"profiles.json ignored for '{name}': {e}")
    for name, p in profiles.items():
        validate(p, name)
    return dict(sorted(profiles.items(), key=lambda kv: kv[1].get('order', 99)))


def save_overrides(patch):
    """Persist user edits. Validated against the merged result first."""
    merged = copy.deepcopy(BUILTIN)
    for name, sub in (patch or {}).items():
        base = merged.get(name, BUILTIN['default'])
        validate(_deep_merge(base, sub), name)
    OVERRIDES_PATH.write_text(json.dumps(patch, indent=2))
    return load()


def enabled(profiles):
    return {k: v for k, v in profiles.items() if v.get('active', True)}
