from importlib import import_module


def serialize_function(func):
    """Serializes a function or a class method as a string.
    It works with:
        - function
        - class method i.e. methods declared with the @classmethod decorator

    Args:
        func: a function or class method

    Returns:
        A string.

    Raises:
        An exception if the function/classmethod cannot be serialized.
    """
    # Check first for class method in class
    if hasattr(func, 'im_func') and hasattr(func, 'im_self'):
        return '%s.%s.%s' % (func.im_self.__module__, func.im_self.__name__, func.im_func.__name__)
    # Check for function
    elif hasattr(func, '__module__') and hasattr(func, '__name__'):
        return '%s.%s' % (func.__module__, func.__name__)

    raise Exception('A string cannot be resolved for this function/method.')


def deserialize_function(name):
    """Deserializes a function given a string.
    It works with:
        - function: module....function
        - class method: module....class.function  i.e. methods declared with the @classmethod decorator

    Be careful: obviously, it does not work with staticmethod.

    Args:
        name: a string being the function/method to deserialize

    Returns:
        A callable if successful. None otherwise.
    """
    if name is None:
        return None

    if callable(name):
        return name

    # Look for the function name
    sep = name.rfind('.')
    if sep <= 0:
        return None
    module_name = name[:sep]
    function_name = name[sep + 1:]

    f = None
    try:  # try module....function
        f = getattr(import_module(module_name), function_name)
    except:
        try:  # try module....class.function
            # Get the class
            sep = module_name.rfind('.')
            klass = getattr(import_module(module_name[:sep]), module_name[sep + 1:])
            f = getattr(klass, function_name)
        except:
            pass

    if callable(f):
        return f

    return None
