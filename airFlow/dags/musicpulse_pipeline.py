from datetime import datetime, timedelta

from airflow.sdk import DAG
from airflow.providers.standard.operators.bash import BashOperator

default_args = {
    'owner': 'pedro',
    'depends_on_past': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=2),
}

with DAG(
    dag_id='musicpulse_pipeline',
    description='Pipeline ETL do MusicPulse com ingestão Spotify e carga DMW',
    start_date=datetime(2024, 3, 26),
    schedule="@daily",
    catchup=False,
    default_args=default_args ,
    tags=['musicpulse', 'spotify', 'etl'],
) as dag:
    
    ingest_recently_played = BashOperator(
        task_id='ingest_recently_played',
        bash_command="""
        set -euxo pipefail
        cd /opt/airflow/project/Flask/etl
        python3 ingest_recently_played.py
        """
    )

    ingest_top_tracks = BashOperator(
        task_id='ingest_top_tracks',
        bash_command="""
        set -euxo pipefail
        cd /opt/airflow/project/Flask/etl
        python3 ingest_top_tracks.py
        """
    )

    load_dhw = BashOperator(
        task_id='load_dhw',
        bash_command="""
        set -euxo pipefail
        cd /opt/airflow/project/Flask/etl
        python3 load_dwh_from_recently_played.py
        """
    )

    ingest_recently_played >> load_dhw
    ingest_top_tracks >> load_dhw