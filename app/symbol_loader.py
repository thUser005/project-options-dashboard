from pymongo import MongoClient
from dotenv import load_dotenv
import os

load_dotenv()

MONGO_URI = os.getenv("MONGO_URL")
DB_NAME = "options_data"
COL_NAME = "symbols_structural"

client = MongoClient(MONGO_URI)
col = client[DB_NAME][COL_NAME]


def load_all_option_symbols(trade_date: str | None = None) -> dict:
    """
    Returns:
    {
        "NIFTY": {
            "2026-01-06": [symbols...],
            "2026-01-13": [symbols...]
        },
        "BANKNIFTY": {...}
    }
    """

    query = {}
    if trade_date:
        query["trade_date"] = trade_date

    doc = col.find_one(query)
    if not doc:
        return {}

    result = {}

    for index, dates in doc["data"].items():
        result[index] = {}

        for expiry, payload in dates.items():
            result[index][expiry] = payload.get("symbols", [])

    return result


def flatten_symbols(symbol_tree: dict) -> list[str]:
    """Flattens nested dict into unique symbol list"""
    out = set()

    for index in symbol_tree.values():
        for symbols in index.values():
            out.update(symbols)

    return list(out)
