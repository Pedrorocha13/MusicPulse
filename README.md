# 🎧 MusicPulse — Spotify Data Engineering Project

Pipeline de dados construído para analisar hábitos musicais pessoais e comparar preferências com tendências do Spotify.

O projeto coleta dados reais da **Spotify Web API**, armazena em um **Data Warehouse PostgreSQL** e executa análises SQL para entender padrões de escuta.

---

# 🚀 Arquitetura

## Stack Tecnológica

* Python
* PostgreSQL
* Docker
* Spotify Web API
* SQL (Window Functions)
* Power BI
* pgAdmin

## Modelagem de Dados

### Staging Layer

Dados brutos da API:
```
stg.spotify_recently_played
stg.spotify_top_tracks
stg.spotify_top_artists
```

### Data Warehouse

Dimensões:
```
dwh.dim_track
dwh.dim_artist
dwh.dim_album
```

Fatos:
```
dwh.fact_play
```

Relacionamento N:N:
```
dwh.bridge_track_artist
```

## Pipeline de Dados
### Fluxo completo do pipeline:
1. Autenticação OAuth com Spotify
2. Ingestão de dados da API (recently-played)
3. Armazenamento em staging
4. Transformação para modelo dimensional
5. Queries analíticas SQL
6. Visualização em dashboard


```mermaid
flowchart LR
    A[Spotify Web API] --> B[Python ETL]
    B --> C[(PostgreSQL)]
    C --> D[Data Warehouse]
    D --> E[SQL Analytics]
    E --> F[Power BI Dashboard]
```

## Exemplos de Queries
### Top músicas mais ouvidas
```SQL
SELECT
    t.track_name,
    COUNT(*) AS total_plays
FROM dwh.fact_play fp
JOIN dwh.dim_track t
    ON fp.track_id = t.track_id
GROUP BY t.track_name
ORDER BY total_plays DESC
LIMIT 10;
```

### Ranking de Artistas
```SQL
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
```

## Como rodar o projeto
### 1 - Subir Infraestrutura
```
docker-compose up -d
```
### 2 - Fazer login no Web Spotify API pelo app.py 
```
python app.py
```
### 3 - Rodar ingestão
```
python etl/ingest_recently_played.py
```
### 4 - Rodar transformação
```
python etl/load_dwh_from_recently_played.py
```

## Dashboard (Em desenvolvimento) 
### O dashboard exibirá:
* músicas mais ouvidas
* artistas mais ouvidos
* evolução temporal de escuta
* comparação com hype regional
```
/docs/dashboard.png
```

## 🗺 Roadmap
### Módulo 1 (Hype Score)
- ✅ Spotify OAuth Authentication

- ✅ Data ingestion pipeline

- ✅ PostgreSQL Data Warehouse

- ✅ SQL analytics queries

-  Top tracks ingestion

-  Regional hype comparison

-  Power BI dashboard

-  Pipeline scheduler

-  Cloud deployment
### Módulo 2 (HeatMap Brazil)

### Módulo 3 (Prefered artists problably shows in your state)

## Objetivo do Projeto
### Explorar engenharia de dados aplicada a comportamento musical, criando um pipeline completo de ingestão, modelagem e análise de dados.

## Autor
### Eu (Pedro Rocha :D)

<br>
<img width="435" height="452" alt="Logic" src="https://github.com/user-attachments/assets/f8420a5c-89d0-4c58-8e7b-f85dc7325570" />
<br/>
