"""
API для доступу до найновіших даних Trending
"""

import asyncio
import json
import os
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional

from fastapi import Body, FastAPI, HTTPException, Query

from parser import GameBoostParser

DATA_FILE = "latest.json"
CACHE_TTL_SECONDS = 15 * 60
STORAGE_DIR = "storage_dumps"
UPLOAD_TOKEN = os.getenv("STORAGE_UPLOAD_TOKEN")

app = FastAPI(title="GameBoost Trending API", version="1.0.0")

_state: Dict[str, Any] = {
    "items": {},
    "updated_at": {},
    "debug": {},
}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_from_disk() -> None:
    if not os.path.exists(DATA_FILE):
        return
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            payload = json.load(f)
        items = payload.get("items", {})
        updated_at = payload.get("updated_at", {})
        debug = payload.get("debug", {})

        if isinstance(items, list):
            items = {"USD": items}
        if isinstance(updated_at, str):
            updated_at = {"USD": updated_at}

        _state["items"] = items if isinstance(items, dict) else {}
        _state["updated_at"] = updated_at if isinstance(updated_at, dict) else {}
        _state["debug"] = debug if isinstance(debug, dict) else {}
    except Exception:
        pass


def _save_to_disk() -> None:
    payload = {
        "updated_at": _state.get("updated_at"),
        "items": _state.get("items", {}),
        "debug": _state.get("debug", {}),
    }
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


def _is_stale(currency: str) -> bool:
    updated_at = _state.get("updated_at", {}).get(currency)
    if not updated_at:
        return True
    try:
        updated_dt = datetime.fromisoformat(updated_at)
        return datetime.now(timezone.utc) - updated_dt > timedelta(seconds=CACHE_TTL_SECONDS)
    except Exception:
        return True


async def _refresh_data(
    method: str = "auto",
    currency: str = "USD",
    storage_file: Optional[str] = None,
) -> List[Dict[str, Any]]:
    parser = GameBoostParser()
    cookies = None
    if storage_file:
        storage_path = Path(storage_file)
        if not storage_path.is_absolute():
            if not str(storage_path).startswith(STORAGE_DIR):
                storage_path = Path(STORAGE_DIR) / storage_path
        if not storage_path.exists():
            raise HTTPException(status_code=400, detail=f"storage_file not found: {storage_path}")
        cookies = parser.load_cookies_from_dump(str(storage_path))
    items = await parser.parse(method=method, currency=currency, cookies=cookies)
    _state["items"][currency] = items
    _state["updated_at"][currency] = _now_iso()
    _state["debug"][currency] = parser.last_debug
    _save_to_disk()
    return items


@app.on_event("startup")
async def on_startup() -> None:
    _load_from_disk()


@app.get("/trending")
async def get_trending(
    refresh: bool = Query(False, description="Оновити дані перед відповіддю"),
    method: str = Query("auto", description="playwright | cloudscraper | selenium | auto"),
    currency: str = Query("USD", description="USD | EUR | UAH"),
    storage_file: Optional[str] = Query(None, description="Шлях до storage_dumps/state_*.json"),
    debug: bool = Query(False, description="Додати debug-інформацію"),
) -> Dict[str, Any]:
    currency = currency.upper()
    if refresh or _is_stale(currency) or not _state.get("items", {}).get(currency):
        await _refresh_data(method=method, currency=currency, storage_file=storage_file)

    response = {
        "currency": currency,
        "updated_at": _state.get("updated_at", {}).get(currency),
        "count": len(_state.get("items", {}).get(currency, [])),
        "items": _state.get("items", {}).get(currency, []),
    }
    if debug:
        response["debug"] = _state.get("debug", {}).get(currency, {})
    return response


@app.post("/refresh")
async def refresh(
    method: str = Query("auto", description="playwright | cloudscraper | selenium | auto"),
    currency: str = Query("USD", description="USD | EUR | UAH"),
    storage_file: Optional[str] = Query(None, description="Шлях до storage_dumps/state_*.json"),
) -> Dict[str, Any]:
    currency = currency.upper()
    items = await _refresh_data(method=method, currency=currency, storage_file=storage_file)
    if not items:
        raise HTTPException(status_code=502, detail="Не вдалося оновити дані")
    return {
        "currency": currency,
        "updated_at": _state.get("updated_at", {}).get(currency),
        "count": len(items),
        "items": items,
    }


@app.post("/storage")
async def upload_storage(
    name: str = Query(..., description="Назва файла, напр. state_usd.json"),
    token: Optional[str] = Query(None, description="Опціональний токен"),
    payload: Dict[str, Any] = Body(...),
) -> Dict[str, Any]:
    if UPLOAD_TOKEN and token != UPLOAD_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid token")

    if "/" in name or "\\" in name:
        raise HTTPException(status_code=400, detail="Invalid file name")

    os.makedirs(STORAGE_DIR, exist_ok=True)
    path = os.path.join(STORAGE_DIR, name)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    return {"saved": True, "path": path}
