"""Framework utility functions"""
from pathlib import Path


def resolve_environment_installation_command(submodule_path):
    """Get environment installation command by project package manager"""
    if Path.is_file(submodule_path / "Pipfile"):
        return "pipenv install --dev"

    if Path.is_file(submodule_path / "pyproject.toml"):
        return "poetry install"


def connect_tasks(tasks: list):
    """Make linear tasks dependencies pipeline from the parsed tasks"""
    for index, task in enumerate(tasks):
        if len(tasks) > index + 1:
            task.set_downstream(tasks[index + 1])
