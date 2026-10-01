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

Los ejemplos usan:

- `AIRFLOW_DATA_DIR=/app/dockerdata/airflow`
- `AIRFLOW_UID=50000`
- master `192.0.2.10`
- workers `192.0.2.41` y `192.0.2.42`

Reemplaza estos valores por los tuyos. Los comandos son para CentOS/RHEL 8+; en CentOS 7, usa `yum`
en lugar de `dnf`.

## 1. Servidor NFS (master)

```bash
sudo dnf install -y nfs-utils

# Carpetas y dueño: el MISMO UID que usan los contenedores en todos los servidores
sudo mkdir -p /app/dockerdata/airflow/{dags,logs,plugins}
sudo chown -R 50000:0 /app/dockerdata/airflow/{dags,logs,plugins}
sudo chmod -R 775 /app/dockerdata/airflow/{dags,logs,plugins}
```

Edita `/etc/exports` con una línea por carpeta y por worker, o usa una subred:

```
/app/dockerdata/airflow/dags     192.0.2.41(rw,sync,no_subtree_check,root_squash) 192.0.2.42(rw,sync,no_subtree_check,root_squash)
/app/dockerdata/airflow/logs     192.0.2.41(rw,sync,no_subtree_check,root_squash) 192.0.2.42(rw,sync,no_subtree_check,root_squash)
/app/dockerdata/airflow/plugins  192.0.2.41(rw,sync,no_subtree_check,root_squash) 192.0.2.42(rw,sync,no_subtree_check,root_squash)
```

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
for ip in 192.0.2.41 192.0.2.42; do
  for svc in nfs mountd rpc-bind; do
    sudo firewall-cmd --permanent --add-rich-rule="rule family=ipv4 source address=$ip service name=$svc accept"
  done
done
sudo firewall-cmd --reload
```

## 2. Cliente NFS (cada worker)

```bash
sudo dnf install -y nfs-utils
sudo mkdir -p /app/dockerdata/airflow/{dags,logs,plugins,ssh}
sudo chown 50000:0 /app/dockerdata/airflow/ssh

showmount -e 192.0.2.10   # debe listar las tres carpetas
```

Añade los montajes a `/etc/fstab` para que se mantengan tras reiniciar:

```
192.0.2.10:/app/dockerdata/airflow/dags     /app/dockerdata/airflow/dags     nfs  defaults,_netdev,hard,timeo=600,retrans=2  0 0
192.0.2.10:/app/dockerdata/airflow/logs     /app/dockerdata/airflow/logs     nfs  defaults,_netdev,hard,timeo=600,retrans=2  0 0
192.0.2.10:/app/dockerdata/airflow/plugins  /app/dockerdata/airflow/plugins  nfs  defaults,_netdev,hard,timeo=600,retrans=2  0 0
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
sudo systemctl edit docker
```

```ini
[Unit]
After=remote-fs.target
RequiresMountsFor=/app/dockerdata/airflow/dags /app/dockerdata/airflow/logs /app/dockerdata/airflow/plugins
```

## 3. Verificación

```bash
# en el worker
touch /app/dockerdata/airflow/logs/prueba_$(hostname)
# en el master
ls -ln /app/dockerdata/airflow/logs/ | grep prueba    # debe verse el archivo
```

La prueba completa es el DAG `test_worker_rapido`. Ver el [README](../README.md#3-probar-con-el-dag-de-humo).

## Problemas comunes

| Síntoma | Causa probable | Solución |
|---|---|---|
| `Permission denied` al escribir logs | El UID del contenedor no es dueño de la carpeta, o difiere entre servidores | Usa el mismo `AIRFLOW_UID` en todos los `.env` y ejecuta `chown` en el master. |
| Archivos con dueño `nobody` | El contenedor corre como root, o falla el `idmapd` de NFSv4 | Verifica `user:` en el compose. Si hace falta, usa el mismo dominio en `/etc/idmapd.conf` en ambos lados. |
| `operation not supported` al levantar compose | `:z` intenta reetiquetar SELinux sobre NFS | Quita `:z` de los montajes NFS y ejecuta `sudo setsebool -P virt_use_nfs 1`. Ver [ADR-0005](adr/0005-etiqueta-selinux-compartida.md). |
| Los DAGs nuevos tardan en aparecer | Caché de atributos de NFS más `AIRFLOW_MIN_FILE_PROCESS_INTERVAL` | Es normal. Para acelerar, añade `actimeo=10` al montaje de `dags`. |
