# 🎧 MusicPulse

> Pipeline de dados pessoal que coleta hábitos de escuta do Spotify, armazena em um Data Warehouse PostgreSQL e gera análises SQL sobre preferências musicais.

<br>

<img width="435" height="452" alt="Diagrama lógico do projeto" src="https://github.com/user-attachments/assets/f8420a5c-89d0-4c58-8e7b-f85dc7325570" />

---

## Índice

- [Visão Geral](#-visão-geral)
- [Stack](#-stack)
- [Arquitetura](#-arquitetura)
- [Modelagem de Dados](#-modelagem-de-dados)
- [Pré-requisitos](#-pré-requisitos)
- [Configuração](#-configuração)
- [Como Executar](#-como-executar)
- [Análises SQL](#-análises-sql)
- [Estrutura do Projeto](#-estrutura-do-projeto)
- [Roadmap](#️-roadmap)
- [Autor](#-autor)

---

## 🔍 Visão Geral

O MusicPulse conecta à **Spotify Web API** via OAuth 2.0, ingere dados de músicas recentemente tocadas e top tracks, armazena os payloads brutos numa **camada de staging** e os transforma num **modelo dimensional** (DWH) pronto para análise.

**O que você vai obter ao rodar o projeto:**

- Histórico completo de músicas ouvidas (até 50 plays por chamada, paginado)
- Ranking pessoal de top tracks por período (últimas 4 semanas, 6 meses e todos os tempos)
- Dimensões de artista, álbum e faixa normalizadas
- Queries prontas para responder perguntas como: "quais artistas dominam minha escuta?" ou "em qual dia ouço mais música?"

---

## 🛠 Stack

| Tecnologia | Uso |
|---|---|
| Python 3.11+ | ETL, servidor OAuth |
| Flask 3 | Servidor OAuth 2.0 local |
| PostgreSQL 16 | Banco de dados (staging + DWH) |
| Docker / Docker Compose | Infraestrutura local |
| psycopg 3 | Driver PostgreSQL |
| Spotify Web API | Fonte de dados |
| pgAdmin 4 | Interface visual do banco |
| Power BI | Dashboard (em desenvolvimento) |

---

## 🚀 Arquitetura

```mermaid
flowchart LR
    A[Spotify Web API] -->|OAuth 2.0| B[Flask app.py]
    B -->|tokens.json| C[Python ETL Scripts]
    C -->|payload bruto| D[(stg — Staging)]
    D -->|transformação| E[(dwh — Data Warehouse)]
    E -->|SQL queries| F[Análises / Power BI]
```

**Fluxo passo a passo:**

1. `app.py` inicia o servidor Flask e executa o handshake OAuth com o Spotify
2. Os tokens de acesso ficam salvos em `tokens.json` (local, apenas para desenvolvimento)
3. Os scripts ETL usam o token para chamar a API e gravar o payload bruto no schema `stg`
4. `load_dwh_from_recently_played.py` lê o staging e popula as dimensões e a tabela de fatos no schema `dwh`
5. As queries em `analytics/` rodam direto no PostgreSQL (via pgAdmin, psql ou Power BI)

---

## 🗄 Modelagem de Dados

### Staging — dados brutos da API

| Tabela | Descrição |
|---|---|
| `stg.spotify_recently_played` | Histórico de plays com payload JSON completo |
| `stg.spotify_top_tracks` | Top tracks por período (short / medium / long term) |
| `stg.spotify_top_artists` | Top artists por período *(tabela criada, ingestão em roadmap)* |

### Data Warehouse — modelo dimensional

```
dwh.dim_album
dwh.dim_artist
dwh.dim_track          ──FK──> dim_album
dwh.bridge_track_artist ──FK──> dim_track, dim_artist  (N:N)
dwh.fact_play          ──FK──> dim_track
```

| Tabela | Tipo | Descrição |
|---|---|---|
| `dwh.dim_track` | Dimensão | Faixas com metadados |
| `dwh.dim_artist` | Dimensão | Artistas |
| `dwh.dim_album` | Dimensão | Álbuns com data de lançamento |
| `dwh.bridge_track_artist` | Bridge | Relacionamento N:N track ↔ artist |
| `dwh.fact_play` | Fato | Cada play com timestamp e contexto |

---

## ✅ Pré-requisitos

Antes de começar, certifique-se de ter instalado:

- [Python 3.11+](https://www.python.org/downloads/)
- [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- Uma conta no [Spotify](https://www.spotify.com) (gratuita funciona)
- Acesso ao [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)

---

## ⚙️ Configuração

### 1. Clone o repositório

```bash
git clone https://github.com/seu-usuario/MusicPulse.git
cd MusicPulse/Flask
```

### 2. Crie o app no Spotify Developer Dashboard

1. Acesse [developer.spotify.com/dashboard](https://developer.spotify.com/dashboard)
2. Clique em **Create App**
3. Preencha nome e descrição (qualquer valor serve)
4. Em **Redirect URIs**, adicione exatamente: `http://127.0.0.1:8888/callback`
5. Marque **Web API** nos usos da API
6. Salve e copie o **Client ID** e o **Client Secret**

### 3. Configure as variáveis de ambiente

```bash
# Copie o template
cp .env.example .env
```

Edite o `.env` com seus valores:

| Variável | Descrição | Exemplo |
|---|---|---|
| `FLASK_SECRET_KEY` | Chave secreta do Flask (qualquer string longa e aleatória) | `minha-chave-super-secreta-123` |
| `SPOTIFY_CLIENT_ID` | Client ID do seu app no Spotify Dashboard | `abc123...` |
| `SPOTIFY_CLIENT_SECRET` | Client Secret do seu app no Spotify Dashboard | `xyz789...` |
| `SPOTIFY_REDIRECT_URI` | Deve ser exatamente igual ao cadastrado no Dashboard | `http://127.0.0.1:8888/callback` |
| `DATABASE_URL` | String de conexão PostgreSQL | `postgresql://musicpulse:senha@localhost:5432/musicpulse` |
| `POSTGRES_PASSWORD` | Senha do PostgreSQL (usada pelo Docker Compose) | `sua-senha-segura` |
| `PGADMIN_PASSWORD` | Senha do pgAdmin (usada pelo Docker Compose) | `sua-senha-segura` |

> **Segurança:** nunca comite o arquivo `.env`. O `.gitignore` já deve excluí-lo. O arquivo `tokens.json` também não deve ser comitado.

### 4. Instale as dependências Python

```bash
pip install -r requirements.txt
```

---

## ▶️ Como Executar

### Passo 1 — Suba a infraestrutura

```bash
docker compose up -d
```

Aguarde o container do PostgreSQL ficar `healthy`. Verifique com:

```bash
docker compose ps
```

O schema do banco (`stg` e `dwh`) é criado automaticamente a partir de `database/init/001_schema.sql` no primeiro boot.

Acesse o pgAdmin em **http://localhost:5050** (e-mail e senha definidos no `.env`).

---

### Passo 2 — Autentique com o Spotify

```bash
python app.py
```

Acesse **http://127.0.0.1:8888/login** no navegador, autorize o app e aguarde a confirmação. Os tokens serão salvos em `tokens.json`.

> O servidor Flask pode ser encerrado após a autenticação.

---

### Passo 3 — Ingira os dados do Spotify

Execute a partir da pasta `Flask/`:

```bash
# Músicas recentemente tocadas (histórico de até ~200 plays)
python etl/ingest_recently_played.py

# Top tracks (short_term, medium_term e long_term)
python etl/ingest_top_tracks.py
```

Os dados brutos são salvos nas tabelas `stg.*`.

---

### Passo 4 — Transforme para o Data Warehouse

```bash
python etl/load_dwh_from_recently_played.py
```

Este script lê o staging, normaliza artistas/álbuns/faixas e popula as tabelas `dwh.*`.

---

### Passo 5 — Execute as análises

Abra as queries em `analytics/` no pgAdmin ou em qualquer cliente SQL conectado ao banco:

| Arquivo | O que responde |
|---|---|
| `analytics/top_tracks.sql` | Quais faixas você mais ouviu |
| `analytics/top_artists.sql` | Quais artistas dominam sua escuta |
| `analytics/plays_per_day.sql` | Em quais dias você mais ouve música |
| `analytics/hype_queries.sql` | Ranking pessoal com window functions |

---

## 📊 Análises SQL

### Músicas mais ouvidas

```sql
SELECT
    t.track_name,
    COUNT(*) AS total_plays
FROM dwh.fact_play fp
JOIN dwh.dim_track t ON fp.track_id = t.track_id
GROUP BY t.track_name
ORDER BY total_plays DESC
LIMIT 10;
```

### Artistas mais ouvidos

```sql
SELECT
    a.artist_name,
    COUNT(*) AS total_plays
FROM dwh.fact_play fp
JOIN dwh.bridge_track_artist bta ON fp.track_id = bta.track_id
JOIN dwh.dim_artist a            ON bta.artist_id = a.artist_id
GROUP BY a.artist_name
ORDER BY total_plays DESC
LIMIT 10;
```

### Plays por dia

```sql
SELECT
    DATE(played_at) AS play_date,
    COUNT(*)        AS total_plays
FROM dwh.fact_play
GROUP BY DATE(played_at)
ORDER BY play_date DESC;
```

### Ranking pessoal com window function

```sql
SELECT
    track_name,
    total_plays,
    ROW_NUMBER() OVER (ORDER BY total_plays DESC, last_played_at DESC) AS personal_rank
FROM (
    SELECT
        t.track_name,
        COUNT(*)        AS total_plays,
        MAX(fp.played_at) AS last_played_at
    FROM dwh.fact_play fp
    JOIN dwh.dim_track t ON fp.track_id = t.track_id
    GROUP BY t.track_name
) ranked;
```

---

## 📁 Estrutura do Projeto

```
Flask/
├── app.py                          # Servidor Flask — OAuth 2.0 com Spotify
├── requirements.txt                # Dependências Python
├── docker-compose.yml              # PostgreSQL + pgAdmin
├── .env.example                    # Template de variáveis de ambiente
├── tokens.json                     # Tokens OAuth (gerado em runtime, não comitar)
│
├── etl/
│   ├── spotify_auth.py             # Módulo compartilhado: tokens, refresh, helpers
│   ├── ingest_recently_played.py   # Ingere histórico de plays → stg
│   ├── ingest_top_tracks.py        # Ingere top tracks → stg
│   └── load_dwh_from_recently_played.py  # Staging → DWH dimensional
│
├── analytics/
│   ├── top_tracks.sql              # Top músicas
│   ├── top_artists.sql             # Top artistas
│   ├── plays_per_day.sql           # Volume por dia
│   └── hype_queries.sql            # Rankings com window functions
│
└── database/
    └── init/
        └── 001_schema.sql          # DDL completo (schemas, tabelas, índices)
```

---

## 🗺️ Roadmap

### Módulo 1 — Hype Score
- [x] Autenticação OAuth com Spotify
- [x] Ingestão de recently played
- [x] Ingestão de top tracks
- [x] PostgreSQL Data Warehouse
- [x] Queries analíticas SQL
- [ ] Comparação com tendências regionais
- [ ] Dashboard Power BI
- [ ] Agendador de pipeline

### Módulo 2 — HeatMap Brazil
- [ ] Mapa de calor de artistas por estado

### Módulo 3 — Artist Affinity
- [ ] Probabilidade de artistas favoritos aparecerem na sua região

### Infra
- [ ] Deploy em cloud (AWS / GCP)

---

## 👤 Autor

**Pedro Rocha**

Projeto desenvolvido para explorar Engenharia de Dados aplicada a comportamento musical, cobrindo o ciclo completo: ingestão, modelagem dimensional, análise SQL e visualização.
