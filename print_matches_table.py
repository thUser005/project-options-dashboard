def print_matches_table(matches):
    if not matches:
        print("❌ No matching instruments found")
        return

    print("\nAvailable Matching Contracts:\n")
    print("Idx | Instrument Key     | Trading Symbol              | ATM   | Spot")
    print("-" * 80)

    for i, m in enumerate(matches):
        print(
            f"{i:<3} | {m['instrument_key']:<18} | "
            f"{m['trading_symbol']:<28} | "
            f"{m['atm']:<5} | {m['spot']}"
        )

def get_user_trade_inputs():
    breakout = float(input("Enter breakout price: "))
    target = float(input("Enter target price: "))
    stoploss = float(input("Enter stoploss price: "))

    return {
        "breakout": breakout,
        "target": target,
        "stoploss": stoploss
    }
