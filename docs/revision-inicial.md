# Revisión inicial: de la configuración en producción a la v1.0.0

Este documento cuenta el punto de partida del proyecto. Los archivos venían de un cluster en
producción, ya sanitizados: sin IPs ni credenciales. Antes de publicarlos se auditaron, y esta es
la lista de hallazgos con lo que se hizo con cada uno. El detalle de cada cambio está en el
[CHANGELOG](../CHANGELOG.md) y el porqué, en los [ADRs](adr/).

**Estados:** ✅ corregido · 📘 documentado / configurable · ⏳ pospuesto

## Hallazgos que afectaban el funcionamiento

| # | Hallazgo | Estado | Resolución |
|---|---|---|---|
| 1 | `AIRFLOW__CORE__PARALLELISM: 4` limitaba **todo el cluster** a 4 tareas simultáneas, sin importar el número de workers. Era un valor heredado de un despliegue con un solo servidor. | ✅📘 | Pasa a `AIRFLOW_PARALLELISM` (default 32) y se explica en el README. [ADR-0008](adr/0008-configuracion-por-env.md) |
| 2 | Faltaba `AIRFLOW__WEBSERVER__SECRET_KEY`. Cada contenedor generaba una distinta, y los logs en vivo daban 403. | ✅ | `AIRFLOW_SECRET_KEY` obligatoria y la misma en todo el cluster. [ADR-0001](adr/0001-secret-key-compartida.md) |
| 3 | `entrypoint.sh` intentaba `ldconfig` sin privilegios y fallaba en silencio. | ✅ | `LD_LIBRARY_PATH`, sin `sudo`. [ADR-0002](adr/0002-oracle-sin-ldconfig.md) |
| 4 | El webserver y el scheduler no esperaban a `airflow-init`, y `\|\| true` ocultaba los fallos de `db migrate`. | ✅ | `set -e` y `service_completed_successfully`. [ADR-0006](adr/0006-airflow-init-como-compuerta.md) |
| 5 | Volúmenes `:Z` (etiqueta privada) en carpetas que montan varios contenedores. | ✅ | `:z`. En origen no fallaba porque SELinux estaba deshabilitado. [ADR-0005](adr/0005-etiqueta-selinux-compartida.md) |

## Seguridad y reproducibilidad

| # | Hallazgo | Estado | Resolución |
|---|---|---|---|
| 6 | Redis expuesto en el 6379 sin contraseña. | ⏳📘 | Se mitiga con firewall y el procedimiento de `requirepass` está documentado. [ADR-0009](adr/0009-redis-sin-password-por-defecto.md), [redis.md](redis.md) |
| 7 | `requirements.txt` sin restricciones y `great-expectations>=1.0.0`. | ✅ | Versiones exactas, instaladas junto con `apache-airflow==<versión>`. [ADR-0004](adr/0004-dependencias-reproducibles.md) |
| 8 | El `ENTRYPOINT` propio eliminaba `dumb-init`. | ✅ | `dumb-init` vuelve a ser PID 1. [ADR-0003](adr/0003-dumb-init-como-pid1.md) |
| 9 | SMTP escrito en el compose, con un puerto no numérico. | ✅📘 | Todo el SMTP se configura en `.env`. |

## Cosméticos

| # | Hallazgo | Estado |
|---|---|---|
| C1 | El encabezado del compose decía "LocalExecutor" y el bloque de Flower tenía el comentario "Redis". | ✅ |
| C2 | Se pasaba `build.args.AIRFLOW_BASE_IMAGE`, pero el Dockerfile tenía un `FROM` fijo. | ✅ Ahora usa `ARG AIRFLOW_VERSION` y `PYTHON_VERSION`. |
| C3 | `.env.example` con espacios alrededor del `=`, comentarios en la misma línea, hostname inválido, errata y finales CRLF. | ✅ |
| C4 | `.gitignore` con `*pyc` y finales CRLF. | ✅ Además se añade `.gitattributes` con LF. |

## Hallazgo urgente

| # | Hallazgo | Estado | Resolución |
|---|---|---|---|
| U1 | `worker/docker-compose.yml` era una copia del master. No levantaba un `celery worker` y apuntaba a `redis`/`postgres` locales. | ✅ | Reescrito como worker dedicado. [ADR-0007](adr/0007-worker-celery-dedicado.md) |
| U2 | `worker/.env.example` estaba vacío. | ✅ | Creado. |

## Pendiente para próximas versiones

- Contraseña en Redis (hallazgo 6).
- Servicio `airflow-triggerer`, si se usan operadores *deferrable*.
- Healthchecks del webserver y el scheduler.
- Lock file completo de dependencias (`pip-compile`).
- Diagramas en `docs/` (`diagrama-arquitectura-general.svg`, `diagrama-flujo-tarea.svg`).
