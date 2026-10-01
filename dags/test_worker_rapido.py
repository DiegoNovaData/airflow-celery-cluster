"""DAG de humo: valida que un worker toma tareas y que el NFS compartido funciona.

Imprime el hostname del worker que ejecutó la tarea y sobrescribe un archivo
en la carpeta de DAGs (compartida por NFS) con el timestamp de la corrida.
Para probar una cola específica, cambiar `queue` (ej. "pesado").
"""
from datetime import datetime

from airflow import DAG
from airflow.operators.bash import BashOperator

with DAG(
    dag_id="test_worker_rapido",
    start_date=datetime(2026, 1, 1),
    schedule=None,
    catchup=False,
    tags=["test", "infra"],
) as dag:
    verificar = BashOperator(
        task_id="verificar_worker",
        queue="default",
        bash_command=(
            "hostname && "
            "echo \"Última ejecución: $(date)\" > /opt/airflow/dags/ultimo_run.txt && "
            "cat /opt/airflow/dags/ultimo_run.txt"
        ),
    )
