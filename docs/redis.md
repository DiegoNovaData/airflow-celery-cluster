# Redis: broker de Celery

Redis es la cola de mensajes del cluster. El scheduler publica cada tarea lista en una cola
(`default`, `pesado`, …) y cada worker toma las tareas de las colas que atiende
(`WORKER_QUEUES`). Redis **no guarda el estado** de las tareas: eso vive en PostgreSQL.

Corre como contenedor en el master (servicio `redis` de `master/docker-compose.yml`), así que no
hay que instalar nada en el sistema operativo.

## Configuración actual

| Aspecto | Valor | Dónde |
|---|---|---|
| Imagen | `REDIS_IMAGE` (default `redis:7`) | `master/.env` |
| Puerto publicado | `REDIS_PORT` (default `6379`) | `master/.env` |
| URL en el master | `redis://redis:6379/0` (red interna de compose) | `master/docker-compose.yml` |
| URL en los workers | `redis://${MASTER_IP}:${REDIS_PORT}/0` | `worker/docker-compose.yml` |
| IP publicada | `MASTER_IP` (el puerto no escucha en otras interfaces) | `master/.env` |
| Autenticación | Ninguna. Ver [ADR-0009](adr/0009-redis-sin-password-por-defecto.md) | — |
| Persistencia | Ninguna (solo en memoria) | — |

## Ajustes del host (master)

Redis advierte en su log si el kernel no permite *overcommit* de memoria:

```bash
echo 'vm.overcommit_memory = 1' | sudo tee /etc/sysctl.d/99-redis.conf
sudo sysctl --system
```

## Firewall: obligatorio

Como no hay contraseña, el puerto 6379 debe quedar abierto **solo a los workers**. Las IPs se
toman de `WORKER_IPS` en `master/.env`:

```bash
cd airflow-celery-cluster/master
set -a; source .env; set +a
for ip in ${WORKER_IPS//,/ }; do
  sudo firewall-cmd --permanent --add-rich-rule="rule family=ipv4 source address=$ip port port=${REDIS_PORT} protocol=tcp accept"
done
sudo firewall-cmd --reload
```

Docker publica los puertos con sus propias reglas de iptables, que pueden saltarse firewalld.
Por eso el compose publica Redis solo en `MASTER_IP` (`"${MASTER_IP}:6379:6379"`) y no en todas
las interfaces. Para filtrar por IP de origen a nivel de Docker, usa la cadena `DOCKER-USER`.

## Persistencia (opcional)

Sin persistencia, si Redis se reinicia se pierden los mensajes que estaban en cola. Las tareas en
ejecución no se pierden, porque su estado está en PostgreSQL. Airflow se recupera solo: el
scheduler reencola las tareas que quedan en `queued` más de `[scheduler] task_queued_timeout`
(600 s por defecto).

Si prefieres no esperar ese tiempo, activa AOF en el servicio `redis`:

```yaml
  redis:
    image: ${REDIS_IMAGE:-redis:7}
    command: ["redis-server", "--appendonly", "yes"]
    volumes:
      - ${AIRFLOW_DATA_DIR:-/app/dockerdata/airflow}/redis:/data:z
```

## Activar contraseña (recomendado)

1. Añade `REDIS_PASSWORD=<clave>` al `.env` del master y de **todos** los workers. Usa solo letras
   y números, o codifica la clave para URL.
2. En `master/docker-compose.yml`:

   ```yaml
     redis:
       command: ["redis-server", "--requirepass", "${REDIS_PASSWORD}"]
       healthcheck:
         test: ["CMD-SHELL", "redis-cli -a \"$${REDIS_PASSWORD}\" ping | grep PONG"]
       environment:
         REDIS_PASSWORD: ${REDIS_PASSWORD}
   ```

   Y en `x-airflow-common`:

   ```yaml
       AIRFLOW__CELERY__BROKER_URL: redis://:${REDIS_PASSWORD}@redis:6379/0
   ```

3. En `worker/docker-compose.yml`:

   ```yaml
         AIRFLOW__CELERY__BROKER_URL: redis://:${REDIS_PASSWORD}@${MASTER_IP}:${REDIS_PORT:-6379}/0
   ```

4. Reinicia el master y luego cada worker: `docker compose up -d`.
5. Registra el cambio con un ADR nuevo que reemplace al ADR-0009.

## Verificación

```bash
# en el master
docker compose exec redis redis-cli ping                # PONG
docker compose exec redis redis-cli LLEN default        # tareas esperando en la cola "default"

# desde un worker: valida red y firewall (con worker/.env cargado)
docker run --rm redis:7 redis-cli -h "${MASTER_IP}" -p "${REDIS_PORT}" ping   # PONG
```

Si `LLEN` crece sin parar, ningún worker está atendiendo esa cola. Revisa `WORKER_QUEUES` y Flower.
