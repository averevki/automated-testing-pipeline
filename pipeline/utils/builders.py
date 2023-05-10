"""Module with tasks building utilities"""
from typing import Optional, Callable, Collection, Any, Iterable

from airflow.operators.python import PythonOperator, BranchPythonOperator
from airflow.operators.bash import BashOperator
from airflow.operators.email import EmailOperator
from airflow.operators.empty import EmptyOperator
from airflow.providers.jenkins.operators.jenkins_job_trigger import JenkinsJobTriggerOperator
from airflow.models.connection import Connection
from airflow.utils.trigger_rule import TriggerRule


def build_bash_task(task_id: str, bash_command: str, cwd: str = None,
                    env: Optional[dict] = None, trigger_rule: TriggerRule = TriggerRule.ALL_SUCCESS) -> BashOperator:
    """BashOperator builder"""
    return BashOperator(
        task_id=task_id,
        bash_command=bash_command,
        cwd=cwd,
        env=env,
        append_env=True,
        trigger_rule=trigger_rule
    )


def build_python_task(task_id: str, callable_: Callable,
                      op_args: Optional[Collection] = None,
                      op_kwargs: Optional[dict[str, Any]] = None,
                      trigger_rule: TriggerRule = TriggerRule.ALL_SUCCESS) -> PythonOperator:
    """PythonOperator builder"""
    return PythonOperator(
        task_id=task_id,
        python_callable=callable_,
        op_args=op_args,
        op_kwargs=op_kwargs,
        trigger_rule=trigger_rule
    )


def build_jenkins_task(task_id: str, job_name: str, jenkins_connection_id: str,
                       params: Optional[dict] = None, trigger_rule: TriggerRule = TriggerRule.ALL_SUCCESS,
                       allowed_jenkins_states: Optional[Iterable] = None) -> JenkinsJobTriggerOperator:
    """JenkinsJobTriggerOperator builder"""
    if allowed_jenkins_states is None:
        allowed_jenkins_states = ["SUCCESS", "UNSTABLE", "FAILURE", "NOT_BUILT", "ABORTED"]
    return JenkinsJobTriggerOperator(
        task_id=task_id,
        job_name=job_name,
        parameters=params,
        jenkins_connection_id=jenkins_connection_id,
        trigger_rule=trigger_rule,
        allowed_jenkins_states=allowed_jenkins_states
    )


def build_branch_python_task(task_id: str, callable_: Callable,
                             op_args: Optional[Collection] = None,
                             op_kwargs: Optional[dict[str, Any]] = None,
                             trigger_rule: TriggerRule = TriggerRule.ALL_SUCCESS) -> BranchPythonOperator:
    """BranchPythonOperator builder"""
    return BranchPythonOperator(
        task_id=task_id,
        python_callable=callable_,
        op_args=op_args,
        op_kwargs=op_kwargs,
        trigger_rule=trigger_rule
    )


def build_results_email_content(result: str, url: str, duration: str, started_by: str, artifacts: list[str]) -> str:
    """Build email content for the jenkins job result"""
    artifacts_anchors = [f"<a href='{a}'>{a}</a>" for a in artifacts]
    return f"Result: {result}<br>" \
           f"Build URL: {url}<br>" \
           f"Build duration: {duration}<br>" \
           f"Started by: {started_by}<br>" \
           f"Build artifacts: <br>&emsp;{'<br>&emsp;'.join(artifacts_anchors)}"


def build_email_task(task_id: str, to: str, subject: str, html_content: str, conn_id: str = None,
                     trigger_rule: TriggerRule = TriggerRule.ALL_SUCCESS) -> EmailOperator:
    """EmailOperator builder"""
    return EmailOperator(
        task_id=task_id,
        to=to,
        subject=subject,
        html_content=html_content,
        trigger_rule=trigger_rule,
        conn_id=conn_id
    )


def build_empty_task(task_id: str, trigger_rule: TriggerRule = TriggerRule.ALL_SUCCESS) -> EmptyOperator:
    """EmptyOperator builder"""
    return EmptyOperator(task_id=task_id, trigger_rule=trigger_rule)


def build_connection(conn_id: str, login: str = None, password: str = None, host: str = None,
                     conn_type: str = None, port: Optional[int] = None, uri: str = None) -> Connection:
    """Connection builder"""
    if uri:
        return Connection(uri=uri)

    return Connection(conn_id=conn_id,
                      login=login, password=password,
                      host=host, conn_type=conn_type, port=port)
