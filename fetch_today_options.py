import requests

OPTIONS_API_URL = "https://mongo-api-fetch.vercel.app/api/options/today"

def fetch_today_options():
    res = requests.get(OPTIONS_API_URL, timeout=15)
    res.raise_for_status()

    raw = res.json()["data"]
    options = []

    for index_name, expiry_map in raw.items():
        for expiry, info in expiry_map.items():
            for sym in info.get("symbols", []):
                options.append({
                    "index": index_name,
                    "expiry": expiry,
                    "atm": info.get("atm"),
                    "spot": info.get("spot"),
                    "strike_step": info.get("strike_step"),
                    "instrument_key": sym["instrument_key"],
                    "option_type": sym["option_type"],
                    "strike": int(sym["symbol"][-7:-2]),  # extract strike
                    "symbol": sym["symbol"],
                    "trading_symbol": sym["trading_symbol"]
                })

    return options
