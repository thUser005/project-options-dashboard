from datetime import datetime, date
from fetch_today_options import fetch_today_options


def _get_nearest_expiry(index_name: str) -> str:
    """
    Pick nearest expiry >= today for given index
    """
    options = fetch_today_options()
    today = date.today()

    index_name = index_name.upper()
    expiries = set()

    for opt in options:
        # safer index comparison
        if opt.get("index", "").upper() == index_name:
            try:
                exp_date = datetime.strptime(
                    opt["expiry"], "%Y-%m-%d"
                ).date()
            except Exception:
                continue

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

    if not text or not isinstance(text, str):
        raise ValueError("Alert text must be a valid string")

    parts = text.strip().upper().split()

    # ===============================
    # FULL FORMAT WITH EXPIRY
    # ===============================
    if len(parts) == 5:
        index = parts[0]

        try:
            day = int(parts[1])
            month = parts[2]
            strike = int(parts[3])
            option_type = parts[4]
        except Exception:
            raise ValueError("Invalid alert values")

        if option_type not in ("CE", "PE"):
            raise ValueError("Option type must be CE or PE")

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

        try:
            strike = int(parts[1])
        except ValueError:
            raise ValueError("Strike must be a number")

        option_type = parts[2]
        if option_type not in ("CE", "PE"):
            raise ValueError("Option type must be CE or PE")

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
