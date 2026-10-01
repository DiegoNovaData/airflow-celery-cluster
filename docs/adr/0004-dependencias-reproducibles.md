# ADR-0004: Dependencias Python reproducibles

- **Estado:** Aceptado
- **Fecha:** 2026-10-01

## Contexto
`requirements.txt` se instalaba sin restricciones y con `great-expectations>=1.0.0`. Dos builds en
fechas distintas podían producir imágenes diferentes, y pip podía actualizar o bajar paquetes de
los que depende Airflow, incluido el propio Airflow.

## Decisión
1. Todas las librerías propias van con versión exacta (`==`). Great Expectations queda en
   `1.23.2`, compatible con Python 3.12, pandas 2.1 y SQLAlchemy 1.4.
2. `requirements.txt` se instala junto con `apache-airflow==${AIRFLOW_VERSION}`, que es el patrón
   de la documentación oficial para extender la imagen. Así pip no puede cambiar la versión de
   Airflow.
3. Airflow y los providers se siguen instalando con el archivo de constraints oficial.

## Consecuencias
- Builds repetibles. Actualizar una librería es un cambio explícito y queda en el historial.
- Algunas librerías propias difieren de los constraints oficiales: `pyarrow` 17 frente a 16.1,
  `psycopg2-binary` 2.9.11 frente a 2.9.9 y `mysql-connector-python` 8.3 frente a 9.0. Se acepta
  porque no afectan al core de Airflow.
- Al subir de versión de Airflow, hay que revisar `SQLAlchemy==1.4.52`.

## Alternativas consideradas
- **Instalar `requirements.txt` con el `--constraint` oficial:** fallaría por los conflictos
  anteriores, porque las versiones fijadas difieren de las del archivo de constraints.
- **Lock file completo (`pip-compile`):** es lo más estricto. Queda como mejora futura.
