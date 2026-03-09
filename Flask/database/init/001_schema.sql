CREATE SCHEMA IF NOT EXISTS stg;
CREATE SCHEMA IF NOT EXISTS dwh;
CREATE TABLE IF NOT EXISTS stg.spotify_recently_played (
    batch_id            uuid            NOT NULL,
    ingested_at         timestamptz     NOT NULL DEFAULT now(),

    played_at           timestamptz     NOT NULL,
    track_id            text            NOT NULL,
    context_type        text            NULL,
    context_uri         text            NULL,

    -- payload bruto pra você não perder nada (debug / reprocess)
    payload_json        jsonb           NOT NULL,

    CONSTRAINT pk_stg_recently_played PRIMARY KEY (played_at, track_id)
);
CREATE TABLE IF NOT EXISTS dwh.dim_artist (
    artist_id       text        PRIMARY KEY,
    artist_name     text        NOT NULL,
    -- campos que podem mudar (popularidade, followers)
    last_seen_at    timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS dwh.dim_album (
    album_id        text        PRIMARY KEY,
    album_name      text        NOT NULL,
    release_date    date        NULL,
    release_date_precision text  NULL,
    last_seen_at    timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS dwh.dim_track (
    track_id        text        PRIMARY KEY,
    track_name      text        NOT NULL,
    album_id        text        NULL REFERENCES dwh.dim_album(album_id),
    duration_ms     int         NULL,
    explicit        boolean     NULL,
    track_number    int         NULL,
    disc_number     int         NULL,
    is_local        boolean     NULL,
    last_seen_at    timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS dwh.bridge_track_artist (
    track_id    text NOT NULL REFERENCES dwh.dim_track(track_id),
    artist_id   text NOT NULL REFERENCES dwh.dim_artist(artist_id),
    artist_order int NULL,  -- ordem do artista na faixa (0,1,2...)
    PRIMARY KEY (track_id, artist_id)
);
CREATE TABLE IF NOT EXISTS dwh.fact_play (
    played_at       timestamptz NOT NULL,
    track_id        text        NOT NULL REFERENCES dwh.dim_track(track_id),

    -- útil pra análises por contexto
    context_type    text        NULL,
    context_uri     text        NULL,

    -- partição por tempo no futuro (opcional)
    ingested_at     timestamptz NOT NULL DEFAULT now(),

    PRIMARY KEY (played_at, track_id)
);
CREATE TABLE IF NOT EXISTS stg.spotify_top_tracks (
    batch_id        uuid            NOT NULL,
    ingested_at     timestamptz     NOT NULL DEFAULT now(),
    time_range      text            NOT NULL, -- short_term / medium_term / long_term
    rank            int             NOT NULL,
    track_id        text            NOT NULL,
    payload_json    jsonb           NOT NULL,
    PRIMARY KEY (time_range, rank, track_id, ingested_at)
);
CREATE TABLE IF NOT EXISTS stg.spotify_top_artists (
    batch_id        uuid            NOT NULL,
    ingested_at     timestamptz     NOT NULL DEFAULT now(),
    time_range      text            NOT NULL,
    rank            int             NOT NULL,
    artist_id       text            NOT NULL,
    payload_json    jsonb           NOT NULL,
    PRIMARY KEY (time_range, rank, artist_id, ingested_at)
);
-- Plays: filtrar por período é comum
CREATE INDEX IF NOT EXISTS idx_fact_play_played_at
ON dwh.fact_play (played_at);

-- Plays: agregações por track são comuns
CREATE INDEX IF NOT EXISTS idx_fact_play_track_id
ON dwh.fact_play (track_id);

-- Bridge: buscar artistas de uma track
CREATE INDEX IF NOT EXISTS idx_bridge_track_artist_track
ON dwh.bridge_track_artist (track_id);

-- Bridge: buscar tracks de um artista
CREATE INDEX IF NOT EXISTS idx_bridge_track_artist_artist
ON dwh.bridge_track_artist (artist_id);