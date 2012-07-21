# Python stdlib
import os
import os.path
import logging
import string
import unicodedata

# Django
from django.utils.functional import LazyObject
from django.core.files.base import ContentFile

# Internal
from .unicode import to_unicode
from .shortcuts import ensure_path


class ImproperlyConfigured(Exception):
    pass


def windows_safe(s):
    """Replaces colon by semicolon on Windows because Windows cannot handle filename with colon."""
    if os.name == 'nt':
        return s.replace(':', ';')
    return s


def make_safe(s):
    valid_chars = ":;+-_.() %s%s" % (string.ascii_letters, string.digits)

    if isinstance(s, unicode):
        s = unicodedata.normalize('NFKD', s).encode('ASCII', 'ignore')
    s = s.replace('/', '_')

    return windows_safe(u''.join(c for c in s if c in valid_chars))


def make_filename(*args, **kwargs):
    delimiter = kwargs.get('delimiter', u'__')
    s = [to_unicode(arg).lower() for arg in args]
    filename = delimiter.join(s)
    return make_safe(filename)


class DefaultLogger(LazyObject):
    """Logger with default file handler if no one exists."""
    def __init__(self, logger_name=None, log_file=None, level=logging.INFO, log_size=5 * 1024 * 2 ** 10, logger_format='%(asctime)s %(levelname)s %(module)s %(message)s'):
        # IMPORTANT: must be here to avoid recursion
        super(DefaultLogger, self).__init__()

        if not logger_name:
            raise ImproperlyConfigured('A logger name is mandatory.')

        logger = logging.getLogger(logger_name)
        if not logger.handlers and not log_file:
            raise ImproperlyConfigured('A log_file is mandatory to use the default RotatingFileHandler when the logger does not exist or does not contain any handler.')

        self.__dict__['logger'] = logger
        self.__dict__['logger_name'] = logger_name
        self.__dict__['log_file'] = log_file
        self.__dict__['log_size'] = log_size
        self.__dict__['logger_format'] = logger_format
        self.__dict__['level'] = level
        self.__dict__['messages'] = []

    def _setup(self):

        if self.logger.level == 0:
            self.logger.setLevel(self.level)

        # Create default handler if no one exists.
        if not self.logger.handlers:
            # Make sure the directory exists.
            ensure_path(self.log_file)

            handler = logging.handlers.RotatingFileHandler(
                filename=self.log_file,
                maxBytes=self.log_size,
                backupCount=50
            )
            handler.formatter = logging.Formatter(fmt=self.logger_format)

            self.logger.handlers.append(handler)

        self._wrapped = self.logger

    def append_msg(self, msg):
        self.messages.append(msg)

    def flush_messages(self):
        msg = ''
        for m in self.messages:
            msg += '\n' + m
        self.__dict__['messages'] = []
        return msg

    def log_messages(self, lvl=logging.ERROR, start='', end=''):
        msg = start + self.flush_messages() + end
        self.log(lvl, msg)
        return msg


class LoggerWithStorage(DefaultLogger):
    """Logger with a Storage."""
    def __init__(self, storage=None, logger_name=None, log_file=None, level=logging.INFO, log_size=5 * 1024 * 2 ** 10, logger_format='%(asctime)s %(levelname)s %(module)s %(message)s'):
        # IMPORTANT: must be here to avoid recursion
        super(LoggerWithStorage, self).__init__(logger_name, log_file, level, log_size, logger_format)

        if not (storage and logger_name):
            raise ImproperlyConfigured('A storage AND a logger name are mandatory.')

        logger = logging.getLogger(logger_name)
        if not logger.handlers and not log_file:
            raise ImproperlyConfigured('A log file is mandatory to use the default RotatingFileHandler when the logger does not exist or does not contain any handler.')

        self.__dict__['storage'] = storage

    @staticmethod
    def make_filename(*args, **kwargs):
        return make_filename(*args, **kwargs)

    def store(self, filename, data):
        """Stores and returns the log message."""
        log_msg = 'Storage attempt:'
        filename = make_safe(filename)

        if self.storage.exists(filename):
            log_msg = '%s File already exists: <%s> ' % (log_msg, filename,)
        else:
            try:
                output = self.storage.save(filename, ContentFile(data))
                log_msg = '%s File saved: <%s> in <%s>.' % (log_msg, output, getattr(self.storage, 'location', 'No location'))
            except StandardError as err:
                log_msg = '%s Cannot save the file <%s> in <%s>.\n%s' % (log_msg, filename, getattr(self.storage, 'location', 'No location'), err)

        return log_msg

    def _log_and_store(self, msg, filename, data, lvl):
        """Logs a message and stores some data in the file."""
        log_msg = '%s\n%s' % (msg, self.store(filename, data))
        self.log(lvl, log_msg)
        return log_msg

    def debug_and_store(self, msg, filename, data):
        return self._log_and_store(msg, filename, data, logging.DEBUG)

    def info_and_store(self, msg, filename, data):
        return self._log_and_store(msg, filename, data, logging.INFO)

    def warning_and_store(self, msg, filename, data):
        return self._log_and_store(msg, filename, data, logging.WARNING)

    def error_and_store(self, msg, filename, data):
        return self._log_and_store(msg, filename, data, logging.ERROR)

    def critical_and_store(self, msg, filename, data):
        return self._log_and_store(msg, filename, data, logging.CRITICAL)
