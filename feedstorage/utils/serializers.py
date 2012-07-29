# Python stdlib
from importlib import import_module


class SerializationFailed(Exception):
    pass


class DeserializationFailed(Exception):
    pass


def serialize_function(func):
    """Serializes a function or a class method.
    It creates a string that will be sufficient to retrieve the function.

    It works with:
        - function i.e. in a module
        - class method i.e. methods declared with the @classmethod decorator

    It DOES NOT work with:
        - static method i.e. methods using the @staticmethod decorator

    Args:
        func: a function or class method

    Returns:
        A string.

    Raises:
        A SerializationFailed exception if the function/classmethod cannot be serialized.
    """
    # Check first for class method in class
    if hasattr(func, 'im_func') and hasattr(func, 'im_self'):
        return '%s.%s.%s' % (func.im_self.__module__, func.im_self.__name__, func.im_func.__name__)
    # Check for function
    elif hasattr(func, '__module__') and hasattr(func, '__name__'):
        return '%s.%s' % (func.__module__, func.__name__)

    raise SerializationFailed('A string cannot be resolved for this function/method.')


def deserialize_function(name):
    """Deserializes a function or a class method given a string.
    It will retrieve the function and return a callable to be able to call it.

    It works with:
        - function i.e. in a module
        - class method i.e. methods declared with the @classmethod decorator

    It DOES NOT work with:
        - static method i.e. methods using the @staticmethod decorator

    Args:
        name: a string being the function/classmethod to deserialize

    Returns:
        A callable.

    Raises:
        A DeserializationFailed exception if the function/classmethod cannot be retrieved.
    """
    if callable(name):
        return name

    if name is not None:

        # Look for the function name
        sep = name.rfind('.')
        if sep > 0:

            module_name = name[:sep]
            function_name = name[sep + 1:]

            f = None
            try:  # try module....function
                f = getattr(import_module(module_name), function_name)
            except:
                try:  # try module....class.function (classmethod)
                    # Get the class
                    sep = module_name.rfind('.')
                    klass = getattr(import_module(module_name[:sep]), module_name[sep + 1:])
                    f = getattr(klass, function_name)
                except:
                    pass

            if callable(f):
                return f

    raise DeserializationFailed('No function/classmethod can be retrieved from the string: %s' % (name,))
