# ADR-0009: Redis sin contraseña por defecto, protegido por firewall

- **Estado:** Aceptado (revisable)
- **Fecha:** 2026-10-01

## Contexto
Redis publica el puerto 6379 para que los workers de otros servidores lleguen al broker, y no
tiene autenticación. Cualquier host con acceso de red podría leer o inyectar mensajes en la cola.

## Decisión
Por ahora se mantiene sin contraseña, para no cambiar el comportamiento de la línea base. La
mitigación **obligatoria** es restringir el 6379 a las IPs de los workers en el firewall del
master. El procedimiento para activar `requirepass` está en [docs/redis.md](../redis.md).

## Consecuencias
- La seguridad del broker depende de la red y del firewall.
- Activar la contraseña más adelante obliga a cambiar el `BROKER_URL` en master y workers a la vez.

## Alternativas consideradas
- **`requirepass` desde la v1.0.0:** es lo recomendado. Se pospuso a una versión posterior.
- **Redis con TLS:** excesivo para una red interna.
