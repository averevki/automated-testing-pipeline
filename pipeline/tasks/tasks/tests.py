"""Module resolving test tasks, including branching and reporting"""
import logging
from datetime import datetime
from typing import Callable

from airflow.decorators import task_group
from airflow.utils.trigger_rule import TriggerRule
from airflow.exceptions import AirflowSkipException

import pipeline.utils as utils
from pipeline.utils.builders import (
    build_jenkins_task, build_python_task, build_branch_python_task,
    build_empty_task, build_email_task, build_results_email_content
)
from pipeline.connections.jenkins_connection import JenkinsConnection
from pipeline.connections.smtp_connection import SMTPConnection


def manage_tests_task():
    """Branching task, deciding if tests should be run"""
    if utils.RUN_TESTS:
        logging.info(f"Tests are NOT skipped (tests.run_tests: {utils.RUN_TESTS})")
        return utils.TESTS_RUN_TASK_ID
    logging.info(f"Tests are skipped (tests.run_tests: {utils.RUN_TESTS})")
    return utils.TESTS_END_TASK_ID


def jenkins_task(ti):
    """Main tests task, which will execute Jenkins job"""
    if not utils.JENKINS_JOB_NAME:
        raise RuntimeError("Jenkins job name isn't configured.")

    # merge cluster context and defined Jenkins parameters
    cluster_context = ti.xcom_pull(task_ids=utils.CLUSTER_MANAGEMENT_END_TASK_ID)
    if cluster_context is None:
        # if cluster context is not defined, run tests on the predeclared context
        if not utils.CLUSTER_URL:
            raise RuntimeError("Neither the cluster-management module nor the cluster URL is defined."
                               "Unable to run a parametrized tests.")
        cluster_context = {"api_url": utils.CLUSTER_URL, "namespace": utils.CLUSTER_NAMESPACE}

    params = {**utils.JENKINS_JOB_PARAMS}
    # set cluster and namespace context parameters
    if utils.JENKINS_CLUSTER_PARAM:
        params.update({utils.JENKINS_CLUSTER_PARAM: cluster_context["api_url"]})
    if utils.JENKINS_NAMESPACE_PARAM:
        params.update({utils.JENKINS_NAMESPACE_PARAM: cluster_context["namespace"]})

    jenkins_hook = JenkinsConnection().get_jenkins_hook()
    logging.info(f"Jenkins connection successful. Running job: {utils.JENKINS_JOB_NAME}, with parameters: {params}")
    build_jenkins_task("run_jenkins", utils.JENKINS_JOB_NAME,
                       jenkins_hook.connection.conn_id, params=params).execute({})


def fetch_jenkins_build() -> dict:
    """Get the latest build info from defined Jenkins job"""
    hook = JenkinsConnection().get_jenkins_hook()
    latest_build = hook.get_latest_build_number(utils.JENKINS_JOB_NAME)
    build_info = hook.jenkins_server.get_build_info(utils.JENKINS_JOB_NAME, latest_build)

    return build_info


def email_tests_results():
    """Fetch information about Jenkins job built and send email with results"""
    if not utils.SEND_REPORT:
        raise AirflowSkipException(f"Tests reporting is skipped (send_report: {utils.SEND_REPORT})")
    if not utils.REPORT_EMAIL:
        raise AirflowSkipException(f"Tests reporting is skipped (email_address is not configured)")

    results = fetch_jenkins_build()
    logging.info(f"Last build results: {results}")

    email_content = build_results_email_content(
        results["result"],
        results["url"],
        f"{results['duration']}s",
        next((item["causes"][0]["userName"] for item in results["actions"] if "causes" in item), None),
        [results["url"] + "artifact/" + a["relativePath"] for a in results["artifacts"] if ".html" in a["fileName"]]
    )

    tests_start_time = datetime.fromtimestamp(results["timestamp"] / 1000).strftime("%Y-%m-%d %H:%M:%S")
    email_subject = f"Tests results - {tests_start_time}"

    conn_id = SMTPConnection().get_connection_id()
    build_email_task("email-tests-results", utils.REPORT_EMAIL, email_subject, email_content, conn_id).execute({})


def build_tests_task() -> Callable:
    """Create task group with test execution"""
    @task_group(group_id=utils.TEST_GROUP_NAME)
    def create_tests_group():
        from pipeline.utils.utils import connect_tasks

        run_tests_start = build_branch_python_task(utils.TESTS_START_NAME, manage_tests_task)
        tests_task = build_python_task(utils.TESTS_RUN_NAME, jenkins_task)
        send_results_task = build_python_task("email-results", email_tests_results)
        run_tests_end = build_empty_task(utils.TESTS_END_NAME, TriggerRule.NONE_FAILED_MIN_ONE_SUCCESS)

        run_tests_start >> run_tests_end
        tests_task >> run_tests_end
        connect_tasks([run_tests_start, tests_task, send_results_task, run_tests_end])

    return create_tests_group
