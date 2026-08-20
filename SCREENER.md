# IDX Screener

Menyaring seluruh emiten likuid BEI setiap hari lewat **empat profil sekaligus**,
lalu mengirim sinyal BUY ke Telegram. Berjalan dari cron atau tombol di halaman
`/screener`, terpisah penuh dari web analyzer.

```
screener.py              pipeline utama
profiles.py              definisi 4 profil (bawaan)
profiles.json            override dari halaman setelan (gitignored)
services/notifier.py     pengirim Telegram
results/YYYY-MM-DD.json  hasil tiap run (gitignored)
results/status.json      progress run yang sedang berjalan
templates/screener.html
static/screener.{css,js}
```

`app.py` hanya membaca `results/` dan bisa **melempar** run ke subprocess.
Screening tidak pernah terjadi di dalam request — prosesnya belasan menit dan
menembak Yahoo ratusan kali, jauh melewati timeout gunicorn.

## Profil

Satu profil menjawab empat hal sekaligus dengan satu set angka yang konsisten:
siapa yang boleh ikut (`universe`), siapa yang layak diambil datanya
(`prescreen`), seberapa besar tiap pilar berpengaruh (`weights`), dan bagaimana
membaca osilator (`oscillator`).

| Profil | Bobot F/T/R/M/S | Osilator | Likuiditas | Harga | Gate |
|---|---|---|---|---|---|
| **Default** | 28/32/20/13/7 | mean reversion | ≥10 M | bebas | EMA50, RSI<78 |
| **Value** | 55/10/25/5/5 | mean reversion | ≥5 M | ≥100 | tanpa EMA, RSI<70 |
| **Breakout** | 10/40/5/35/10 | momentum | ≥10 M | bebas | EMA50, RSI<95, **RVOL≥1.5** |
| **Gorengan** | 0/35/0/45/20 | momentum | ≥2 M | 50–500 | EMA50, RSI<95, **RVOL≥1.5** |

### Gate volume: penyaring false breakout

Breakout tanpa volume adalah definisi false breakout, tapi volume nyaris tidak
punya pengaruh di skor: OBV cuma 4% dari skor akhir, MFI 2%, dan RVOL tercampur
dengan rekomendasi analis di dalam pilar Sentimen 10% — sehingga saham yang
menembus resistance dengan RVOL 0.5x bisa tertolong opini analis.

Terukur sebelum gate ini ada: **75% sinyal breakout tidak punya RVOL ≥ 2x**, dan
median RVOL kandidatnya cuma **0.94x** — separuh menembus dengan volume di bawah
rata-rata.

Karena itu volume jadi **syarat di prescreen**, bukan sekadar komponen skor:
yang tidak lolos tidak dinilai sama sekali. Dampaknya breakout 93→53 kandidat,
gorengan 104→56.

`min_rvol` diukur sebagai **RVOL tertinggi dalam 5 sesi terakhir**, bukan hari
ini saja — breakout yang meledak tiga hari lalu volumenya sudah normal hari ini,
jadi cek harian akan menolak persis setup yang mau dikonfirmasi. Pembandingnya
rata-rata 20 sesi yang **berakhir sebelum** jendela 5 hari itu, supaya hari
lonjakan tidak masuk ke rata-ratanya sendiri (kalau masuk, lonjakan 4x terukur
cuma 3.5x).

### Kenapa ada dua kurva osilator

Ini bagian yang paling mudah disalahpahami, dan bobot saja **tidak cukup**
untuk menyatakannya.

```
RSI    50    65    80    86    95
──────────────────────────────────
mean   62    72    49    34    22     ← puncak di 65, jatuh setelah 80
momentum 50  72    88    91    74     ← makin kuat makin baik, sampai blow-off
```

`osc_score` dipakai RSI, Stochastic, MFI, dan Williams %R — **40% dari pilar
Teknikal** — plus kurva terpisah untuk %B Bollinger. Tanpa kurva momentum,
profil breakout/gorengan akan menghukum persis saham yang dicarinya. Contoh
nyata: MDIA (RSI 86,8) dapat **49,3 HOLD** di model default dan **78,6 STRONG
BUY** di profil gorengan — data yang sama, cara baca yang berbeda.

### Catatan Value & bank

Piotroski tidak terdefinisi untuk bank/asuransi (tidak ada working capital,
gross margin, atau current ratio di neraca bank), jadi `calculate_piotroski`
mengembalikan `None` untuk mereka. Profil Value tetap mensyaratkan bukti
kualitas, tapi lewat `require: ['fundamental_quality']` yang memberi
pengecualian untuk sektor keuangan — kalau tidak, seluruh perbankan (±30%
kapitalisasi IDX) akan terkunci keluar dari screener value.

