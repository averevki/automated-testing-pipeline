"""Module implements base object for the airflow connection"""
from abc import ABC, abstractmethod

from airflow.models.connection import Connection


class BaseConnection(ABC):
    """Base connection object"""
    __instance = None
    _conn = None

    def __new__(cls):
        """Connection singleton method"""
        if cls.__instance is None:
            cls.__instance = super().__new__(cls)
        return cls.__instance

    @abstractmethod
    def _create_connection(self):
        """Create new connection and assign it to self._conn value"""

    def get_connection(self) -> Connection:
        """Connection get method"""
        if self._conn is None:
            self._create_connection()
        return self._conn

    def get_connection_id(self):
        """Connection id get method"""
        return self.get_connection().conn_id
