# ADR-0010: Eliminar el soporte de Oracle Instant Client

- **Estado:** Aceptado
- **Fecha:** 2026-10-01
- **Reemplaza a:** [ADR-0002](0002-oracle-sin-ldconfig.md), [ADR-0003](0003-dumb-init-como-pid1.md)

## Contexto
Oracle Instant Client era una necesidad del entorno original. El repo busca ser una receta
genérica de Airflow distribuido, y Oracle añadía piezas que la mayoría de usuarios no necesita:

- `libaio1` en la imagen.
- Un `entrypoint.sh` propio que reemplazaba al oficial.
- Un override de compose con montajes de `/usr/lib/oracle` y `/opt/oracle`.
- Variables `ORACLE_*` y `TNS_ADMIN`.

## Decisión
Quitar todo lo relacionado con Oracle:

- **Imagen:** sin `libaio1` y sin `entrypoint.sh`. Se usa el `ENTRYPOINT` oficial, que es
  `dumb-init` + `/entrypoint`.
- **Worker:** se borra `worker/docker-compose.oracle.yml`.
- **Configuración:** se eliminan las variables `ORACLE_*` de `worker/.env.example`.

## Consecuencias
- La imagen es más simple y se comporta igual que la oficial. Ya no hay que mantener un
  entrypoint propio.
- El problema de `ldconfig` (ADR-0002) y el de `dumb-init` (ADR-0003) desaparecen: ya no existe
  el entrypoint que los causaba. `DUMB_INIT_SETSID=0` se mantiene en el worker.
- Quien necesite Oracle debe extender la imagen. Por ejemplo, con un `Dockerfile` propio
  `FROM <esta imagen>` que instale `libaio1` y el Instant Client, y que defina `LD_LIBRARY_PATH`.
  La versión 1.0.0 del repo tiene la implementación anterior como referencia.

## Alternativas consideradas
- **Mantenerlo como override opcional:** ya lo era, pero igual obligaba a tener un entrypoint
  propio y `libaio1` en la imagen para todos.
