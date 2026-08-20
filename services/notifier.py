"""Telegram delivery for screener runs.

Kept deliberately dumb: format a message, POST it, report what happened.
No queueing, no retry storm -- a missed daily run is not worth the machinery.
"""
import html
import os
import time

import requests

API = "https://api.telegram.org/bot{token}/sendMessage"
LIMIT = 4096          # Telegram's hard cap per message
CHUNK = 3800          # leave room for the header we prepend to each part


class NotifierNotConfigured(RuntimeError):
    pass


def _config():
    token = os.environ.get('TELEGRAM_BOT_TOKEN', '').strip()
    chat_id = os.environ.get('TELEGRAM_CHAT_ID', '').strip()
    if not token or not chat_id:
        raise NotifierNotConfigured(
            "Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in .env"
        )
    return token, chat_id


def _split(text):
    """Split on blank lines so a stock's block is never cut in half."""
    blocks, out, buf = text.split('\n\n'), [], ''
    for b in blocks:
        candidate = f"{buf}\n\n{b}" if buf else b
        if len(candidate) > CHUNK and buf:
            out.append(buf)
            buf = b
        else:
            buf = candidate
    if buf:
        out.append(buf)
    return out or ['']


def send(text, disable_preview=True):
    """Send `text` (Telegram HTML). Returns the number of messages delivered."""
    token, chat_id = _config()
    url = API.format(token=token)
    parts = _split(text)
    sent = 0
    for i, part in enumerate(parts):
        if len(parts) > 1:
            part = f"<i>({i + 1}/{len(parts)})</i>\n{part}"
        r = requests.post(url, timeout=30, json={
            'chat_id': chat_id,
            'text': part[:LIMIT],
            'parse_mode': 'HTML',
            'disable_web_page_preview': disable_preview,
        })
        if not r.ok:
            raise RuntimeError(f"Telegram {r.status_code}: {r.text[:300]}")
        sent += 1
        if i + 1 < len(parts):
            time.sleep(1)   # stay under Telegram's ~20 msg/min per chat
    return sent


def esc(s):
    return html.escape(str(s), quote=False)


def rp(v):
    """Rupiah, Indonesian thousands separator."""
    if v is None:
        return '—'
    return 'Rp ' + f"{float(v):,.0f}".replace(',', '.')


def test_connection():
    """Verify the bot token and chat id actually work."""
    token, chat_id = _config()
    r = requests.get(
        f"https://api.telegram.org/bot{token}/getChat",
        params={'chat_id': chat_id}, timeout=20,
    )
    return r.ok, r.json()
