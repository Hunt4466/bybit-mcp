import os
from datetime import datetime, timezone

import httpx
from fastmcp import FastMCP

mcp = FastMCP("Bybit Read-Only Market Data")
BASE_URL = "https://api.bybit.com"


async def fetch_market(path: str, params: dict) -> dict:
    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.get(BASE_URL + path, params=params)
        response.raise_for_status()
        data = response.json()

    if data.get("retCode") != 0:
        raise ValueError(f"Bybit error: {data.get('retMsg')}")

    return {
        "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
        "data": data,
    }


@mcp.tool()
async def get_ticker(symbol: str = "BTCUSDT") -> dict:
    """Fetch fresh Bybit USDT perpetual last price, mark price and ticker."""
    return await fetch_market(
        "/v5/market/tickers",
        {"category": "linear", "symbol": symbol.upper().strip()},
    )


@mcp.tool()
async def get_candles(
    symbol: str = "BTCUSDT",
    interval: str = "15",
    limit: int = 300,
) -> dict:
    """Fetch candles, newest first. The newest candle may be incomplete.
    Intervals: 15 = 15 minutes, 60 = 1 hour, 240 = 4 hours, D = daily.
    Rows: start time ms, open, high, low, close, volume, turnover.
    """
    allowed = {
        "1", "3", "5", "15", "30", "60",
        "120", "240", "360", "720", "D", "W", "M",
    }
    if interval not in allowed:
        raise ValueError("Unsupported candle interval")

    return await fetch_market(
        "/v5/market/kline",
        {
            "category": "linear",
            "symbol": symbol.upper().strip(),
            "interval": interval,
            "limit": max(1, min(limit, 1000)),
        },
    )


if __name__ == "__main__":
    mcp.run(
        transport="http",
        host="0.0.0.0",
        port=int(os.environ.get("PORT", "8000")),
        path="/mcp",
    )
