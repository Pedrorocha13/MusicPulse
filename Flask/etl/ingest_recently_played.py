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
        raise FileNotFoundError(
            "tokens.json não encontrado. Rode o fluxo OAuth primeiro no Flask."
        )
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


def get_recently_played(access_token: str, before: str | None = None) -> dict:
    url = "https://api.spotify.com/v1/me/player/recently-played"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    params: dict[str, int | str] = {"limit": 50}
    if before:
        params["before"] = before

    response = requests.get(url, headers=headers, params=params, timeout=30)
    return {
        "status_code": response.status_code,
        "data": response.json() if response.content else {}
    }


def normalize_recently_played(items: list[dict], batch_id: str) -> list[tuple]:
    rows = []

    for item in items:
        track = item.get("track", {})
        context = item.get("context") or {}

        played_at = item.get("played_at")
        track_id = track.get("id")

        if not played_at or not track_id:
            continue

        rows.append(
            (
                batch_id,
                played_at,
                track_id,
                context.get("type"),
                context.get("uri"),
                json.dumps(item, ensure_ascii=False),
            )
        )

    return rows


def upsert_staging(rows: list[tuple]) -> int:
    if not rows:
        return 0

    query = """
        INSERT INTO stg.spotify_recently_played (
            batch_id,
            played_at,
            track_id,
            context_type,
            context_uri,
            payload_json
        )
        VALUES (%s, %s, %s, %s, %s, %s::jsonb)
        ON CONFLICT (played_at, track_id)
        DO UPDATE SET
            context_type = EXCLUDED.context_type,
            context_uri = EXCLUDED.context_uri,
            payload_json = EXCLUDED.payload_json;
    """

    with psycopg.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            cur.executemany(query, rows)
        conn.commit()

    return len(rows)


def main() -> None:
    tokens = load_tokens()
    access_token = tokens.get("access_token")
    refresh_token = tokens.get("refresh_token")

    if not access_token:
        raise ValueError("access_token não encontrado no tokens.json")

    all_rows = []
    batch_id = str(uuid4())
    before = None

    while True:
        result = get_recently_played(access_token, before=before)

        if result["status_code"] == 401 and refresh_token:
            new_tokens = refresh_access_token(refresh_token)
            tokens["access_token"] = new_tokens["access_token"]
            tokens["expires_in"] = new_tokens.get("expires_in", tokens.get("expires_in"))
            save_tokens(tokens)
            access_token = tokens["access_token"]

            result = get_recently_played(access_token, before=before)

        if result["status_code"] != 200:
            raise RuntimeError(
                f"Erro ao buscar recently played: {result['status_code']} - {result['data']}"
            )

        data = result["data"]
        items = data.get("items", [])

        if not items:
            break

        rows = normalize_recently_played(items, batch_id)
        all_rows.extend(rows)

        cursors = data.get("cursors", {})
        before = cursors.get("before")

        if len(items) < 50 or not before:
            break

    inserted = upsert_staging(all_rows)
    print(f"Linhas processadas para staging: {inserted}")


if __name__ == "__main__":
    main()