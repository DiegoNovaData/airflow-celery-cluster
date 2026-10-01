"""Hostname que cada componente de Airflow registra en la metadata DB.

Airflow guarda en cada TaskInstance el "hostname" del worker que la ejecutó y
el webserver lo usa para pedirle los logs en vivo (http://<hostname>:8793).
Por defecto es el FQDN del servidor, que el master tiene que poder resolver.

Con AIRFLOW_ADVERTISED_HOST (en el worker = WORKER_IP del .env) se anuncia la
IP directamente, sin depender de DNS ni de /etc/hosts.

Se activa con:  AIRFLOW__CORE__HOSTNAME_CALLABLE=cluster_hostname.get_hostname
"""
from __future__ import annotations

import os

from airflow.utils.net import getfqdn


def get_hostname() -> str:
    return os.environ.get("AIRFLOW_ADVERTISED_HOST") or getfqdn()
