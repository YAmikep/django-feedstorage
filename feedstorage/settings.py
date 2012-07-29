# Python stdlib
import os.path
import logging

# Django
from django.conf import settings as django_settings

# Internal
from .utils import PROJECT_ROOT


DEFAULT_SETTINGS = {

    # Storage settings
    # Storage used to save the retrieved feed as a file if an error occurs while fetching.
    'FILE_STORAGE': 'django.core.files.storage.FileSystemStorage',
    # Dict of arguments to pass to the Storage
    'FILE_STORAGE_ARGS': {
        # Absolute file system path to the directory that will hold downloaded feed files when an error occurs.
        'location': os.path.join(PROJECT_ROOT, 'logs/feedstorage_files/'),
    },

    # Logging settings
    'LOGGER_NAME': 'feedstorage',
    'LOGGER_FORMAT': '%(asctime)s %(levelname)s %(message)s',
    'LOG_FILE': os.path.join(PROJECT_ROOT, 'logs/feedstorage.log'),
    # Maximum size of one log file: when the size is reached, the file is archived and a new file is created.
    'LOG_SIZE': 5 * 1024 * 2 ** 10,  # 5 MB
    'LOG_LEVEL': logging.INFO,

    # Use HTTP Compression to download data
    'USE_HTTP_COMPRESSION': True,
}

# Get the user settings to update the default settings.
user_settings = getattr(django_settings, 'FEED_STORAGE_SETTINGS', {})
FEED_STORAGE_SETTINGS = dict(DEFAULT_SETTINGS.items() + user_settings.items())

globals().update(FEED_STORAGE_SETTINGS)
