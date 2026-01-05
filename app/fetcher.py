import aiohttp
import asyncio
from datetime import datetime, timezone, timedelta

from app.config import URL, HEADERS
from app.store import LIVE_OPTION_DATA, SYMBOL_STRUCTURE

# ==================================================
# IST TIMEZONE
# ==================================================
IST = timezone(timedelta(hours=5, minutes=30))


# ==================================================
# HELPERS
# ==================================================
def chunk_list(items, size=100):
    """
    Yield fixed-size chunks from a list
    """
    for i in range(0, len(items), size):
        yield items[i:i + size]


# ==================================================
# NORMALIZE GROWW RESPONSE (AUTO TIMESTAMP FIX)
# ==================================================
def normalize(raw: dict) -> dict:
    """
    Convert Groww raw response into clean live format

    ✔ Auto-detect seconds / milliseconds timestamp
    ✔ Safe for missing fields
    ✔ Prevents 1970 timestamp bug permanently
    """
    out = {}

    for sym, info in raw.items():
        ts = info.get("tsInMillis")
        ts_sec = None

        if isinstance(ts, (int, float)):
            ts_sec = ts / 1000 if ts > 1_000_000_000_000 else ts

        out[sym] = {
            "ltp": info.get("ltp"),
            "oi": info.get("openInterest", 0),
            "volume": info.get("volume", 0),
            "timestamp": (
                datetime.fromtimestamp(ts_sec, IST).strftime("%Y-%m-%d %H:%M:%S")
                if ts_sec else None
            ),
            "last_update_epoch": ts_sec,
        }

    return out


# ==================================================
# LIVE PRICE FETCHER (EXPIRY-WISE BATCHING)
# ==================================================
async def live_fetcher():
    """
    🔁 Background task

    1️⃣ Wait for SYMBOL_STRUCTURE (MongoDB loaded at startup)
    2️⃣ Loop index → expiry → symbols
    3️⃣ Batch symbols safely (≤100 per request)
    4️⃣ Call Groww API
    5️⃣ Incrementally update LIVE_OPTION_DATA
    """

    # --------------------------------------------------
    # Wait until symbol structure is available
    # --------------------------------------------------
    while not SYMBOL_STRUCTURE:
        print("⏳ Waiting for symbol structure to load...")
        await asyncio.sleep(0.5)

    print("✅ Symbol structure ready. Starting Groww polling...")

    timeout = aiohttp.ClientTimeout(total=5)

    async with aiohttp.ClientSession(timeout=timeout) as session:
        while True:
            try:
                updated_count = 0

                # ==================================================
                # INDEX → EXPIRY → BATCH LOOP
                # ==================================================
                for index, expiries in SYMBOL_STRUCTURE.items():
                    for expiry, symbols in expiries.items():

                        if not symbols:
                            continue

                        # Split expiry symbols into safe batches
                        for batch in chunk_list(symbols, size=100):

                            async with session.post(
                                URL,
                                headers=HEADERS,
                                json=batch,
                            ) as resp:

                                if resp.status == 200:
                                    raw = await resp.json()
                                    LIVE_OPTION_DATA.update(normalize(raw))
                                    updated_count += len(batch)

                                else:
                                    print(
                                        f"⚠️ Groww HTTP {resp.status} | "
                                        f"{index} {expiry} | batch={len(batch)}"
                                    )

                            # Small delay between batches (VERY IMPORTANT)
                            await asyncio.sleep(0.05)

                print(f"🔄 Live prices updated for ~{updated_count} symbols")

            except asyncio.TimeoutError:
                print("⚠️ Groww request timed out")

            except Exception as e:
                print("❌ Fetcher error:", e)

            # Full polling interval
            await asyncio.sleep(1)
