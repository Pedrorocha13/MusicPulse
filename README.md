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
- [Pipeline com Apache Airflow](#-pipeline-com-apache-airflow)
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
| Apache Airflow 3 | Orquestração e agendamento do pipeline ETL |
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
    C -->|orquestrado por| G[Apache Airflow DAG]
    G -->|ingest_recently_played| D[(stg — Staging)]
    G -->|ingest_top_tracks| D
    D -->|load_dhw| E[(dwh — Data Warehouse)]
    E -->|SQL queries| F[Análises / Power BI]
```

**Fluxo passo a passo:**

1. `app.py` inicia o servidor Flask e executa o handshake OAuth com o Spotify
2. Os tokens de acesso ficam salvos em `tokens.json` (local, apenas para desenvolvimento)
3. O **Apache Airflow** agenda e orquestra a execução diária dos scripts ETL
4. Os scripts ETL usam o token para chamar a API e gravar o payload bruto no schema `stg`
5. `load_dwh_from_recently_played.py` lê o staging e popula as dimensões e a tabela de fatos no schema `dwh`
6. As queries em `analytics/` rodam direto no PostgreSQL (via pgAdmin, psql ou Power BI)

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

---

> **Dica:** Os passos 3 e 4 acima podem ser substituídos pelo Apache Airflow, que os executa automaticamente todo dia. Veja a seção [Pipeline com Apache Airflow](#-pipeline-com-apache-airflow).

---

| Arquivo | O que responde |
|---|---|
| `analytics/top_tracks.sql` | Quais faixas você mais ouviu |
| `analytics/top_artists.sql` | Quais artistas dominam sua escuta |
| `analytics/plays_per_day.sql` | Em quais dias você mais ouve música |
| `analytics/hype_queries.sql` | Ranking pessoal com window functions |

---

## ⚡ Pipeline com Apache Airflow

O Apache Airflow assume o papel de **orquestrador** do projeto: em vez de executar os scripts ETL manualmente a cada vez, o Airflow agenda, monitora e controla automaticamente a execução do pipeline completo, todo dia à meia-noite UTC.

---

### Visão Geral da DAG

```mermaid
flowchart LR
    A([ingest_recently_played]) --> C([load_dhw])
    B([ingest_top_tracks])      --> C
```

| Task | Script executado | O que faz |
|---|---|---|
| `ingest_recently_played` | `etl/ingest_recently_played.py` | Busca o histórico de plays na API do Spotify e salva em `stg.spotify_recently_played` |
| `ingest_top_tracks` | `etl/ingest_top_tracks.py` | Busca as top tracks (short/medium/long term) e salva em `stg.spotify_top_tracks` |
| `load_dhw` | `etl/load_dwh_from_recently_played.py` | Lê o staging e popula as dimensões e a tabela de fatos no schema `dwh` |

As duas tasks de ingestão rodam **em paralelo**. O `load_dhw` só inicia quando **ambas** terminam com sucesso.

---

### Arquitetura dos Serviços Airflow

O stack do Airflow é definido em `airFlow/docker-compose.yml` e sobe **6 serviços**:

| Serviço | Imagem | Função |
|---|---|---|
| `postgres` | `postgres:16` | Banco de metadados interno do Airflow (separado do banco do MusicPulse) |
| `airflow-init` | `apache/airflow:3.1.8` | Roda `airflow db migrate` para inicializar o schema do metadb. Executa uma vez e termina. |
| `airflow-apiserver` | `apache/airflow:3.1.8` | Serve a UI Web do Airflow na porta `8080` e expõe a Execution API usada pelo Scheduler |
| `airflow-dag-processor` | `apache/airflow:3.1.8` | Parseia e valida os arquivos `.py` da pasta `dags/` continuamente |
| `airflow-scheduler` | **imagem customizada** (Dockerfile) | Avalia o schedule de cada DAG e enfileira as execuções. Usa a imagem customizada com as dependências do projeto |
| `airflow-triggerer` | `apache/airflow:3.1.8` | Gerencia tarefas deferidas (sensors assíncronos, etc.) |

> O `airflow-scheduler` usa uma **imagem customizada** (`airFlow/Dockerfile`) que parte do `apache/airflow:3.1.8` e instala os pacotes extras listados em `requirements-musicpulse.txt` (psycopg, requests, etc.).

---

### Volume Compartilhado

Todos os serviços montam `../Flask` em `/opt/airflow/project/Flask`. Isso significa que os scripts ETL da pasta `Flask/etl/` ficam disponíveis **dentro dos containers do Airflow**, sem precisar copiar arquivos. O `tokens.json` também é compartilhado pelo mesmo caminho.

```yaml
volumes:
  - ./dags:/opt/airflow/dags          # DAGs mapeados para dentro do container
  - ./logs:/opt/airflow/logs          # Logs de execução das tasks
  - ./plugins:/opt/airflow/plugins    # Plugins customizados (opcional)
  - ../Flask:/opt/airflow/project/Flask  # Scripts ETL do projeto
```

---

### Pré-requisito Adicional

Antes de subir o Airflow, certifique-se de ter completado a [autenticação OAuth](#passo-2----autentique-com-o-spotify) e gerado o arquivo `Flask/tokens.json`. O Airflow precisará dele para autenticar nas chamadas à API do Spotify.

---

### Como Executar o Airflow

#### 1. Entre na pasta do Airflow

```bash
cd airFlow
```

#### 2. Configure as variáveis de ambiente

Crie um arquivo `.env` dentro de `airFlow/` com o seguinte conteúdo:

```env
# UID do seu usuário Linux/Mac (no Windows com WSL2, use: id -u)
AIRFLOW_UID=50000

# Variáveis de conexão ao banco do MusicPulse (mesmo .env do Flask)
DATABASE_URL=postgresql://musicpulse:sua-senha@host.docker.internal:5432/musicpulse
```

> **Importante:** `host.docker.internal` é o hostname especial que permite aos containers do Airflow acessarem o PostgreSQL do MusicPulse, que sobe em outro `docker-compose.yml`.

#### 3. Suba o stack do Airflow

```bash
docker compose up -d
```

O serviço `airflow-init` inicializará o banco de metadados automaticamente e depois encerrará. Os demais serviços ficarão em execução.

Verifique o status dos containers:

```bash
docker compose ps
```

Aguarde todos estarem `healthy` ou `running`. O `airflow-init` deve aparecer como `exited (0)` — isso é o comportamento esperado.

#### 4. Acesse a UI do Airflow

Abra **http://localhost:8080** no navegador.

- Usuário padrão: `admin`
- Senha padrão: `admin`

> Na primeira vez, o Airflow cria automaticamente o usuário `admin`. Para criar outros usuários ou trocar a senha, use a aba **Security > Users** na UI.

#### 5. Ative e execute a DAG

1. Na lista de DAGs, localize **`musicpulse_pipeline`**
2. Clique no toggle para **ativar** a DAG (o status muda de *Paused* para *Active*)
3. Para acionar manualmente, clique no ícone ▶ **Trigger DAG**
4. Acompanhe o progresso no **Graph View** ou **Grid View**

A DAG também executa automaticamente todo dia no schedule `@daily` (meia-noite UTC).

---

### Monitorando Execuções

- **Grid View:** visão histórica de todas as execuções com status por task (verde = sucesso, vermelho = falha)
- **Graph View:** visualiza as dependências entre tasks em tempo real
- **Logs:** clique em qualquer task e depois em **Log** para ver a saída completa do script Python

---

### Política de Retry

Cada task está configurada com:

```python
default_args = {
    'retries': 2,
    'retry_delay': timedelta(minutes=2),
}
```

Se um script falhar (ex: API do Spotify instável, conexão ao banco), o Airflow tentará novamente até **2 vezes**, aguardando **2 minutos** entre cada tentativa.

---

### Parando o Airflow

```bash
# Para todos os containers mantendo os volumes (metadados preservados)
docker compose stop

# Para e remove containers + volumes (reset completo)
docker compose down -v
```

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
MusicPulse/
│
├── Flask/
│   ├── app.py                          # Servidor Flask — OAuth 2.0 com Spotify
│   ├── requirements.txt                # Dependências Python
│   ├── docker-compose.yml              # PostgreSQL + pgAdmin
│   ├── .env.example                    # Template de variáveis de ambiente
│   ├── tokens.json                     # Tokens OAuth (gerado em runtime, não comitar)
│   │
│   ├── etl/
│   │   ├── spotify_auth.py             # Módulo compartilhado: tokens, refresh, helpers
│   │   ├── ingest_recently_played.py   # Ingere histórico de plays → stg
│   │   ├── ingest_top_tracks.py        # Ingere top tracks → stg
│   │   └── load_dwh_from_recently_played.py  # Staging → DWH dimensional
│   │
│   ├── analytics/
│   │   ├── top_tracks.sql              # Top músicas
│   │   ├── top_artists.sql             # Top artistas
│   │   ├── plays_per_day.sql           # Volume por dia
│   │   └── hype_queries.sql            # Rankings com window functions
│   │
│   └── database/
│       └── init/
│           └── 001_schema.sql          # DDL completo (schemas, tabelas, índices)
│
└── airFlow/
    ├── docker-compose.yml              # Stack completo do Airflow (6 serviços)
    ├── Dockerfile                      # Imagem customizada do scheduler com dependências extras
    ├── requirements-musicpulse.txt     # Pacotes Python instalados no scheduler
    ├── .env                            # Variáveis de ambiente do Airflow (não comitar)
    │
    ├── dags/
    │   └── musicpulse_pipeline.py      # DAG principal: ingestão + carga DWH
    │
    ├── logs/                           # Logs de execução das tasks (gerado em runtime)
    └── plugins/                        # Plugins customizados do Airflow (reservado)
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
- [x] Agendador de pipeline com Apache Airflow

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
