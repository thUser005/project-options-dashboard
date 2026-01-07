import threading
import time
import os
import socket
import sys
import subprocess
import shutil
import re
from functools import wraps

import upstox_client
from flask import Flask, render_template, request, redirect, url_for, jsonify
from dotenv import load_dotenv
from pymongo import MongoClient
from bson import ObjectId
from upstox_client.feeder.market_data_streamer_v3 import MarketDataStreamerV3

from fetch_today_options import fetch_today_options
from parse_alert_text import parse_alert_text
from match_options import match_options

# ✅ TELEGRAM NOTIFIER (SINGLE SOURCE OF TRUTH)
from telegram_notifier import (
    alert_created,
    alert_deleted,
    breakout_hit,
    target_hit,
    stoploss_hit
)

# ======================================================
# INIT
# ======================================================
load_dotenv()
app = Flask(__name__)

# ======================================================
# GLOBAL STATE
# ======================================================
LIVE_LTP = {}
ACTIVE_STREAMS = {}

ACCESS_TOKEN_CACHE = {"token": None, "ts": 0}

TOKEN_TTL = 60 * 20
TOKEN_VALIDITY = 60 * 60 * 24

# ======================================================
# MONGODB
# ======================================================
mongo = MongoClient(os.getenv("MONGO_URL"))
db = mongo["alerts_db"]

alerts_col = db["alerts"]
tokens_col = db["upstox_tokens"]

WEBSITE_URL = os.getenv("WEBSITE_URL")

# ======================================================
# RETRY DECORATOR (MAX 3)
# ======================================================
def retry_safe(max_retries=3, delay=1):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            for i in range(max_retries):
                try:
                    return fn(*args, **kwargs)
                except Exception as e:
                    print(f"⚠️ {fn.__name__} failed ({i+1}/{max_retries}): {e}")
                    if i == max_retries - 1:
                        return None
                    time.sleep(delay)
        return wrapper
    return decorator

# ======================================================
# COLAB DETECTION
# ======================================================
def running_in_colab():
    return "google.colab" in sys.modules

# ======================================================
# CLOUDFLARE INSTALL
# ======================================================
def install_cloudflared():
    if shutil.which("cloudflared"):
        return
    subprocess.run([
        "curl", "-fsSL",
        "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64",
        "-o", "cloudflared"
    ], check=True)
    subprocess.run(["chmod", "+x", "cloudflared"], check=True)

