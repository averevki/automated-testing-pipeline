"""Pipeline main dag and entrypoint"""
import sys
from datetime import datetime
from pathlib import Path

from airflow.models import Variable
from airflow.decorators import dag, task_group
from airflow.utils.trigger_rule import TriggerRule

sys.path.append(str(Path(__file__).parents[2]))
from pipeline.config import settings


# change environment variable and trigger through terminal
# export AIRFLOW_VAR_ENV_FOR_DYNACONF=diff
# airflow dags trigger 3scale-pipeline
settings.setenv(Variable.get("ENV_FOR_DYNACONF", "default"))

default_args = {
    "owner": "Aleksandr Verevkin"
}


@dag(dag_id="pipeline-dag",
     default_args=default_args,
     description="Cluster/product/tests automatic pipeline",
     start_date=datetime(2021, 7, 29, 2),
     max_active_runs=1,
     schedule=None)
def main_dag():
    """Main dag pipeline"""
    import pipeline.utils as utils
    from pipeline.utils.builders import build_bash_task

    setup_t = build_bash_task(
        task_id="submodules-init",
        bash_command="git submodule update --init --recursive --remote --merge",
        cwd=f"{utils.ROOT}"
    )

    @task_group(group_id=utils.MAIN_PIPELINE_NAME)
    def main_pipeline():
        """Main pipeline task group"""
        from pipeline.tasks.tasks.tasks import task_from_module
        from pipeline.tasks.tasks.tests import build_tests_task
        from pipeline.utils.utils import connect_tasks

        pipeline_tasks = []
        # create tasks from existing modules
        for module in settings.modules:
            module_tg = task_from_module(module)
            pipeline_tasks.append(module_tg())
        # set tests tasks
        tests_group = build_tests_task()
        pipeline_tasks.append(tests_group())
        # create single tasks pipeline
        connect_tasks(pipeline_tasks)

    setup_t >> main_pipeline()


main_dag()
