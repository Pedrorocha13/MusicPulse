SELECT
    DATE(played_at) AS play_date,
    COUNT(*) AS total_plays
FROM dwh.fact_play
GROUP BY DATE(played_at)
ORDER BY play_date DESC;
