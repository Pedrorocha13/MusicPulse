FROM apache/airflow:3.1.8

USER airflow
COPY requirements-musicpulse.txt /tmp/requirements-musicpulse.txt
RUN pip install --no-cache-dir -r /tmp/requirements-musicpulse.txt