# Dependencies: third-party apps
import requests  # http://docs.python-requests.org

# Django
from django.utils import timezone


class RequestsModuleError(Exception):
    """An error occured in the Requests third-party module."""
    pass


def _return(*args):
    """Selects which value to return."""
    to_return = ()

    for arg in args:
        cond, value = arg
        if cond:
            to_return += (value,)

    if len(to_return) == 1:
        return to_return[0]
    return to_return


def get_content(url, etag=None, use_http_compression=True, return_etag=False, return_status_code=False, return_datetime=False, return_response=False):
    """Fetches data and metadata from an URL.

    Dependency: requests module (http://docs.python-requests.org): HTTP library, written in Python, for human beings.

    Args:
        url: The URL to fetch.
        etag: The ETag to use to compare whether the file has changed.
        use_http_compression: Whether http compression can be used. Default=True
        return_etag: Whether it must return the new etag. Default=False
        return_status_code: Whether it must return the HTTP status code. Default=False
        return_datetime: Whether it must return the datetime of fetching. Default=False
        return_response: Whether it must return the response instance. Default=False

    Returns:
        Either a string being the fetched data.
        Or a tuple wrapping the asked values if AT LEAST ONE of the optional returned values is asked: (data [, etag] [status_code,] [, datetime] [, response]).

    Raises:
        RequestsModuleError: An error occured in the Requests third-party module.
    """
    error_msg = 'HTTP GET %s' % (url,)

    # Sets the headers.
    headers = {}
    if etag:
        headers['If-None-Match'] = etag
    if not use_http_compression:
        headers['Accept-Encoding'] = ''

    downloaded_date = (return_datetime and [timezone.now()] or [None])[0]

    # Makes the request.
    try:
        response = requests.get(url, headers=headers)
    except StandardError as e:
        raise RequestsModuleError('%s - Requests module error\n%s' % (error_msg, e))

    data = response.content
    etag = (return_etag and [response.headers.get('ETag', None)] or [None])[0]
    status_code = response.status_code

    return _return((True, data), (return_etag, etag), (return_status_code, status_code), (return_datetime, downloaded_date), (return_response, response))
