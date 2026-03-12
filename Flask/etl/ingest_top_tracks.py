import json
import os
from pathlib import Path
from uuid import uuid4

import requests
import psycopg
from dotenv import load_dotenv

load_dotenv()

def require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise ValueError(f"Variável de ambiente obrigatória não encontrada: {name}")
    return value

DATABASE_URL = require_env("DATABASE_URL")
SPOTIFY_CLIENT_ID = require_env("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = require_env("SPOTIFY_CLIENT_SECRET")

TOKENS_FILE = Path("tokens.json")

def load_tokens() -> dict:
    if not TOKENS_FILE.exists():
        raise FileNotFoundError("tokens.json não encontrado.")
    with TOKENS_FILE.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_tokens(tokens: dict) -> None:
    with TOKENS_FILE.open("w", encoding="utf-8") as f:
        json.dump(tokens, f, ensure_ascii=False, indent=2)

def refresh_access_token(refresh_token: str) -> dict:
    url = "https://accounts.spotify.com/api/token"
    data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
    }

    response = requests.post(
        url,
        data=data,
        auth=(SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET),
        timeout=30,
    )
    response.raise_for_status()
    return response.json()

def get_top_tracks(access_token: str, time_range: str) -> dict:
    url = "https://api.spotify.com/v1/me/top/tracks"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    params = {
        "time_range": time_range,
        "limit": 50
    }

    response = requests.get(
        url,
        headers=headers,
        params=params,
        timeout=30,
    )

    return {
        "status_code": response.status_code,
        "data": response.json() if response.content else {}
    }

def normalize_top_tracks(items: list[dict], batch_id: str, time_range: str) -> list[tuple]:
    rows = []

    for idx, item in enumerate(items, start=1):
        track_id = item.get("id")
        if not track_id:
            continue

        rows.append(
            (
                batch_id,
                time_range,
                idx,
                track_id,
                json.dumps(item, ensure_ascii=False),
            )
        )

    return rows