-- Query 1: base de preferência
SELECT
    fp.track_id,
    t.track_name,
    COUNT(*) AS total_plays,
    MAX(fp.played_at) AS last_played_at
FROM dwh.fact_play fp
JOIN dwh.dim_track t
    ON fp.track_id = t.track_id
GROUP BY fp.track_id, t.track_name
ORDER BY total_plays DESC, last_played_at DESC;


-- Query 2: ranking pessoal
SELECT
    track_id,
    track_name,
    total_plays,
    last_played_at,
    ROW_NUMBER() OVER (
        ORDER BY total_plays DESC, last_played_at DESC
    ) AS personal_rank
FROM (
    SELECT
        fp.track_id,
        t.track_name,
        COUNT(*) AS total_plays,
        MAX(fp.played_at) AS last_played_at
    FROM dwh.fact_play fp
    JOIN dwh.dim_track t
        ON fp.track_id = t.track_id
    GROUP BY fp.track_id, t.track_name
) ranked;


-- Query 3: ranking de artistas
SELECT
    artist_name,
    total_plays,
    ROW_NUMBER() OVER (
        ORDER BY total_plays DESC
    ) AS artist_rank
FROM (
    SELECT
        a.artist_name,
        COUNT(*) AS total_plays
    FROM dwh.fact_play fp
    JOIN dwh.bridge_track_artist bta
        ON fp.track_id = bta.track_id
    JOIN dwh.dim_artist a
        ON bta.artist_id = a.artist_id
    GROUP BY a.artist_name
) ranked_artists;