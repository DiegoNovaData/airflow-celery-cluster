# ADR-0011: IPs del cluster en `.env` y worker anunciado por IP

- **Estado:** Aceptado
- **Fecha:** 2026-10-01
- **Modifica a:** [ADR-0007](0007-worker-celery-dedicado.md)

## Contexto
- Las IPs del master y de los workers solo aparecían como ejemplos en la documentación, y había
  que reemplazarlas a mano en cada comando de firewall y NFS.
- El master publicaba sus puertos en todas las interfaces (`0.0.0.0`). Docker los publica con
  reglas propias de iptables, que pueden saltarse firewalld.
- Para ver los logs en vivo, el master tenía que **resolver el hostname** de cada worker por DNS
  o `/etc/hosts` (consecuencia de ADR-0007).

## Decisión
- **`master/.env`:**
  - `MASTER_IP`: los puertos 8080, 5555, 6379 y 5432 se publican solo en esa IP.
  - `WORKER_IPS`: lista de workers separada por comas.
- **`worker/.env`:**
  - `MASTER_IP`: dirección de Redis y PostgreSQL. Reemplaza a `MASTER_HOST`.
  - `WORKER_IP`: IP del propio worker.
- **Hostname de las tareas:** el worker define
  `AIRFLOW__CORE__HOSTNAME_CALLABLE=cluster_hostname.get_hostname` y
  `AIRFLOW_ADVERTISED_HOST=${WORKER_IP}`. El módulo `master/cluster_hostname.py` se copia en la
  imagen, en `$AIRFLOW_HOME/config`, que está en el `sys.path` de Airflow. Con esto, cada tarea
  queda registrada con la IP del worker y el webserver pide los logs a `http://WORKER_IP:8793`.
  Si la variable no existe, por ejemplo en el master, el módulo devuelve el FQDN de siempre.
- **Documentación:** los comandos de firewall y NFS cargan el `.env`
  (`set -a; source .env; set +a`) y recorren `WORKER_IPS`, en lugar de usar IPs escritas a mano.

## Consecuencias
- Agregar un worker es: añadir su IP a `WORKER_IPS` en el master, volver a ejecutar los bloques
  de NFS y firewall, y crear el `worker/.env` con su `WORKER_IP`.
- Ya no se necesita DNS ni `/etc/hosts` entre servidores.
- `MASTER_IP` es obligatoria en master y worker: compose falla si falta.
- Con los puertos publicados solo en `MASTER_IP`, no se accede por `127.0.0.1` desde el propio
  master. Hay que usar `MASTER_IP`.
- El `.env` puede referenciar otras variables, por ejemplo
  `AIRFLOW_BASE_URL=http://${MASTER_IP}:${AIRFLOW_WEBSERVER_PORT}`. Docker Compose v2 y bash las
  expanden igual.

## Alternativas consideradas
- **`extra_hosts` en el master con pares `hostname:IP` de cada worker:** obliga a editar el
  compose por cada worker nuevo, y compose no admite listas variables.
- **`airflow.utils.net.get_host_ip_address`:** depende de cómo resuelva cada servidor su propio
  hostname, y puede devolver `127.0.0.1`.