### Catatan Gorengan

Profil ini akan memunculkan saham yang sedang dipompa. Indikator teknikal tidak
bisa membedakan "awal kenaikan" dari "puncak sebelum ARB" — keduanya terlihat
identik. Risk (Sharpe/Sortino/Altman) sengaja dimatikan karena ketiganya
mengukur volatilitas, yaitu hal yang justru dicari profil ini.

## Cara kerja

Lima tahap. Semuanya dipakai bersama antar profil — yang mahal adalah
mengambil data, jadi satu emiten diambil **sekali** lalu diskor oleh setiap
profil yang meminta.

| Tahap | Isi | Request |
|---|---|---|
| 1. universe | `yf.screen` semua ekuitas Indonesia (~822) | ~4 |
| 2. eligible | filter harga/likuiditas/sektor per profil | 0 |
| 3. prescreen | bulk OHLCV sekali, gate per profil | ~1 per 100 |
| 4. analyse | ambil sekali, skor N kali | ~6 per emiten |
| 5. report | simpan JSON + Telegram | 1–3 |

Dedup di tahap 4 nyata: 238 emiten unik, bukan 437 kalau tiap profil jalan
sendiri — hemat 46%.

Tahap 3 **bukan** pengambil keputusan. Tugasnya cuma menahan jumlah emiten yang
masuk tahap 4 supaya tidak kena rate limit. Yang memutuskan tetap
`calculate_composite`, fungsi yang sama persis dipakai halaman analyzer.

## Setup

### 1. Bot Telegram

