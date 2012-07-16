==================
django-feedstorage
==================

The django-feedstorage is an application designed for storing Feeds entries 
and notifying subscribers only when there are new entries.


Installation
============

#. Dependencies
    requests and lxml
    
#. Run the following command inside this directory:

        python setup.py install

    Or if you're using ``pip``::

        pip install django-feedstorage

    Or if you'd prefer you can simply place the included ``feedstorage``
    directory somewhere on your Python path, or symlink to it from
    somewhere on your Python path; this is useful if you're working from a
    Mercurial checkout.

#. Add `feedstorage` to your `INSTALLED_APPS` setting::

    INSTALLED_APPS = (
        ...
    'feedstorage',
    )

#. Run syncdb.

Note that this application has been tested with Python 2.7 and a
functional installation of Django 1.4`. You can obtain Python
from http://www.python.org/ and Django from http://www.djangoproject.com/.


Configuration
=============

The feedstorage application has one optional setting that can be set in `settings.py`
It mainly controls the way logging is managed.
You can change the default behavior by adding a dict called `FEED_STORAGE_SETTINGS` to your ``settings.py``file.
See below to know how to modify it. 

#. HTTP Compression
    # Use HTTP Compression to download data
    - 'USE_HTTP_COMPRESSION': whether HTTP compression must be use when possible. Default: True. 

#. Logging
The feedstorage application creates a log file to track what is going on.
When an error occurs while parsing a Feed, the application also saves the file to be able to go through it later on.

By default, a logs folder is created in the outer directory containing your project.
It contains the log file and a folder to save the files.
For example, based on the Django tutorial, the structure would look like this:
    mysite/
        manage.py
        logs/
            feedstorage.log
            feedstorage_files/
        mysite/
            __init__.py
            settings.py
            urls.py
            wsgi.py

            
Below are the different settings related to logging you can change:
    
    - 'FILE_STORAGE': the storage class to use to save file when an error occurs in parsing.
        It is based on the Django File storage API, you must be able to use any storage implementing this API.
        Default: 'django.core.files.storage.FileSystemStorage',
    - 'FILE_STORAGE_ARGS': a dict being the arguments to pass to the storage class
        For a FileSystemStorage, the location is required. By default, the logs/feedstorage_files/ folder as discussed above is used.
        You can change where you want to save those files.
        For example:
        'FILE_STORAGE_ARGS': {
                # Absolute file system path to the directory that will hold downloaded feed files when an error occurs.
                'location': '/my/path/to/logs/files/'),
        }
    - 'LOGGER_NAME': the name of the logger. You might have defined a logger somewhere else and want to use it, this is possible by changing this setting. Default: 'feedstorage'
        If you provide an existing logger which has a handler, it will be used and the following settings will be ignored.
    - 'LOGGER_FORMAT': format of the logger Default: '%(asctime)s %(levelname)s %(module)s %(message)s',
    - 'LOG_FILE': where the log file must be saved.  By default, it is logs/feedstorage.log as discussed above.
    - 'LOG_SIZE': maximum size of one log file: when the size is reached, the file is archived and a new file is created. Default: 5 MB
    - 'LOG_LEVEL': the level of the logger. Default: logging.INFO


For example, if you just want to change where the log and files are saved::

        FEED_STORAGE_SETTINGS = {
            'FILE_STORAGE_ARGS': {
                # I want to change the location of saved files
                'location': '/my/path/logs/files/'),
            },
            # I want to change the location of the log file
            'LOG_FILE': '/my/path/logs/mylogfile.log'),
        }

  
Supported FEED formats:
======================
For now, just the two main common feed formats are supported: RSS and Atom.
  
Scheduling: automatic fetching
=============
You can manually launch the fetching of the Feeds from the admin but to really make it powerful, you should make it automatic.

For now, the app does not take care of scheduling so you can set up a cron job and use the ``feedstorage_fetch`` management command. 
This management command fetches all the enabled Feeds.
Make sure you have the ``DJANGO_SETTINGS_MODULE`` environment variable set and add the following to your crontab::

    * * * * * /full/path/to/manage.py feedstorage_fetch


Example: use of the Hub interface to subscribe/unsubscribe to a Feed
**********************************************
In your application, just use the provided Hub interface:
- Hub.subscribe(feed_url, callback, dispatch_uid) when you want to be notified of new entries for a specific feed
- Hub.unsubscribe(feed_url, callback, dispatch_uid) to stop getting notifications of new entries for a specific feed

feed_url: The URL of the Feed
dispatch_uid: A unique identifier for a signal receiver in cases where duplicate signals may be sent. 
See Preventing duplicate signals for more information in django documentation.
callback: a callable function which will be notified of the new entries

#. Example
    # Here is my callback
    def new_entries_detected(cls, sender, **kwargs):
        feed_url = kwargs.get('feed_url')
        entries = kwargs.get('new_entries')  
        # Work with entries now
        # xml pieces are available through entry.xml

    from feedstorage.hub import Hub

    # I want to follow these 2 Feeds and be notified all the time there are new entries
    Hub.subscribe('https://www.djangoproject.com/rss/community/blogs/', new_entries_detected, 'my_app')
    Hub.subscribe('https://www.djangoproject.com/rss/community/jobs/', new_entries_detected, 'my_app')
    # Every time there are new entries, I will be notified and can handle them.

    # I do not want to be notified anymore about this feed.
    Hub.unsubscribe('https://www.djangoproject.com/rss/community/blogs/', new_entries_detected, 'my_app')

    # So I will now just get notified when there are new entries for the django jobs Feed.
    
    
    
Next things to do:
*****
- write tests
- write more documentation
- test with former versions of python and django
- add Scheduling in the admin
- handle more feed formats
- notify new entries in a merged XML file instead of several Entry objects
- refactoring: create a "callback" custom field to serialize/deserialize a callable object