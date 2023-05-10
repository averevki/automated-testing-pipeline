"""Module implements Jenkins connection object, used by Airflow to run tests on product"""
import os
import logging

from airflow.providers.jenkins.hooks.jenkins import JenkinsHook

import pipeline.utils as utils
from pipeline.connections.base_connection import BaseConnection
from pipeline.utils.builders import build_connection


class JenkinsConnection(BaseConnection):
    _connection_id = "jenkins_connection"

    def _create_connection(self):
        """Create new jenkins connection from settings"""
        conn = build_connection(self._connection_id, utils.JENKINS_LOGIN, utils.JENKINS_PASSWORD,
                                utils.JENKINS_HOST, utils.JENKINS_PROTOCOL, utils.JENKINS_PORT, utils.JENKINS_URI)
        os.environ[f"AIRFLOW_CONN_{self._connection_id.upper()}"] = conn.get_uri()
        logging.info("JENKINS connection configured")

        self._conn = conn

    def get_jenkins_hook(self):
        """Get jenkins connection hook"""
        jenkins_connection = self.get_connection()
        logging.info(f"Connecting to jenkins on: {jenkins_connection.get_uri()}")
        return JenkinsHook(jenkins_connection.conn_id)
