import json
import os

import psycopg
from dotenv import load_dotenv

load_dotenv()

def require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise ValueError(f"Variável de ambiente obrigatória não encontrada: {name}")
    return value

DATABASE_URL = require_env("DATABASE_URL")


def load_rows_from_staging() -> list[dict]:
    query = """
        SELECT payload_json
        FROM stg.spotify_recently_played;
    """

    with psycopg.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            cur.execute(query)
            results = cur.fetchall()

    return [row[0] for row in results]


def upsert_album(cur, album: dict) -> None:
    if not album or not album.get("id"):
        return

    release_date = album.get("release_date")
    precision = album.get("release_date_precision")

    if release_date and precision != "day":
        release_date = None

    cur.execute(
        """
        INSERT INTO dwh.dim_album (
            album_id,
            album_name,
            release_date,
            release_date_precision
        )
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (album_id)
        DO UPDATE SET
            album_name = EXCLUDED.album_name,
            release_date = EXCLUDED.release_date,
            release_date_precision = EXCLUDED.release_date_precision,
            last_seen_at = now();
        """,
        (
            album.get("id"),
            album.get("name"),
            release_date,
            precision,
        ),
    )


def upsert_track(cur, track: dict, album_id: str | None) -> None:
    if not track or not track.get("id"):
        return

    cur.execute(
        """
        INSERT INTO dwh.dim_track (
            track_id,
            track_name,
            album_id,
            duration_ms,
            explicit,
            track_number,
            disc_number,
            is_local
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (track_id)
        DO UPDATE SET
            track_name = EXCLUDED.track_name,
            album_id = EXCLUDED.album_id,
            duration_ms = EXCLUDED.duration_ms,
            explicit = EXCLUDED.explicit,
            track_number = EXCLUDED.track_number,
            disc_number = EXCLUDED.disc_number,
            is_local = EXCLUDED.is_local,
            last_seen_at = now();
        """,
        (
            track.get("id"),
            track.get("name"),
            album_id,
            track.get("duration_ms"),
            track.get("explicit"),
            track.get("track_number"),
            track.get("disc_number"),
            track.get("is_local"),
        ),
    )


def upsert_artist(cur, artist: dict) -> None:
    if not artist or not artist.get("id"):
        return

    cur.execute(
        """
        INSERT INTO dwh.dim_artist (
            artist_id,
            artist_name
        )
        VALUES (%s, %s)
        ON CONFLICT (artist_id)
        DO UPDATE SET
            artist_name = EXCLUDED.artist_name,
            last_seen_at = now();
        """,
        (
            artist.get("id"),
            artist.get("name"),
        ),
    )


def upsert_bridge(cur, track_id: str, artist_id: str, artist_order: int) -> None:
    cur.execute(
        """
        INSERT INTO dwh.bridge_track_artist (
            track_id,
            artist_id,
            artist_order
        )
        VALUES (%s, %s, %s)
        ON CONFLICT (track_id, artist_id)
        DO UPDATE SET
            artist_order = EXCLUDED.artist_order;
        """,
        (track_id, artist_id, artist_order),
    )


def insert_fact_play(cur, played_at: str, track_id: str, context_type: str | None, context_uri: str | None) -> None:
    cur.execute(
        """
        INSERT INTO dwh.fact_play (
            played_at,
            track_id,
            context_type,
            context_uri
        )
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (played_at, track_id)
        DO NOTHING;
        """,
        (played_at, track_id, context_type, context_uri),
    )


def main() -> None:
    staging_rows = load_rows_from_staging()

    with psycopg.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            for payload in staging_rows:
                if isinstance(payload, str):
                    payload = json.loads(payload)

                track = payload.get("track", {})
                album = track.get("album", {})
                artists = track.get("artists", [])
                played_at = payload.get("played_at")
                context = payload.get("context") or {}

                track_id = track.get("id")
                if not played_at or not track_id:
                    continue

                upsert_album(cur, album)
                upsert_track(cur, track, album.get("id"))

                for idx, artist in enumerate(artists):
                    upsert_artist(cur, artist)
                    upsert_bridge(cur, track_id, artist.get("id"), idx)

                insert_fact_play(
                    cur,
                    played_at,
                    track_id,
                    context.get("type"),
                    context.get("uri"),
                )

        conn.commit()

    print("Carga no DWH concluída com sucesso.")


if __name__ == "__main__":
    main()