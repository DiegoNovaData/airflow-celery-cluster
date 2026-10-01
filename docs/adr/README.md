# Architecture Decision Records

Cada ADR registra una decisión: el contexto, lo que se decidió y sus consecuencias.
Si una decisión cambia, no se edita el ADR: se crea uno nuevo que lo reemplaza
(estado "Reemplazado por ADR-XXXX").

| ADR | Título | Estado |
|---|---|---|
| [0001](0001-secret-key-compartida.md) | Secret key del webserver compartida en todo el cluster | Aceptado |
| [0002](0002-oracle-sin-ldconfig.md) | Oracle Instant Client con LD_LIBRARY_PATH en lugar de ldconfig | Reemplazado por 0010 |
| [0003](0003-dumb-init-como-pid1.md) | Mantener dumb-init como PID 1 | Reemplazado por 0010 |
| [0004](0004-dependencias-reproducibles.md) | Dependencias Python reproducibles | Aceptado |
| [0005](0005-etiqueta-selinux-compartida.md) | Etiqueta SELinux compartida (`:z`) en volúmenes | Aceptado |
| [0006](0006-airflow-init-como-compuerta.md) | `airflow-init` como compuerta de arranque | Aceptado |
| [0007](0007-worker-celery-dedicado.md) | Worker Celery dedicado con red del host | Aceptado (modificado por 0010, 0011) |
| [0008](0008-configuracion-por-env.md) | Toda la configuración variable en `.env` | Aceptado |
| [0009](0009-redis-sin-password-por-defecto.md) | Redis sin contraseña por defecto, protegido por firewall | Aceptado (revisable) |
| [0010](0010-sin-soporte-oracle.md) | Eliminar el soporte de Oracle Instant Client | Aceptado |
| [0011](0011-ips-del-cluster-en-env.md) | IPs del cluster en `.env` y worker anunciado por IP | Aceptado |

Plantilla: [0000-plantilla.md](0000-plantilla.md)
