# Django
from django.utils.encoding import force_unicode


def date_to_unicode(d, fmt='%Y-%m-%dT%H:%M:%S.%f%z'):
    """Converts a datetime instance into a unicode string.

    Args:
        d: A datetime instance.
        format: A format to apply. Default: YYYY-MM-DDTHH:MM:SS.mmmmmm+HHMM (See http://docs.python.org/library/datetime.html)

    Returns:
        A unicode string.
    """
    return force_unicode(d.strftime(fmt))


def to_unicode(an_object, date_format='%Y-%m-%dT%H:%M:%S.%f%z'):
    """Converts any objects into a unicode string.
    A date format can be passed and will be used if the object is a date. (= any objects with a strftime function)

    Args:
        an_object: The object to convert.
        date_format: A Date format string to use if the passed object is a date. Default: YYYY-MM-DDTHH:MM:SS.mmmmmm+HHMM (See http://docs.python.org/library/datetime.html)

    Returns:
        A unicode string.
    """
    if hasattr(an_object, 'strftime'):
        return date_to_unicode(an_object, fmt=date_format)

    return force_unicode(an_object)
