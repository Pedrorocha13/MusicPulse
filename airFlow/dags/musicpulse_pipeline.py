from datetime import datetime, timedelta

from airflow.sdk import DAG
from airflow.providers.standard.operators.bash import BashOperator

default_args = {
    "owner": "pedro",
    "depends_on_past": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=2),
}

with DAG(
    dag_id="musicpulse_pipeline",
    description="Pipeline ETL do MusicPulse com ingestão Spotify e carga DWH",
    start_date=datetime(2026, 3, 26),
    schedule="@daily",
    catchup=False,
    default_args=default_args,
    tags=["musicpulse", "spotify", "etl"],
) as dag:

    ingest_recently_played = BashOperator(
        task_id="ingest_recently_played",
        bash_command="""
        set -euxo pipefail
        cd /opt/airflow/project/Flask/etl
        python ingest_recently_played.py
        """,
    )

    ingest_top_tracks = BashOperator(
        task_id="ingest_top_tracks",
        bash_command="""
        set -euxo pipefail
        cd /opt/airflow/project/Flask/etl
        python ingest_top_tracks.py
        """,
    )

    load_dwh = BashOperator(
        task_id="load_dwh",
        bash_command="""
        set -euxo pipefail
        cd /opt/airflow/project/Flask/etl
        python load_dwh_from_recently_played.py
        """,
    )

    validate_dwh = BashOperator(
        task_id="validate_dwh",
        bash_command="""
        set -euxo pipefail
        cd /opt/airflow/project/Flask
        python -c "
import os
from pathlib import Path
from dotenv import load_dotenv
import psycopg

base_dir = Path('/opt/airflow/project/Flask')
load_dotenv(base_dir / '.env')

database_url = os.getenv('DATABASE_URL')
if not database_url:
    raise ValueError('DATABASE_URL não encontrada no ambiente.')

with psycopg.connect(database_url) as conn:
    with conn.cursor() as cur:
        cur.execute('SELECT COUNT(*) FROM dwh.fact_play;')
        fact_play_count = cur.fetchone()[0]

        cur.execute('SELECT COUNT(*) FROM dwh.dim_track;')
        dim_track_count = cur.fetchone()[0]

        print(f'Total de registros em dwh.fact_play: {fact_play_count}')
        print(f'Total de registros em dwh.dim_track: {dim_track_count}')

        if fact_play_count == 0:
            raise Exception('Validação falhou: dwh.fact_play está vazio.')

        if dim_track_count == 0:
            raise Exception('Validação falhou: dwh.dim_track está vazio.')
"
        """,
    )

    [ingest_recently_played, ingest_top_tracks] >> load_dwh >> validate_dwh # type: ignore