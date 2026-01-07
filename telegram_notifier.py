import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

# ===============================
# UTILITIES
# ===============================
def _fmt_time(ts=None):
    """
    Format timestamp to readable IST/local time
    """
    ts = ts or time.time()
    return time.strftime("%d-%b-%Y %H:%M:%S", time.localtime(ts))


def _safe(val, default="NA"):
    return val if val not in (None, "", []) else default


def _option_block(alert):
    """
    Optional option context block (SAFE)
    """
    lines = []

    if alert.get("alert_text"):
        lines.append(f"📈 <b>Option:</b> {_safe(alert.get('alert_text'))}")

    if alert.get("trading_symbol"):
        lines.append(f"🧾 <b>Trading Symbol:</b> {_safe(alert.get('trading_symbol'))}")

    if lines:
        return "\n".join(lines) + "\n\n"

    return ""


# ===============================
# CORE SENDERS (UNCHANGED)
# ===============================
def send_text(message: str):
    if not BOT_TOKEN or not CHAT_ID:
        return

    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    requests.post(
        f"{BASE_URL}/sendMessage",
        data=payload,
        timeout=10
    )


def send_image(image_url: str, caption: str = ""):
    if not BOT_TOKEN or not CHAT_ID:
        return

    payload = {
        "chat_id": CHAT_ID,
        "photo": image_url,
        "caption": caption,
        "parse_mode": "HTML"
    }
    requests.post(
        f"{BASE_URL}/sendPhoto",
        data=payload,
        timeout=10
    )


def send_file(file_path: str, caption: str = ""):
    if not BOT_TOKEN or not CHAT_ID:
        return

    with open(file_path, "rb") as f:
        files = {"document": f}
        data = {
            "chat_id": CHAT_ID,
            "caption": caption,
            "parse_mode": "HTML"
        }
        requests.post(
            f"{BASE_URL}/sendDocument",
            files=files,
            data=data,
            timeout=20
        )

# ===============================
# FORMATTED ALERT MESSAGES (ENHANCED, SAFE)
# ===============================
def alert_created(alert, ltp=None):
    send_text(
        f"🟢 <b>ALERT CREATED</b>\n\n"
        f"{_option_block(alert)}"
        f"<b>Instrument:</b> {_safe(alert.get('instrument_key'))}\n"
        f"<b>LTP:</b> {_safe(ltp)}\n\n"
        f"<b>Breakout:</b> {alert.get('breakout')}\n"
        f"<b>Target:</b> {alert.get('target')}\n"
        f"<b>Stoploss:</b> {alert.get('stoploss')}\n\n"
        f"<b>Created At:</b> {_fmt_time(alert.get('created_at'))}"
    )


def alert_deleted(alert, ltp=None):
    send_text(
        f"🗑️ <b>ALERT DELETED</b>\n\n"
        f"{_option_block(alert)}"
        f"<b>Instrument:</b> {_safe(alert.get('instrument_key'))}\n"
        f"<b>LTP:</b> {_safe(ltp)}\n\n"
        f"<b>Created At:</b> {_fmt_time(alert.get('created_at'))}\n"
        f"<b>Deleted At:</b> {_fmt_time()}"
    )


def breakout_hit(alert, ltp):
    send_text(
        f"🚀 <b>BREAKOUT HIT</b>\n\n"
        f"{_option_block(alert)}"
        f"<b>Instrument:</b> {_safe(alert.get('instrument_key'))}\n"
        f"<b>LTP:</b> {_safe(ltp)}\n"
        f"<b>Breakout:</b> {alert.get('breakout')}\n\n"
        f"<b>Time:</b> {_fmt_time()}"
    )


def target_hit(alert, ltp):
    send_text(
        f"🎯 <b>TARGET HIT</b>\n\n"
        f"{_option_block(alert)}"
        f"<b>Instrument:</b> {_safe(alert.get('instrument_key'))}\n"
        f"<b>LTP:</b> {_safe(ltp)}\n"
        f"<b>Target:</b> {alert.get('target')}\n\n"
        f"<b>Time:</b> {_fmt_time()}"
    )


def stoploss_hit(alert, ltp):
    send_text(
        f"🛑 <b>STOPLOSS HIT</b>\n\n"
        f"{_option_block(alert)}"
        f"<b>Instrument:</b> {_safe(alert.get('instrument_key'))}\n"
        f"<b>LTP:</b> {_safe(ltp)}\n"
        f"<b>Stoploss:</b> {alert.get('stoploss')}\n\n"
        f"<b>Time:</b> {_fmt_time()}"
    )
