import json
import os
from uuid import uuid4

import requests
import psycopg
from dotenv import load_dotenv

from spotify_auth import (
    load_tokens,
    save_tokens,
    refresh_access_token,
    require_env,
)

load_dotenv()

DATABASE_URL = require_env("DATABASE_URL")

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


TIME_RANGES = ("short_term", "medium_term", "long_term")


def upsert_staging_top_tracks(rows: list[tuple]) -> int:
    if not rows:
        return 0

    query = """
        INSERT INTO stg.spotify_top_tracks (
            batch_id,
            time_range,
            rank,
            track_id,
            payload_json
        )
        VALUES (%s, %s, %s, %s, %s::jsonb);
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

    all_rows: list[tuple] = []
    batch_id = str(uuid4())

    for time_range in TIME_RANGES:
        result = get_top_tracks(access_token, time_range)

        if result["status_code"] == 401 and refresh_token:
            new_tokens = refresh_access_token(refresh_token)
            tokens["access_token"] = new_tokens["access_token"]
            tokens["expires_in"] = new_tokens.get("expires_in", tokens.get("expires_in"))
            if "refresh_token" in new_tokens:
                tokens["refresh_token"] = new_tokens["refresh_token"]
            save_tokens(tokens)
            access_token = tokens["access_token"]

            result = get_top_tracks(access_token, time_range)

        if result["status_code"] != 200:
            raise RuntimeError(
                f"Erro ao buscar top tracks ({time_range}): "
                f"{result['status_code']} - {result['data']}"
            )

        items = result["data"].get("items", [])
        rows = normalize_top_tracks(items, batch_id, time_range)
        all_rows.extend(rows)
        print(f"  {time_range}: {len(rows)} faixas")

    inserted = upsert_staging_top_tracks(all_rows)
    print(f"Linhas inseridas no staging: {inserted}")


if __name__ == "__main__":
    main()