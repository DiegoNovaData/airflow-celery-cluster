# Changelog

Formato basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/),
versionado [SemVer](https://semver.org/lang/es/).

## [2.0.0] - 2026-10-01

### Añadido
- `MASTER_IP` (master y worker), `WORKER_IPS` (master) y `WORKER_IP` (worker) en los `.env`.
  [ADR-0011](docs/adr/0011-ips-del-cluster-en-env.md)
- `master/cluster_hostname.py`: el worker registra sus tareas con `WORKER_IP` como hostname, así
  el webserver le pide los logs en vivo sin DNS ni `/etc/hosts`.
- Los comandos de firewall y NFS de README, `docs/nfs.md`, `docs/redis.md` y `docs/flower.md`
  leen las IPs y rutas del `.env` en lugar de usar valores escritos a mano.
- Drop-in de systemd para que Docker espere los montajes NFS, generado desde `AIRFLOW_DATA_DIR`.
- `WORKER_NAME` (worker): nombre único del worker, que es su hostname y su nombre Celery en Flower.
- ADR-0010, ADR-0011 y ADR-0012.

### Cambiado
- Los puertos del master (8080, 5555, 6379, 5432) se publican solo en `MASTER_IP`, no en `0.0.0.0`.
- El worker pasa de `network_mode: host` a red bridge con `hostname: ${WORKER_NAME}` y el puerto
  8793 publicado en `WORKER_IP`, igual que el compose de los workers de producción.
  [ADR-0012](docs/adr/0012-worker-en-red-bridge.md)
- `AIRFLOW_BASE_URL` se arma por defecto con `http://${MASTER_IP}:${AIRFLOW_WEBSERVER_PORT}`.
- `Dockerfile`: vuelve al `ENTRYPOINT` oficial (`dumb-init` + `/entrypoint`).
- El estado de ADR-0002 y ADR-0003 pasa a "Reemplazado por ADR-0010", y ADR-0007 se marca como
  modificado por ADR-0010 y ADR-0011.

### Eliminado
- Todo el soporte de Oracle Instant Client: `master/entrypoint.sh`, `worker/docker-compose.oracle.yml`,
  `libaio1` en la imagen y las variables `ORACLE_*` y `TNS_ADMIN`.
  [ADR-0010](docs/adr/0010-sin-soporte-oracle.md)
- `MASTER_HOST`, reemplazada por `MASTER_IP`.

## [1.0.0] - 2026-10-01

Primera versión publicable. Parte de la configuración en producción (0.1.0), ya sanitizada,
y corrige los hallazgos de [docs/revision-inicial.md](docs/revision-inicial.md).

### Añadido
- `AIRFLOW__WEBSERVER__SECRET_KEY` (`AIRFLOW_SECRET_KEY`) en master y worker, igual en ambos
  para que el webserver pueda pedir logs a los workers. [ADR-0001](docs/adr/0001-secret-key-compartida.md)
- `worker/docker-compose.yml` reescrito como worker Celery real. [ADR-0007](docs/adr/0007-worker-celery-dedicado.md)
- `worker/docker-compose.oracle.yml`: override opcional para Oracle Instant Client.
- `worker/.env.example` (antes estaba vacío).
- Healthcheck del worker (`celery inspect ping`) y `DUMB_INIT_SETSID=0` para *warm shutdown*.
- Autenticación opcional de Flower con `FLOWER_BASIC_AUTH`.
- Variables configurables por `.env` con valores por defecto: concurrencia, SMTP, puertos,
  rutas (`AIRFLOW_DATA_DIR`), nombre de imagen y versiones. [ADR-0008](docs/adr/0008-configuracion-por-env.md)
- Validación de secretos obligatorios con `${VAR:?}`: compose falla con un mensaje claro si faltan.
- `.gitattributes` que fuerza finales de línea LF.
- `dags/test_worker_rapido.py` (DAG de humo).
- Documentación: README, `docs/nfs.md`, `docs/redis.md`, `docs/flower.md`,
  `docs/revision-inicial.md` y ADRs 0001–0009.

### Cambiado
- `AIRFLOW__CORE__PARALLELISM` pasa de un valor fijo `4` a `AIRFLOW_PARALLELISM`, con default `32`.
  El valor 4 limitaba todo el cluster a 4 tareas simultáneas. Lo mismo para `MAX_ACTIVE_TASKS_PER_DAG`
  (2 → 16) y `MAX_ACTIVE_RUNS_PER_DAG` (1 → 16). Los defaults son los de Airflow.
- SMTP: host, puerto, STARTTLS, SSL y remitente pasan del compose al `.env`.
- `Dockerfile`: recibe `AIRFLOW_VERSION` y `PYTHON_VERSION` como `ARG`. La imagen base pasa a ser
  `apache/airflow:<versión>-python<versión>` (Python explícito) y los constraints se derivan de los mismos
  valores. Antes, `AIRFLOW_BASE_IMAGE` se pasaba pero el Dockerfile lo ignoraba.
- `Dockerfile`: `ENTRYPOINT` vuelve a usar `dumb-init` como PID 1. [ADR-0003](docs/adr/0003-dumb-init-como-pid1.md)
- `requirements.txt`: `great-expectations>=1.0.0` → `==1.23.2`. Se instala junto con
  `apache-airflow==<versión>` para que pip no pueda cambiar Airflow. [ADR-0004](docs/adr/0004-dependencias-reproducibles.md)
- `airflow-init`: `db migrate` ya no oculta errores (`set -e`), y el usuario admin solo se crea
  si no existe. El webserver, el scheduler y Flower esperan a que `airflow-init` termine bien.
  [ADR-0006](docs/adr/0006-airflow-init-como-compuerta.md)
- Volúmenes: `:Z` → `:z`. [ADR-0005](docs/adr/0005-etiqueta-selinux-compartida.md)
- `.env.example`: sin espacios alrededor del `=`, sin comentarios en la misma línea, placeholders
  uniformes (`changeme`, `generar_con_*`), finales LF y errata corregida ("constraseña").
- Imagen renombrada a un nombre genérico configurable (`AIRFLOW_IMAGE_NAME`, default `airflow-celery:2.9.3`).
- `AIRFLOW_UID` en los ejemplos: default `50000` (el de la imagen oficial).
- Comentarios del compose: el encabezado decía "LocalExecutor" y el bloque de Flower decía "Redis".
- `.gitignore`: `*pyc` → `*.pyc`, finales LF, y se añaden `*.tar`, `dags/ultimo_run.txt` y `CLAUDE.md`.

### Corregido
- `entrypoint.sh`: no podía escribir en `/etc/ld.so.conf.d` ni ejecutar `ldconfig` porque corre
  como usuario no-root, y fallaba en silencio. Ahora exporta `LD_LIBRARY_PATH`.
  [ADR-0002](docs/adr/0002-oracle-sin-ldconfig.md)
- El webserver y el scheduler podían arrancar antes de terminar la migración de la DB.
- El worker no levantaba ningún `celery worker` y duplicaba postgres, redis, webserver y scheduler.

### Eliminado
- `sudo` y la regla de `/etc/sudoers.d/airflow` de la imagen: ya no hacen falta.
- Del worker: los montajes `/app/scripts` y `postgres_backup`, que eran específicos del entorno.
  Si se necesitan, se añaden con un `docker-compose.override.yml`.

### Seguridad
- Ningún secreto queda escrito en el compose. Todos salen del `.env`, que está en `.gitignore`.
- Redis sigue sin contraseña: es una decisión documentada, con mitigación por firewall.
  [ADR-0009](docs/adr/0009-redis-sin-password-por-defecto.md)

## [0.1.0] - 2026-09-08

Línea base: configuración tal como corría en producción, sanitizada (sin IPs ni credenciales).
Es una versión de referencia y **no se recomienda desplegarla**. Sus problemas conocidos están
en [docs/revision-inicial.md](docs/revision-inicial.md).

- Master con CeleryExecutor: postgres, redis, init, webserver, scheduler y flower.
- Imagen propia basada en `apache/airflow:2.9.3` con providers SSH y Celery, librerías de datos
  y geoespaciales, y soporte de Oracle Instant Client.
- `worker/docker-compose.yml` copiado del master por error.
