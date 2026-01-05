📡 Live Option Feed API

## A real-time options market data backend built using FastAPI, MongoDB, aiohttp, and WebSockets.

## This service:

## Loads option symbols dynamically from MongoDB

## Fetches live prices from Groww API every second

## Serves data via REST APIs and WebSockets

## Supports Index → Expiry → Options structure

## Is optimized for trading dashboards, algos, and UIs

## 🚀 What This Project Does (High Level)

## At startup

## Reads option symbol structure from MongoDB

## Organizes data as
INDEX → EXPIRY → OPTION SYMBOLS

## In background

## Polls Groww live price API every second

## Stores latest prices in memory

## For users

## REST APIs to explore structure & fetch prices

## WebSockets for real-time streaming

## Filter data by index & expiry

## 📁 Project Folder Structure
option_live_feed/
│
├── main.py
├── requirements.txt
│
└── app/
    ├── api.py
    ├── fetcher.py
    ├── store.py
    ├── utils.py
    ├── symbol_loader.py
    ├── config.py
    ├── .env
    └── __init__.py

## 📄 File-by-File Explanation (Simple)
🔹 main.py

## Entry point of the application

## Starts FastAPI server (Uvicorn)

## Starts background task live_fetcher()

## Works on Windows & Colab

## 🔹 app/api.py

## All REST APIs & WebSocket routes

## Responsibilities:

## Load symbol structure at startup

## Define all API routes

## Handle WebSocket connections

## Filter live data per request

## This is the public interface of your backend.

## 🔹 app/fetcher.py

## Live price fetcher (background task)

## Runs continuously (every 1 second)

## Calls Groww live price API

## Updates in-memory live data store

## No database access (fast & safe)

## 🔹 app/store.py

## In-memory shared storage

## LIVE_OPTION_DATA   # latest live prices
SYMBOL_STRUCTURE   # index → expiry → symbols

## 
Acts like a live cache shared across the app.

## 🔹 app/symbol_loader.py

## MongoDB reader

## Connects to MongoDB

## Loads symbol structure once at startup

## Converts DB document into Python dict

## Flattens symbols when needed

## MongoDB is the single source of truth for symbols.

## 🔹 app/utils.py

## Helper & transformation functions

## Used to:

## Build structure summaries

## Group live prices by index & expiry

## Filter live data for specific requests

## No API logic here — only pure data functions.

## 🔹 app/config.py

## Configuration constants

## Groww API URL

## Request headers

## Common settings

## 🔹 .env

## Secrets & environment variables

## Example:

## MONGO_URL=mongodb://localhost:27017

## 
Never commit real secrets.

## 🌐 API ROUTES (REST)

## Base URL:

## http://127.0.0.1:8000

## 🏠 /

## Health & discovery

## GET /

## 
Returns available routes and server status.

## Use this to verify the server is running.

## 📊 /live/options

## Flat live prices (all symbols)

## GET /live/options

## 
Returns:

## {
  "NIFTY26JAN24350CE": {
    "ltp": 132.45,
    "oi": 245000,
    "volume": 15420,
    "timestamp": "2026-01-04 15:10:01"
  }
}

## 
Best for:

## Trading bots

## Raw price consumers

## 🧱 /live/structure

## Index → Expiry → Option count

## GET /live/structure

## 
Returns:

## {
  "NIFTY": {
    "2026-01-06": { "option_count": 76 }
  }
}

## 
Best for:

## UI dropdowns

## Navigation menus

## 📅 /live/structure/{index}

## Expiries available for one index

## GET /live/structure/NIFTY

## 
Returns all expiries under that index.

## 📜 /live/structure/{index}/{expiry}

## Symbols under an index & expiry

## GET /live/structure/NIFTY/2026-01-06

## 
Returns list of option symbols.

## 🧠 /live/options/structured

## All live prices grouped by index & expiry

## GET /live/options/structured

## 
Returns:

## INDEX → EXPIRY → SYMBOL → LIVE DATA

## 
Best for:

## Dashboards

## Tables

## Charts

## 🎯 /live/options/{index}/{expiry}

## Live prices for one index & expiry

## GET /live/options/NIFTY/2026-01-06

## 
Returns only relevant options.

## Best for:

## Focused trading screens

## Strategy execution

## ⚡ WebSocket ROUTES (Live Streaming)
🔁 /ws/options

## Flat live stream (all symbols)

## ws://127.0.0.1:8000/ws/options

## 
Streams full live data every second.

## 🎯 /ws/options/{index}/{expiry}

## Filtered live stream

## ws://127.0.0.1:8000/ws/options/NIFTY/2026-01-06

## 
Streams only options under that index & expiry.

## Best for:

## Live option chain UI

## Strategy monitoring

## 🧠 Architecture Flow (Mental Model)
MongoDB
   ↓ (startup)
SYMBOL_STRUCTURE
   ↓
Fetcher (Groww API)
   ↓
LIVE_OPTION_DATA
   ↓
FastAPI REST & WebSocket

## ✅ Why This Design Is Good

## ⚡ Very fast (in-memory reads)

## 🔒 MongoDB accessed only once

## 🧠 No duplicate API calls

## 📡 Scales to many clients

## 🧩 Easy to extend

## 🔮 Possible Future Enhancements

## /ws/options/{index} (all expiries)

## Auto-refresh ATM symbols

## Save ticks to MongoDB

## Build 1-min / 5-min candles

## Redis for multi-worker scaling

## Auth & rate limiting

## React / TradingView frontend