SELECT
    t.track_name,
    COUNT(*) AS total_plays
FROM dwh.fact_play fp
JOIN dwh.dim_track t
    ON fp.track_id = t.track_id
GROUP BY t.track_name
ORDER BY total_plays DESC
LIMIT 20;