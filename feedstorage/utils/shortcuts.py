# Python stdlib
import hashlib
import os
from importlib import import_module


# Find the path of the project package to use as a default root for logs default dir
# Take care of a single settings.py module or settings package.
settings_module = import_module(os.environ['DJANGO_SETTINGS_MODULE'])
project_package = import_module(settings_module.__package__.split('.')[0])
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(project_package.__file__)), '..'))


def get_project_root():
    return PROJECT_ROOT


def ensure_path(filename):
    """Make sure the path exists."""
    d = os.path.dirname(filename)
    if not os.path.isdir(d):
        os.makedirs(d)


def md5(data):
    m = hashlib.md5()
    m.update(data)
    return m.hexdigest()


def _return(*args):
    to_return = ()

    for arg in args:
        cond, value = arg
        if cond:
            to_return += (value,)

    if len(to_return) == 1:
        return to_return[0]
    return to_return