# ======================================================
# START CLOUDFLARE TUNNEL
# ======================================================
def start_cloudflare_tunnel(port):
    proc = subprocess.Popen(
        ["./cloudflared", "tunnel", "--url", f"http://127.0.0.1:{port}"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )

    public_url = None
    for line in iter(proc.stdout.readline, ""):
        if "trycloudflare.com" in line:
            match = re.search(r"https://[a-zA-Z0-9\-]+\.trycloudflare\.com", line)
            if match:
                public_url = match.group(0)
                print("🌍 Public URL:", public_url)
                break

    return proc, public_url

# ======================================================
# SEND URL TO TELEGRAM (ONCE)
# ======================================================
@retry_safe()
def send_public_url_to_telegram(url):
    from telegram import Bot
    bot = Bot(os.getenv("TELEGRAM_BOT_TOKEN"))
    bot.send_message(
        chat_id=os.getenv("TELEGRAM_CHAT_ID"),
        text=f"🌍 Public App URL:\n{url}"
    )

# ======================================================
# ACCESS TOKEN MANAGER (UNCHANGED LOGIC)
# ======================================================
@retry_safe()
def get_access_token():
    now = time.time()

    if ACCESS_TOKEN_CACHE["token"] and (now - ACCESS_TOKEN_CACHE["ts"] < TOKEN_TTL):
        return ACCESS_TOKEN_CACHE["token"]

    doc = tokens_col.find_one(sort=[("created_at", -1)])
    if doc and (now - doc["created_at"] < TOKEN_VALIDITY):
        ACCESS_TOKEN_CACHE["token"] = doc["access_token"]
        ACCESS_TOKEN_CACHE["ts"] = now
        return doc["access_token"]

    raise RuntimeError("No valid Upstox access token found")

# ======================================================
# LIVE STREAM
# ======================================================
@retry_safe()
def start_ltp_stream(instrument_key):
    if instrument_key in ACTIVE_STREAMS:
        return

    token = get_access_token()
    if not token:
        return

    config = upstox_client.Configuration()
    config.access_token = token
    api_client = upstox_client.ApiClient(config)

    streamer = MarketDataStreamerV3(api_client)
    ACTIVE_STREAMS[instrument_key] = streamer

    def on_open():
        streamer.subscribe([instrument_key], "ltpc")

    def on_message(msg):
        feeds = msg.get("feeds", {})
        ltpc = feeds.get(instrument_key, {}).get("ltpc")
        if ltpc:
            LIVE_LTP[instrument_key] = float(ltpc["ltp"])

    streamer.on("open", on_open)
    streamer.on("message", on_message)
    streamer.on("error", lambda e: print("❌ Stream error:", e))
    streamer.on("close", lambda c, m: print("🔌 Stream closed"))

    threading.Thread(target=streamer.connect, daemon=True).start()

# ======================================================
# ALERT MONITOR
# ======================================================
def alert_monitor():
    while True:
        try:
            alerts = list(alerts_col.find({"status": {"$in": ["ACTIVE", "BREAKOUT_HIT"]}}))
            for a in alerts:
                ltp = LIVE_LTP.get(a["instrument_key"])
                if not ltp:
                    continue

                if a["status"] == "ACTIVE" and ltp >= a["breakout"]:
                    breakout_hit(a, ltp)
                    alerts_col.update_one({"_id": a["_id"]}, {"$set": {"status": "BREAKOUT_HIT"}})

                elif ltp >= a["target"]:
                    target_hit(a, ltp)
                    alerts_col.update_one({"_id": a["_id"]}, {"$set": {"status": "TARGET_HIT"}})

                elif ltp <= a["stoploss"]:
                    stoploss_hit(a, ltp)
                    alerts_col.update_one({"_id": a["_id"]}, {"$set": {"status": "STOPLOSS_HIT"}})

        except Exception as e:
            print("⚠️ Alert monitor error:", e)

        time.sleep(1)

# ======================================================
# ROUTES (UNCHANGED)
# ======================================================
@app.route("/", methods=["GET", "POST"])
def index():
    matches = []
    saved_alerts = list(alerts_col.find().sort("created_at", -1))

    for a in saved_alerts:
        start_ltp_stream(a["instrument_key"])

    if request.method == "POST":
        alert_text = request.form["alert_text"]
        criteria = parse_alert_text(alert_text)

        options = retry_safe()(fetch_today_options)()
        matches = retry_safe()(match_options)(options, criteria) or []

        for m in matches:
            start_ltp_stream(m["instrument_key"])

    return render_template(
        "index.html",
        matches=matches,
        saved_alerts=saved_alerts,
        website_url=WEBSITE_URL
    )

@app.route("/ltp/<instrument_key>")
def get_ltp(instrument_key):
    return jsonify({"ltp": LIVE_LTP.get(instrument_key)})

@app.route("/create_alert", methods=["POST"])
def create_alert():
    data = {
        "instrument_key": request.form["instrument_key"],
        "trading_symbol": request.form.get("trading_symbol"),
        "breakout": float(request.form["breakout"]),
        "target": float(request.form["target"]),
        "stoploss": float(request.form["stoploss"]),
        "created_at": time.time(),
        "status": "ACTIVE"
    }

    alerts_col.insert_one(data)
    alert_created(data, LIVE_LTP.get(data["instrument_key"]))
    return redirect(url_for("index"))

@app.route("/delete_alert/<alert_id>", methods=["POST"])
def delete_alert(alert_id):
    alert = alerts_col.find_one({"_id": ObjectId(alert_id)})
    alerts_col.delete_one({"_id": ObjectId(alert_id)})

    if alert:
        alert_deleted(alert, LIVE_LTP.get(alert["instrument_key"]))

    return redirect(url_for("index"))

# ======================================================
# TOKEN ROUTES (UNCHANGED)
# ======================================================
@app.route("/token")
def token_page():
    return render_template("token.html", website_url=WEBSITE_URL, mobile_num=os.getenv("MOBILE_NUM"))

@app.route("/token/save", methods=["POST"])
def save_token():
    token = request.form["access_token"].strip()
    tokens_col.insert_one({"access_token": token, "created_at": time.time()})
    ACCESS_TOKEN_CACHE.update({"token": token, "ts": time.time()})
    return redirect(url_for("index"))

@app.route("/token/status")
def token_status():
    doc = tokens_col.find_one(sort=[("created_at", -1)])
    if not doc:
        return jsonify({"exists": False, "expired": True})
    return jsonify({
        "exists": True,
        "expired": (time.time() - doc["created_at"]) > TOKEN_VALIDITY,
        "created_at": doc["created_at"]
    })

# ======================================================
# PORT AUTO
# ======================================================
def get_free_port():
    s = socket.socket()
    s.bind(("", 0))
    port = s.getsockname()[1]
    s.close()
    return port

# ======================================================
# MAIN
# ======================================================
if __name__ == "__main__":
    threading.Thread(target=alert_monitor, daemon=True).start()

    PORT = get_free_port()
    print(f"🚀 Server running at http://127.0.0.1:{PORT}")

    threading.Thread(
        target=lambda: app.run(
            host="127.0.0.1",
            port=PORT,
            debug=True,
            use_reloader=False
        ),
        daemon=True
    ).start()

    if running_in_colab():
        install_cloudflared()
        _, public_url = start_cloudflare_tunnel(PORT)
        if public_url:
            send_public_url_to_telegram(public_url)

    while True:
        time.sleep(5)
