# ADR-0005: Etiqueta SELinux compartida (`:z`) en volúmenes

- **Estado:** Aceptado
- **Fecha:** 2026-10-01

## Contexto
Los volúmenes usaban `:Z` (mayúscula), que reetiqueta el directorio con una etiqueta SELinux
**privada** de un solo contenedor. `dags`, `logs` y `plugins` los montan a la vez el webserver,
el scheduler, Flower e init. Con SELinux en *enforcing*, cada contenedor que arranca le quita el
acceso al anterior. En el entorno original SELinux está deshabilitado, por eso no fallaba.

## Decisión
Usar `:z` (minúscula, etiqueta compartida) en todos los volúmenes.

## Consecuencias
- No tiene efecto con SELinux deshabilitado y es correcto con SELinux en *enforcing*.
- Sobre NFS, el reetiquetado puede no estar soportado. Si `docker compose up` falla con
  `operation not supported`, hay que quitar `:z` de los montajes NFS y ejecutar
  `setsebool -P virt_use_nfs 1` en el host (ver [docs/nfs.md](../nfs.md)).

## Alternativas consideradas
- **Quitar el sufijo:** funciona sin SELinux, pero rompe a quien lo tenga activo.
