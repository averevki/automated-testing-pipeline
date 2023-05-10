"""Dynaconf config settings declaration"""
from dynaconf import Validator
from dynaconf.base import LazySettings
from dynaconf.constants import DEFAULT_SETTINGS_FILES

settings = LazySettings(
    environments=True,
    lowercase_read=True,
    load_dotenv=True,
    default_settings_paths=DEFAULT_SETTINGS_FILES,
    validators=[
        Validator("modules", must_exist=True)
    ],
    validate_only=["modules"],
)
