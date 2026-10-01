# ADR-0002: Oracle Instant Client con LD_LIBRARY_PATH en lugar de ldconfig

- **Estado:** Reemplazado por [ADR-0010](0010-sin-soporte-oracle.md)
- **Fecha:** 2026-10-01

## Contexto
El `entrypoint.sh` original escribía `/etc/ld.so.conf.d/oracle.conf` y ejecutaba `ldconfig`.
Los contenedores corren como `AIRFLOW_UID:0` (no-root), así que ambas operaciones fallaban por
permisos. La regla de sudoers era para el usuario `airflow` (UID 50000), así que no aplicaba a
otro UID, y el script tampoco usaba `sudo`. El fallo era silencioso, porque el script no tenía
`set -e`. Oracle funcionaba solo porque el worker además definía `LD_LIBRARY_PATH`.

## Decisión
- El entrypoint exporta `LD_LIBRARY_PATH` si existe `ORACLE_CLIENT_LIB_DIR`.
  Eso no requiere privilegios.
- El script usa `set -euo pipefail`.
- Se eliminan de la imagen `sudo` y la regla de sudoers.
- El montaje de Oracle pasa a un override opcional (`worker/docker-compose.oracle.yml`).

## Consecuencias
- Comportamiento correcto y explícito con cualquier UID.
- La imagen tiene menos superficie de ataque, porque ya no incluye `sudo`.
- Quien no usa Oracle no necesita montar nada.
- `libaio1` sigue en la imagen, porque Instant Client la necesita.

## Alternativas consideradas
- **Correr el entrypoint como root y bajar a usuario con `gosu`:** más complejo y contrario al
  diseño de la imagen oficial.
- **Copiar Instant Client dentro de la imagen y ejecutar `ldconfig` en el build:** acopla la
  imagen a la licencia y la versión de Oracle, y la hace más pesada para quien no lo usa.
