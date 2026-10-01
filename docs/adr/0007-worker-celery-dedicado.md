# ADR-0007: Worker Celery dedicado con red del host

- **Estado:** Aceptado. Modificado por [ADR-0010](0010-sin-soporte-oracle.md) (Oracle), [ADR-0011](0011-ips-del-cluster-en-env.md) (IPs y hostname) y [ADR-0012](0012-worker-en-red-bridge.md) (red bridge).
- **Fecha:** 2026-10-01

## Contexto
`worker/docker-compose.yml` era una copia del compose del master. Levantaba otro postgres, otro
redis, otro webserver y otro scheduler, y ningún `celery worker`. Además, `redis://redis` y
`@postgres` no resuelven desde otro servidor.

## Decisión
- El worker tiene un solo servicio, `airflow-worker`, que ejecuta
  `celery worker --queues ${WORKER_QUEUES} --concurrency ${WORKER_CONCURRENCY}`.
- Se conecta al broker y a la DB del master con `MASTER_HOST`.
- Usa `network_mode: host`. El worker se registra con el hostname real del servidor, y el
  webserver puede pedirle logs en el puerto 8793 sin mapear puertos ni depender de la IP interna
  del contenedor.
- La imagen se construye desde `../master` con el mismo Dockerfile. Puede construirse nativa en
  ARM o cargarse con `docker load` en servidores de la misma arquitectura.
- Oracle se separa en `docker-compose.oracle.yml`.

## Consecuencias
- El master debe poder **resolver el hostname** de cada worker (DNS o `/etc/hosts`) para mostrar
  logs en vivo. Los logs de tareas terminadas se leen del NFS de todos modos.
- Con red del host, el puerto 8793 queda expuesto en el servidor y debe restringirse al master
  en el firewall.
- Añadir un worker se reduce a clonar el repo, copiar el `.env` y ejecutar `docker compose up -d`.

## Alternativas consideradas
- **Red bridge con `hostname:` y `ports: 8793:8793`:** exige mantener a mano un hostname único por
  servidor y mapear puertos. No resuelve nada que la red del host no resuelva ya.
