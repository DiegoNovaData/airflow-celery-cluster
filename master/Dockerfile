# =============================================================================
# Imagen personalizada de Airflow (master y workers usan la misma imagen)
# =============================================================================
# La versión de Airflow y de Python se reciben como build args desde
# docker-compose (.env). Ambas se usan para el tag base y para el archivo de
# constraints, así nunca quedan desalineadas.
# Imagen multi-arquitectura: el mismo Dockerfile construye amd64 y arm64.

ARG AIRFLOW_VERSION=2.9.3
ARG PYTHON_VERSION=3.12

FROM apache/airflow:${AIRFLOW_VERSION}-python${PYTHON_VERSION}

# Los ARG declarados antes de FROM no son visibles después; se redeclaran.
ARG AIRFLOW_VERSION
ARG PYTHON_VERSION

USER root
# libaio1: requerida por Oracle Instant Client (opcional, ver worker/docker-compose.oracle.yml)
RUN apt-get update \
    && apt-get install -y --no-install-recommends libaio1 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*
COPY entrypoint.sh /custom-entrypoint.sh
RUN chmod +x /custom-entrypoint.sh
USER airflow

# Providers horneados en la imagen, resueltos con los constraints oficiales
RUN pip install --no-cache-dir \
    "apache-airflow==${AIRFLOW_VERSION}" \
    apache-airflow-providers-ssh \
    apache-airflow-providers-celery \
    --constraint "https://raw.githubusercontent.com/apache/airflow/constraints-${AIRFLOW_VERSION}/constraints-${PYTHON_VERSION}.txt"

# Librerías propias. Se repite apache-airflow==<versión> para que pip no pueda
# actualizar ni bajar Airflow al resolver estas dependencias (ver docs/adr/0004).
COPY requirements.txt /requirements.txt
RUN pip install --no-cache-dir "apache-airflow==${AIRFLOW_VERSION}" -r /requirements.txt

# dumb-init es el PID 1 de la imagen oficial: reenvía señales y recoge procesos
# zombie. Se mantiene delante del entrypoint propio (ver docs/adr/0003).
ENTRYPOINT ["/usr/bin/dumb-init", "--", "/custom-entrypoint.sh"]