Chat ke [@BotFather](https://t.me/BotFather) → `/newbot` → salin token.

Untuk chat id: kirim satu pesan ke bot barumu, buka
`https://api.telegram.org/bot<TOKEN>/getUpdates`, ambil `message.chat.id`.
Untuk grup, masukkan bot ke grup dulu (id grup bernilai negatif).

### 2. Isi `.env`

```bash
TELEGRAM_BOT_TOKEN=123456:ABC-DEF...
TELEGRAM_CHAT_ID=987654321
SCREENER_SLEEP=0.7      # jeda antar request; naikkan kalau kena rate limit
```

`.env` sudah di-gitignore. Jangan pernah commit token.

### 3. Tes

```bash
python3 screener.py --limit 10 --dry-run          # 10 emiten, tanpa kirim
python3 screener.py --profile gorengan --limit 20 # satu profil saja
python3 -c "from services.notifier import test_connection; print(test_connection())"
python3 screener.py --limit 10                    # kirim beneran
```

### 4. Cron di VPS

Bursa tutup 15:00 WIB (Jumat 14:50), data Yahoo delay ~15 menit. Run penuh
empat profil butuh ~11 menit.

```cron
TZ=Asia/Jakarta
5 16 * * 1-5 cd /path/ke/idx-analyzer && /usr/bin/python3 screener.py >> /var/log/idx-screener.log 2>&1
```

Pakai path python di venv kalau ada. Screener tidak tahu kalender libur bursa —
di hari libur ia tetap jalan dan mengirim hasil berdasarkan penutupan terakhir.

## Setelan dari halaman

`/screener` → tombol **⚙ Setelan**. Tiap profil bisa diubah:

- likuiditas minimum, harga min/maks
- ambang skor, jumlah maksimal hasil
- gate EMA (50/200/mati) dan batas RSI
- bobot 5 pilar (0 = diabaikan, dinormalisasi otomatis)
- kurva osilator

Simpan menulis ke `profiles.json`, yang di-merge di atas bawaan di `profiles.py`.
Validasi jalan sebelum menulis, jadi setelan yang tidak masuk akal (total bobot
nol, min_score 150, harga min > maks) ditolak dengan pesan jelas, bukan diam-diam
menghasilkan skor ngawur. **Kembalikan bawaan** menghapus override profil itu.

Cron dan tombol manual membaca file yang sama, jadi tidak ada dua kebenaran.
Setelan yang dipakai ikut tercatat di tiap file hasil — kalau ambang berubah di
antara dua run, daftar "keluar dari daftar BUY" akan menandainya, supaya saham
yang jatuh karena **ambangnya digeser** tidak tertukar dengan yang jatuh karena
**melemah**.

## Trigger manual

Tombol **▶ Jalankan** melempar `screener.py` sebagai subprocess terpisah
(`start_new_session=True`, jadi selamat dari reload gunicorn) dan langsung
kembali. Progress dibaca dari `results/status.json` — file, bukan memori, karena
gunicorn jalan 2 worker dan run-nya ada di proses ketiga.

Dua pengaman: run baru ditolak kalau ada run yang masih jalan (409), dan ditolak
kalau run terakhir selesai kurang dari 5 menit lalu (429). Status `running` yang
lebih tua dari 45 menit dianggap sisa crash, bukan run hidup.

## Akses & password

Endpoint yang menyentuh data screener (`GET /api/screener`, `GET/POST
/api/screener/profiles`, `POST /api/screener/run`) dijaga `@admin_required`.
Lolos kalau salah satu terpenuhi:

1. **Request benar-benar dari server itu sendiri** — `remote_addr` loopback
   **dan** tidak ada header proxy. Ini yang dipakai cron, tanpa password.
2. **Header `X-Admin-Token` cocok** dengan `SCREENER_ADMIN_TOKEN` di `.env`.

Halaman `/screener` meminta password lewat `prompt()`, menyimpannya di
`sessionStorage` (mati saat tab ditutup), lalu mengirimkannya sebagai
`X-Admin-Token` di setiap request. Password salah → 403 → prompt lagi.

`GET /api/screener/status` sengaja dibiarkan terbuka; halaman perlu bisa
bertanya "apakah saya terkunci?" sebelum punya password. Isinya cuma
penghitung progress.

### Kenapa syaratnya loopback DAN tanpa header proxy

Kalau cuma cek loopback: dengan nginx/Cloudflare di depan, `remote_addr`
berubah jadi `127.0.0.1` untuk **semua** pengunjung termasuk dari internet —
cek itu justru meloloskan semua orang. Sebaliknya penyerang yang memalsukan
`X-Forwarded-For: 127.0.0.1` juga ditolak, karena keberadaan header itu
sendiri yang mendiskualifikasi. Terverifikasi:

| Skenario | Hasil |
|---|---|
| dari server sendiri, gunicorn langsung | ✅ lolos tanpa password |
| dari internet, gunicorn langsung | ❌ perlu password |
| lewat Cloudflare/nginx, tanpa password | ❌ 403 |
| lewat Cloudflare/nginx, password salah | ❌ 403 |
| lewat Cloudflare/nginx, password benar | ✅ 200 |
| memalsukan `X-Forwarded-For: 127.0.0.1` | ❌ 403 |

### Seberapa kuat ini sebenarnya

**Tidak kuat.** Ini guard tipis, bukan keamanan. Password dimasukkan lewat
`prompt()` browser lalu dikirim sebagai header — siapa pun yang membaca
`static/screener.js` tahu cara memanggil API-nya langsung dengan `curl`, dan
password-nya sendiri ada di `.env` server, bukan di-hash.

Cukup untuk: menghalau orang yang tidak sengaja menemukan URL-nya.
Tidak cukup untuk: data yang benar-benar rahasia, atau kalau ada yang punya
motif menembusnya.

Kalau nanti butuh yang sungguhan, jangan tambal ini — pasang **Cloudflare
Access** atau **basic auth di reverse proxy** di depan aplikasi. Keduanya
bekerja sebelum request menyentuh Flask, dan tidak bergantung pada JavaScript
yang bisa dibaca siapa saja.

### Kalau kamu sedang di mesin itu sendiri

Buka lewat `127.0.0.1`, bukan IP LAN. `192.168.x.x` dihitung sebagai mesin
lain, jadi tetap diminta password. Dari jauh:
`ssh -L 8080:127.0.0.1:8080 user@vps`, lalu buka `http://127.0.0.1:8080/screener`
— tidak perlu password sama sekali.

## Opsi CLI

```
--dry-run              cetak pesan, jangan kirim
--limit N              batasi universe tiap profil (tes)
--profile NAMA         jalankan profil ini saja (bisa diulang)
--force                abaikan kunci run-sedang-berjalan
```

## Catatan jujur

Bobot 28/32/20/13/7 dan ambang 60/70 adalah heuristik, **tidak divalidasi lewat
backtest**. Begitu juga kurva osilator dan angka profil lainnya. Screener ini
mempersempit daftar yang layak dilihat — bukan pengganti keputusan sendiri.

Mengubah bobot juga mengubah *arti* skornya: 65 dengan bobot lama tidak sebanding
dengan 65 dengan bobot baru. Itu sebabnya setelan ikut disimpan di tiap hasil.
