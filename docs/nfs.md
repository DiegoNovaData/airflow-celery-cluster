# NFS: DAGs, logs y plugins compartidos

Todos los componentes de Airflow (scheduler, webserver y cada worker) deben ver **la misma copia**
de `dags/`, `logs/` y `plugins/`. El master exporta esas tres carpetas por NFS y cada worker las
monta en la misma ruta.

```
master  ${AIRFLOW_DATA_DIR}/dags     ──NFS──►  worker  ${AIRFLOW_DATA_DIR}/dags
        ${AIRFLOW_DATA_DIR}/logs     ──NFS──►          ${AIRFLOW_DATA_DIR}/logs
        ${AIRFLOW_DATA_DIR}/plugins  ──NFS──►          ${AIRFLOW_DATA_DIR}/plugins
        ${AIRFLOW_DATA_DIR}/postgres   (local, NUNCA por NFS)
        ${AIRFLOW_DATA_DIR}/ssh        (local en cada servidor)
```

Todos los comandos toman las rutas, el UID y las IPs del `.env` del repo, así que no hay que
escribir IPs a mano. Antes de ejecutarlos, carga el `.env` en la shell:

```bash
cd airflow-celery-cluster/master     # en un worker: cd airflow-celery-cluster/worker
set -a; source .env; set +a
```

| Variable | Archivo | Uso aquí |
|---|---|---|
| `AIRFLOW_DATA_DIR` | master y worker | Carpeta base (la misma ruta en todos los servidores) |
| `AIRFLOW_UID` | master y worker | Dueño de las carpetas compartidas |
| `WORKER_IPS` | `master/.env` | Clientes autorizados en el export y en el firewall |
| `MASTER_IP` | `worker/.env` | Servidor NFS al que se conecta el worker |

Los comandos son para CentOS/RHEL 8+. En CentOS 7, usa `yum` en lugar de `dnf`.

## 1. Servidor NFS (master)

```bash
sudo dnf install -y nfs-utils

# Carpetas y dueño: el MISMO UID que usan los contenedores en todos los servidores
sudo mkdir -p "${AIRFLOW_DATA_DIR}"/{dags,logs,plugins}
sudo chown -R "${AIRFLOW_UID}:0" "${AIRFLOW_DATA_DIR}"/{dags,logs,plugins}
sudo chmod -R 775 "${AIRFLOW_DATA_DIR}"/{dags,logs,plugins}
```

Genera `/etc/exports.d/airflow.exports`, con una línea por carpeta y un cliente por cada IP
de `WORKER_IPS`:

```bash
for d in dags logs plugins; do
  line="${AIRFLOW_DATA_DIR}/$d"
  for ip in ${WORKER_IPS//,/ }; do
    line+=" ${ip}(rw,sync,no_subtree_check,root_squash)"
  done
  echo "$line"
done | sudo tee /etc/exports.d/airflow.exports
```

Si agregas un worker, añade su IP a `WORKER_IPS` y vuelve a ejecutar este bloque y el del firewall.

| Opción | Por qué |
|---|---|
| `rw` | Los workers escriben logs y el DAG de prueba escribe en `dags/`. |
| `sync` | Confirma cada escritura en disco antes de responder. Es más lento, pero los logs no se pierden si el master se cae. |
| `no_subtree_check` | Evita errores cuando se renombran archivos dentro del export. |
| `root_squash` | Un root remoto se mapea a `nobody`. Los contenedores no corren como root, así que no afecta a Airflow. |

Activa el servicio y publica los exports:

```bash
sudo systemctl enable --now rpcbind nfs-server
sudo exportfs -rav
sudo exportfs -v          # verificar
```

Abre el firewall solo a los workers:

```bash
for ip in ${WORKER_IPS//,/ }; do
  for svc in nfs mountd rpc-bind; do
    sudo firewall-cmd --permanent --add-rich-rule="rule family=ipv4 source address=$ip service name=$svc accept"
  done
done
sudo firewall-cmd --reload
```

## 2. Cliente NFS (cada worker)

```bash
sudo dnf install -y nfs-utils
sudo mkdir -p "${AIRFLOW_DATA_DIR}"/{dags,logs,plugins,ssh}
sudo chown "${AIRFLOW_UID}:0" "${AIRFLOW_DATA_DIR}/ssh"

showmount -e "${MASTER_IP}"   # debe listar las tres carpetas
```

Añade los montajes a `/etc/fstab` para que se mantengan tras reiniciar:

```bash
for d in dags logs plugins; do
  echo "${MASTER_IP}:${AIRFLOW_DATA_DIR}/$d  ${AIRFLOW_DATA_DIR}/$d  nfs  defaults,_netdev,hard,timeo=600,retrans=2  0 0"
done | sudo tee -a /etc/fstab
```

```bash
sudo systemctl daemon-reload
sudo mount -a
df -h | grep airflow      # deben aparecer los tres montajes
```

- `_netdev` espera a que haya red antes de montar.
- `hard` hace que una escritura se reintente si el master no responde, en lugar de devolver
  error y corromper un log.

### Que Docker no arranque antes que NFS

Si Docker arranca antes de que NFS monte, el worker escribe en la carpeta **local vacía**, y los
DAGs "desaparecen". Para evitarlo, obliga a Docker a esperar los montajes:

```bash
sudo mkdir -p /etc/systemd/system/docker.service.d
printf '[Unit]\nAfter=remote-fs.target\nRequiresMountsFor=%s/dags %s/logs %s/plugins\n' \
  "${AIRFLOW_DATA_DIR}" "${AIRFLOW_DATA_DIR}" "${AIRFLOW_DATA_DIR}" \
  | sudo tee /etc/systemd/system/docker.service.d/nfs-mounts.conf
sudo systemctl daemon-reload
```

## 3. Verificación

```bash
# en el worker
touch "${AIRFLOW_DATA_DIR}/logs/prueba_$(hostname)"
# en el master
ls -ln "${AIRFLOW_DATA_DIR}/logs/" | grep prueba    # debe verse el archivo
```

La prueba completa es el DAG `test_worker_rapido`. Ver el [README](../README.md#3-probar-con-el-dag-de-humo).

## Problemas comunes

| Síntoma | Causa probable | Solución |
|---|---|---|
| `Permission denied` al escribir logs | El UID del contenedor no es dueño de la carpeta, o difiere entre servidores | Usa el mismo `AIRFLOW_UID` en todos los `.env` y ejecuta `chown` en el master. |
| Archivos con dueño `nobody` | El contenedor corre como root, o falla el `idmapd` de NFSv4 | Verifica `user:` en el compose. Si hace falta, usa el mismo dominio en `/etc/idmapd.conf` en ambos lados. |
| `operation not supported` al levantar compose | `:z` intenta reetiquetar SELinux sobre NFS | Quita `:z` de los montajes NFS y ejecuta `sudo setsebool -P virt_use_nfs 1`. Ver [ADR-0005](adr/0005-etiqueta-selinux-compartida.md). |
| Los DAGs nuevos tardan en aparecer | Caché de atributos de NFS más `AIRFLOW_MIN_FILE_PROCESS_INTERVAL` | Es normal. Para acelerar, añade `actimeo=10` al montaje de `dags`. |
