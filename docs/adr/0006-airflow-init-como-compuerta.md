# ADR-0006: `airflow-init` como compuerta de arranque

- **Estado:** Aceptado
- **Fecha:** 2026-10-01

## Contexto
El comando original era `airflow db migrate && airflow users create ... || true`. Por la
precedencia de `&&` y `||`, el `|| true` también ocultaba un fallo de `db migrate`. Además, el
webserver y el scheduler solo dependían de postgres y redis, así que podían arrancar contra una
base sin migrar.

## Decisión
- `airflow-init` corre con `set -e`. Si `db migrate` falla, el contenedor sale con código distinto de 0.
- El usuario admin se crea solo si no existe. Se consulta con `airflow users list`, en lugar de
  ignorar cualquier error.
- Las credenciales llegan por variables de entorno y las expande bash (`$$VAR`), no compose.
  Así, una contraseña con comillas no rompe el comando.
- Webserver, scheduler y Flower usan
  `depends_on: airflow-init: condition: service_completed_successfully`.

## Consecuencias
- Un error de migración detiene el despliegue de forma visible, en lugar de producir
  fallos raros más adelante.
- `docker compose up` es idempotente: puede ejecutarse muchas veces sin duplicar el admin.

## Alternativas consideradas
- **`_AIRFLOW_DB_MIGRATE` y `_AIRFLOW_WWW_USER_CREATE` del entrypoint oficial:** también ignoran
  los errores de migración (`airflow db migrate || true` en `entrypoint_prod.sh` de 2.9.3).
