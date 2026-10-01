# Flower: monitoreo de Celery

Flower es el dashboard en vivo de Celery. Muestra qué workers están conectados, cuántas tareas
ejecuta cada uno y cuántos mensajes hay en cada cola. Corre en el master (servicio `flower` de
`master/docker-compose.yml`) con la misma imagen de Airflow (`airflow celery flower`), así que no
requiere instalación aparte.

## Acceso

- URL: `http://${MASTER_IP}:${FLOWER_PORT}` (default `5555`).
- Login: el valor de `FLOWER_BASIC_AUTH` en `master/.env`, con formato `usuario:clave`.
  Para varios usuarios, sepáralos con coma: `admin:clave1,ops:clave2`.

```
FLOWER_BASIC_AUTH=admin:una_clave_larga
```

Si `FLOWER_BASIC_AUTH` está vacío, Flower queda **sin login**. No lo dejes así: desde la UI se
puede apagar workers y cambiar su pool.

El login básico viaja sin cifrar sobre HTTP. Si Flower se accede fuera de una red de confianza,
ponlo detrás de un proxy con TLS (nginx o Traefik). Como mínimo, limita el puerto en el firewall:

```bash
sudo firewall-cmd --permanent --add-rich-rule="rule family=ipv4 source address=<red_admins>/24 port port=5555 protocol=tcp accept"
sudo firewall-cmd --reload
```

## Qué mirar

| Pestaña | Para qué |
|---|---|
| **Workers** | Cada worker aparece como `celery@<hostname>`. *Status* Online significa que está conectado al broker. Se ven las colas que atiende y su concurrencia. |
| **Tasks** | Historial de tareas Celery: recibidas, en ejecución, exitosas y fallidas, con el worker que las ejecutó. |
| **Broker** | Mensajes pendientes por cola. Si una cola crece y no baja, ningún worker la atiende. |

## Diagnóstico rápido

| Síntoma | Revisar |
|---|---|
| Un worker no aparece | `docker compose logs airflow-worker` en el worker. Valida `MASTER_IP`, `REDIS_PORT` y el firewall del 6379 (ver [redis.md](redis.md)). |
| Worker *Offline* después de reiniciar el master | Normal durante unos segundos: Celery se reconecta solo. |
| Tareas en `queued` en Airflow y la cola crece en Flower | No hay worker para esa cola (`WORKER_QUEUES`) o todos están llenos (`WORKER_CONCURRENCY`). |
| Tareas en `queued` en Airflow y la cola vacía en Flower | El límite está antes del broker: `AIRFLOW_PARALLELISM`, pools o `MAX_ACTIVE_TASKS_PER_DAG`. Ver el README. |

## API

Flower expone una API REST, útil para monitoreo externo:

```bash
curl -s -u "${FLOWER_BASIC_AUTH}" "http://${MASTER_IP}:${FLOWER_PORT}/api/workers" | python3 -m json.tool
```
