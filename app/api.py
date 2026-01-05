import asyncio

from fastapi import FastAPI, WebSocket, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from starlette.websockets import WebSocketDisconnect

from app.store import LIVE_OPTION_DATA, SYMBOL_STRUCTURE
from app.symbol_loader import load_all_option_symbols
from app.utils import (
    build_structure_summary,
    build_live_structured,
    filter_live_by_index_expiry,
)

# ==================================================
# APP INITIALIZATION
# ==================================================
app = FastAPI(title="Live Option Feed")

# Serve static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Templates
templates = Jinja2Templates(directory="app/templates")

# ==================================================
# STARTUP EVENT → LOAD SYMBOL STRUCTURE
# ==================================================
@app.on_event("startup")
async def startup_event():
    """
    Load MongoDB symbol structure ONCE at startup
    """
    symbol_tree = load_all_option_symbols()

    SYMBOL_STRUCTURE.clear()
    SYMBOL_STRUCTURE.update(symbol_tree)

    print(f"✅ Symbol structure loaded | Indexes: {len(SYMBOL_STRUCTURE)}")


# ==================================================
# HOME
# ==================================================
@app.get("/")
def home():
    return {
        "status": "running",
        "message": "Live Option Feed server is running",
        "routes": {
            "ui": "/ui",
            "flat_live": "/live/options",
            "structure": "/live/structure",
            "structure_index": "/live/structure/{index}",
            "structure_expiry": "/live/structure/{index}/{expiry}",
            "structured_live": "/live/options/structured",
            "live_by_expiry": "/live/options/{index}/{expiry}",
            "ws_flat": "/ws/options",
            "ws_by_expiry": "/ws/options/{index}/{expiry}",
        },
    }


# ==================================================
# UI (HTML)
# ==================================================
@app.get("/ui", response_class=HTMLResponse)
def ui(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {"request": request},
    )


# ==================================================
# FLAT LIVE DATA
# ==================================================
@app.get("/live/options")
def get_live_options():
    """
    Flat symbol → live price mapping
    """
    return LIVE_OPTION_DATA


# ==================================================
# STRUCTURE SUMMARY
# ==================================================
@app.get("/live/structure")
def get_structure():
    """
    Index → expiry → option count
    """
    return build_structure_summary(SYMBOL_STRUCTURE)


@app.get("/live/structure/{index}")
def get_index_structure(index: str):
    """
    Expiries available for an index
    """
    index = index.upper()
    data = SYMBOL_STRUCTURE.get(index)

    if not data:
        return {"error": f"Index '{index}' not found"}

    return {
        expiry: {"option_count": len(symbols)}
        for expiry, symbols in data.items()
    }


@app.get("/live/structure/{index}/{expiry}")
def get_expiry_structure(index: str, expiry: str):
    """
    Option symbols under an index + expiry
    """
    index = index.upper()
    symbols = SYMBOL_STRUCTURE.get(index, {}).get(expiry)

    if not symbols:
        return {"error": "Index / Expiry not found"}

    return {
        "index": index,
        "expiry": expiry,
        "option_count": len(symbols),
        "symbols": symbols,
    }


# ==================================================
# STRUCTURED LIVE DATA (ALL INDEXES)
# ==================================================
@app.get("/live/options/structured")
def get_structured_live():
    """
    Index → expiry → symbol → live price data
    """
    return build_live_structured(SYMBOL_STRUCTURE, LIVE_OPTION_DATA)


# ==================================================
# LIVE DATA FOR INDEX + EXPIRY (REST)
# ==================================================
@app.get("/live/options/{index}/{expiry}")
def get_live_options_by_expiry(index: str, expiry: str):
    """
    Live prices for a specific index + expiry
    """
    data = filter_live_by_index_expiry(
        SYMBOL_STRUCTURE,
        LIVE_OPTION_DATA,
        index,
        expiry,
    )

    if not data:
        return {"error": "Index / Expiry not found or no live data"}

    return {
        "index": index.upper(),
        "expiry": expiry,
        "option_count": len(data),
        "data": data,
    }


# ==================================================
# WEBSOCKET – FLAT LIVE DATA
# ==================================================
@app.websocket("/ws/options")
async def ws_options(ws: WebSocket):
    await ws.accept()

    try:
        while True:
            await ws.send_json(LIVE_OPTION_DATA)
            await asyncio.sleep(1)

    except WebSocketDisconnect:
        # Normal client disconnect
        print("🔌 Flat WebSocket disconnected")


# ==================================================
# WEBSOCKET – INDEX + EXPIRY
# ==================================================
@app.websocket("/ws/options/{index}/{expiry}")
async def ws_options_by_expiry(ws: WebSocket, index: str, expiry: str):
    await ws.accept()

    index = index.upper()
    symbols = SYMBOL_STRUCTURE.get(index, {}).get(expiry)

    if not symbols:
        await ws.send_json({"error": "Index / Expiry not found"})
        await ws.close()
        return

    try:
        while True:
            payload = {
                sym: LIVE_OPTION_DATA[sym]
                for sym in symbols
                if sym in LIVE_OPTION_DATA
            }

            await ws.send_json({
                "index": index,
                "expiry": expiry,
                "option_count": len(payload),
                "data": payload,
            })

            await asyncio.sleep(1)

    except WebSocketDisconnect:
        # Normal client disconnect (dropdown change / refresh)
        print(f"🔌 WebSocket disconnected: {index} {expiry}")
