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

<br>
<img width="435" height="452" alt="Logic" src="https://github.com/user-attachments/assets/f8420a5c-89d0-4c58-8e7b-f85dc7325570" />
<br/>
