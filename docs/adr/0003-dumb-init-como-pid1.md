# ADR-0003: Mantener dumb-init como PID 1

- **Estado:** Aceptado
- **Fecha:** 2026-10-01

## Contexto
La imagen oficial usa `ENTRYPOINT ["/usr/bin/dumb-init", "--", "/entrypoint"]`. El Dockerfile
original lo reemplazaba por `["/custom-entrypoint.sh"]` y perdía `dumb-init`. Sin un init real
como PID 1, las señales (el SIGTERM de `docker stop`) no se reenvían bien y los procesos zombie
no se recogen. En un worker Celery eso significa cortes bruscos de tareas al reiniciar.

## Decisión
`ENTRYPOINT ["/usr/bin/dumb-init", "--", "/custom-entrypoint.sh"]`. El script propio termina con
`exec /entrypoint "$@"`. En el worker se define `DUMB_INIT_SETSID=0`, como recomienda Airflow,
para que Celery reciba la señal y haga *warm shutdown*: termina las tareas en curso antes de salir.

## Consecuencias
- Paradas limpias y sin zombies.
- El comportamiento es igual al de la imagen oficial, así que la documentación de Airflow aplica
  tal cual.

## Alternativas consideradas
- **`init: true` en compose (tini):** funciona, pero duplica un init que la imagen ya trae y es
  fácil olvidarlo en un servicio.
