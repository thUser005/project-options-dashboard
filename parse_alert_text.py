from datetime import datetime, date
from fetch_today_options import fetch_today_options


def _get_nearest_expiry(index_name: str) -> str:
    """
    Pick nearest expiry >= today for given index
    """
    options = fetch_today_options()
    today = date.today()

    expiries = set()

    for opt in options:
        if index_name in opt["index"]:
            exp_date = datetime.strptime(opt["expiry"], "%Y-%m-%d").date()
            if exp_date >= today:
                expiries.add(exp_date)

    if not expiries:
        raise ValueError(f"No valid expiry found for {index_name}")

    nearest = min(expiries)
    return nearest.strftime("%Y-%m-%d")


def parse_alert_text(text: str):
    """
    Supported formats:
    1) SENSEX 08 JAN 85200 PE
    2) NIFTY 26400 PE   -> auto nearest expiry
    """

    parts = text.strip().upper().split()

    # ===============================
    # FULL FORMAT WITH EXPIRY
    # ===============================
    if len(parts) == 5:
        index = parts[0]
        day = int(parts[1])
        month = parts[2]
        strike = int(parts[3])
        option_type = parts[4]

        year = datetime.now().year
        expiry = datetime.strptime(
            f"{day} {month} {year}",
            "%d %b %Y"
        ).strftime("%Y-%m-%d")

    # ===============================
    # SHORT FORMAT → AUTO EXPIRY
    # ===============================
    elif len(parts) == 3:
        index = parts[0]
        strike = int(parts[1])
        option_type = parts[2]

        expiry = _get_nearest_expiry(index)

    else:
        raise ValueError(
            "Invalid alert format.\n"
            "Use:\n"
            "  SENSEX 08 JAN 85200 PE\n"
            "  NIFTY 26400 PE"
        )

    return {
        "index": index,
        "expiry": expiry,
        "strike": strike,
        "option_type": option_type
    }
