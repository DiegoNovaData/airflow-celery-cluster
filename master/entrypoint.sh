#!/usr/bin/env bash
# Entrypoint propio: prepara Oracle Instant Client (si está montado) y delega
# en el entrypoint oficial de Airflow.
#
# El contenedor corre como usuario no-root (AIRFLOW_UID), así que no puede
# escribir en /etc/ld.so.conf.d ni ejecutar ldconfig. En su lugar se exporta
# LD_LIBRARY_PATH, que no requiere privilegios (ver docs/adr/0002).
set -euo pipefail

ORACLE_CLIENT_LIB_DIR="${ORACLE_CLIENT_LIB_DIR:-/usr/lib/oracle/instantclient_23_26}"

if [[ -d "${ORACLE_CLIENT_LIB_DIR}" ]]; then
    export LD_LIBRARY_PATH="${ORACLE_CLIENT_LIB_DIR}${LD_LIBRARY_PATH:+:${LD_LIBRARY_PATH}}"
    echo "Oracle Instant Client detectado en ${ORACLE_CLIENT_LIB_DIR}"
fi

exec /entrypoint "$@"
