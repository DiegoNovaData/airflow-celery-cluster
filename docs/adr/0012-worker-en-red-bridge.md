# ADR-0012: Worker en red bridge con nombre propio y puerto de logs publicado

- **Estado:** Aceptado
- **Fecha:** 2026-10-01
- **Modifica a:** [ADR-0007](0007-worker-celery-dedicado.md) (red del worker)

## Contexto
ADR-0007 eligió `network_mode: host` para que el worker se registrara con un hostname alcanzable
desde el master. Hay dos razones para revisarlo:

- Desde [ADR-0011](0011-ips-del-cluster-en-env.md), el worker anuncia `WORKER_IP` como hostname,
  así que el hostname del contenedor ya no importa para los logs.
- El compose de los workers de producción usaba red *bridge* con `hostname:` fijo y el puerto
  8793 publicado, y funcionaba.

## Decisión
- El worker vuelve a la red *bridge* por defecto de Docker Compose.
- `hostname: ${WORKER_NAME}` es obligatorio y único por worker. Es el nombre Celery
  (`celery@WORKER_NAME`) que se ve en Flower y el que usa el healthcheck.
- El log server se publica como `${WORKER_IP}:8793:8793`, solo en la IP del worker.

## Consecuencias
- El contenedor queda aislado de la red del host, salvo el puerto 8793.
- Los nombres en Flower son legibles y estables, por ejemplo `celery@worker-41-default`.
- Si dos workers tienen el mismo `WORKER_NAME`, Celery emite `DuplicateNodenameWarning` y
  Flower los mezcla.
- El firewall del worker debe permitir el 8793 solo desde `MASTER_IP`. Eso no cambia.

## Alternativas consideradas
- **Mantener `network_mode: host`:** funciona, pero expone al contenedor toda la red del servidor
  y ya no aporta nada frente a ADR-0011.
