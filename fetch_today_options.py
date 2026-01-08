import requests
import re

OPTIONS_API_URL = "https://mongo-api-fetch.vercel.app/api/options/today"

def extract_strike(trading_symbol: str) -> int:
    """
    Extract strike from trading_symbol like:
    'BANKNIFTY 58700 CE 27 JAN 26'
    """
    match = re.search(r"\b(\d{4,6})\b", trading_symbol)
    return int(match.group(1)) if match else None


def fetch_today_options():
    res = requests.get(OPTIONS_API_URL, timeout=15)
    res.raise_for_status()

    raw = res.json()["data"]
    options = []

    for index_name, expiry_map in raw.items():
        for expiry, info in expiry_map.items():
            for sym in info.get("symbols", []):

                trading_symbol = sym.get("trading_symbol", "")
                strike = extract_strike(trading_symbol)

                options.append({
                    "index": index_name,
                    "expiry": expiry,
                    "atm": info.get("atm"),
                    "spot": info.get("spot"),
                    "strike_step": info.get("strike_step"),

                    "instrument_key": sym.get("instrument_key"),
                    "exchange_token": sym.get("exchange_token"),
                    "option_type": sym.get("option_type"),
                    "strike": strike,
                    "symbol": sym.get("id"),          # using id as symbol
                    "trading_symbol": trading_symbol,
                    "day_high": sym.get("day_high"),
                    "day_low": sym.get("day_low"),
                    "market_open": sym.get("market_open"),
                })

    return options
