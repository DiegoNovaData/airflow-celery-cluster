# ADR-0008: Toda la configuración variable en `.env`

- **Estado:** Aceptado
- **Fecha:** 2026-10-01

## Contexto
El repo debe servir a cualquier persona, no solo al entorno original. Había valores fijos en el
compose que cambian según el entorno: concurrencia, SMTP, rutas del host, puertos y nombre de
imagen. Otros eran incorrectos para un cluster: `PARALLELISM: 4` limitaba todo el cluster a 4
tareas simultáneas.

## Decisión
- Cada valor que depende del entorno se lee como `${VARIABLE:-default}` desde el `.env`. Los
  defaults son los de Airflow o los de la imagen oficial.
- Los secretos sin default razonable usan `${VARIABLE:?mensaje}`, así compose se niega a arrancar
  si faltan: `FERNET_KEY`, `SECRET_KEY`, credenciales de Postgres y del admin.
- Cada variable se documenta en el README ("Variables ajustables") con su archivo y su efecto.

## Consecuencias
- El `docker-compose.yml` es igual en todos los entornos. Solo cambia el `.env`, que no se versiona.
- El `.env.example` es la referencia completa de lo configurable.
- Los límites de recursos (`deploy.resources`) siguen fijos en el compose, porque cambian poco.

## Alternativas consideradas
- **Un `docker-compose.override.yml` por entorno:** útil para casos puntuales, como Oracle, pero
  dispersa la configuración si se usa para todo.
