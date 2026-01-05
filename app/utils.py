# ==================================================
# STRUCTURE SUMMARY
# ==================================================
def build_structure_summary(symbol_structure: dict) -> dict:
    """
    Returns:
    {
      "NIFTY": {
         "2026-01-06": {
             "option_count": 76
         }
      }
    }
    """
    out = {}

    for index, expiries in symbol_structure.items():
        out[index] = {}

        for expiry, symbols in expiries.items():
            out[index][expiry] = {
                "option_count": len(symbols)
            }

    return out


# ==================================================
# FULL STRUCTURED LIVE DATA
# ==================================================
def build_live_structured(symbol_structure: dict, live_data: dict) -> dict:
    """
    Returns:
    {
      INDEX: {
        EXPIRY: {
          SYMBOL: { ltp, oi, volume, timestamp }
        }
      }
    }
    """
    out = {}

    for index, expiries in symbol_structure.items():
        out[index] = {}

        for expiry, symbols in expiries.items():
            expiry_data = {
                sym: live_data[sym]
                for sym in symbols
                if sym in live_data
            }

            # include expiry only if we have live data
            if expiry_data:
                out[index][expiry] = expiry_data

    return out


# ==================================================
# FILTER LIVE DATA BY INDEX + EXPIRY
# ==================================================
def filter_live_by_index_expiry(
    symbol_structure: dict,
    live_data: dict,
    index: str,
    expiry: str
) -> dict:
    """
    Returns live data ONLY for a specific index + expiry

    {
      SYMBOL: { ltp, oi, volume, timestamp }
    }
    """
    index = index.upper()

    symbols = symbol_structure.get(index, {}).get(expiry)
    if not symbols:
        return {}

    return {
        sym: live_data[sym]
        for sym in symbols
        if sym in live_data
    }


# ==================================================
# FILTER LIVE DATA BY INDEX (ALL EXPIRIES)
# ==================================================
def filter_live_by_index(
    symbol_structure: dict,
    live_data: dict,
    index: str
) -> dict:
    """
    Returns:
    {
      EXPIRY: {
        SYMBOL: { ltp, oi, volume, timestamp }
      }
    }
    """
    index = index.upper()
    expiries = symbol_structure.get(index)

    if not expiries:
        return {}

    out = {}

    for expiry, symbols in expiries.items():
        expiry_data = {
            sym: live_data[sym]
            for sym in symbols
            if sym in live_data
        }

        if expiry_data:
            out[expiry] = expiry_data

    return out
