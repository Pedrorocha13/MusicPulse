SELECT
    a.artist_name,
    COUNT(*) AS total_plays
FROM dwh.fact_play fp
JOIN dwh.bridge_track_artist ta
    ON fp.track_id = ta.track_id
JOIN dwh.dim_artist a
    ON ta.artist_id = a.artist_id
GROUP BY a.artist_name
ORDER BY total_plays DESC
LIMIT 10;