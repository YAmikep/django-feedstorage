# Django
from django.core.files.storage import get_storage_class
from django.utils.functional import LazyObject

# Internal
from .settings import (
    FILE_STORAGE, FILE_STORAGE_ARGS,
    LOGGER_NAME, LOG_FILE, LOG_SIZE, LOGGER_FORMAT, LOG_LEVEL
)
from .utils import LoggerWithStorage


class DefaultFileStorage(LazyObject):
    def _setup(self):
        self._wrapped = get_storage_class(FILE_STORAGE)(**FILE_STORAGE_ARGS)

default_file_storage = DefaultFileStorage()
default_logger = LoggerWithStorage(
    storage=default_file_storage,
    logger_name=LOGGER_NAME,
    level=LOG_LEVEL,
    log_file=LOG_FILE,
    log_size=LOG_SIZE,
    logger_format=LOGGER_FORMAT
)
