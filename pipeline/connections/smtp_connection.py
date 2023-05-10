"""Module implements SMTP connection object, used by Airflow to send emails with test results"""
import os
import logging

import pipeline.utils as utils
from pipeline.connections.base_connection import BaseConnection
from pipeline.utils.builders import build_connection


class SMTPConnection(BaseConnection):
    _connection_id = "smtp_default"

    @staticmethod
    def _configure_server():
        """Set smtp server configuration environment variables"""
        os.environ["AIRFLOW__SMTP__SMTP_HOST"] = "smtp.gmail.com"
        if utils.SEND_FROM_LOGIN is not None:
            os.environ["AIRFLOW__SMTP__SMTP_MAIL_FROM"] = utils.SEND_FROM_LOGIN
        os.environ["AIRFLOW__SMTP__SMTP_SSL"] = "true"
        os.environ["AIRFLOW__SMTP__SMTP_STARTTLS"] = "false"
        os.environ["AIRFLOW__SMTP__SMTP_PORT"] = "465"

    def _create_connection(self):
        """Create new smtp connection from settings"""
        self._configure_server()
        logging.info("SMTP server configured")

        conn = build_connection(self._connection_id, utils.SEND_FROM_LOGIN, utils.SEND_FROM_PASSWORD)
        os.environ[f"AIRFLOW_CONN_{self._connection_id.upper()}"] = conn.get_uri()
        logging.info("SMTP connection configured")

        self._conn = conn
