from importlib import import_module


def serialize_function(target):
    """Serialize a function or a static/class method as a string to be stored in the DB."""
    # Check first for method in class
    if hasattr(target, 'im_func') and hasattr(target, 'im_self'):
        return '%s.%s.%s' % (target.im_self.__module__, target.im_self.__name__, target.im_func.__name__)
    # Check for function
    elif hasattr(target, '__module__') and hasattr(target, '__name__'):
        return '%s.%s' % (target.__module__, target.__name__)

    raise Exception('A string cannot be resolved for this function/method.')


def deserialize_function(name):
    """Get a function or static/class method given a string"""
    sep = name.rfind('.')
    module_name = name[:sep]
    function_name = name[sep + 1:]

    try:  # it is a function
        m = import_module(module_name)
    except:
        try:  # it is a class or static method, must first import only the module and get the class
            sep = module_name.rfind('.')
            class_name = module_name[sep + 1:]
            module_name = module_name[:sep]
            m = import_module(module_name)
            m = getattr(m, class_name)
        except:
            pass

    return getattr(m, function_name)
