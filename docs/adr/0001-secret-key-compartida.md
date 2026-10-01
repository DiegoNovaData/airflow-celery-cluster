# ADR-0001: Secret key del webserver compartida en todo el cluster

- **Estado:** Aceptado
- **Fecha:** 2026-10-01

## Contexto
Cuando una tarea está en ejecución, el webserver pide su log al *log server* del worker
(puerto 8793). Esa petición va firmada con `[webserver] secret_key`, y el worker la valida con
su propia clave. La configuración original no la definía, así que cada contenedor generaba una
aleatoria. Las firmas no coincidían y los logs en vivo respondían `403 Forbidden`. Con NFS no se
nota en tareas terminadas, porque su log se lee del archivo compartido.

## Decisión
Definir `AIRFLOW__WEBSERVER__SECRET_KEY` desde la variable obligatoria `AIRFLOW_SECRET_KEY`,
con el mismo valor en el `.env` del master y de cada worker.

## Consecuencias
- Los logs en vivo funcionan desde la UI.
- La clave estable evita que las sesiones de la UI se invaliden al reiniciar el webserver.
- Es un secreto más que hay que distribuir a cada worker, igual que `FERNET_KEY`.
- Si la clave se rota, hay que cambiarla en todos los servidores a la vez.

## Alternativas consideradas
- **Depender solo de NFS para los logs:** no cubre las tareas en curso.
- **Logging remoto (S3/GCS/Elasticsearch):** innecesario on-prem con NFS disponible.
