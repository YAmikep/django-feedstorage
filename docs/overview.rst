Supported FEED formats:
======================

For now, just the two main common feed formats are supported: RSS and Atom.


Quick HOW-TO: use the Hub interface to subscribe/unsubscribe to a Feed
======================================================================
In your application, just use the provided Hub interface:

- Hub.subscribe(feed_url, callback, dispatch_uid) when you want to be notified of new entries for a specific feed
- Hub.unsubscribe(feed_url, callback, dispatch_uid) to stop getting notifications of new entries for a specific feed

with:

* ``feed_url``: The URL of the Feed
* ``dispatch_uid``: A unique identifier for a signal receiver in cases where duplicate signals may be sent. See Preventing duplicate signals for more information in Django documentation.
* ``callback``: a callable function which will be notified of the new entries

* Example::
    
    # Here is my callback
    def new_entries_detected(cls, sender, **kwargs):
        feed_url = kwargs.get('feed_url')
        entries = kwargs.get('new_entries')  
        
        # Work with entries now
        for entry in entries:
            print entry.xml
            # xml pieces are available through entry.xml

    # I am going to use the Hub interface to subscribe/unsubscribe to a Feed
    from feedstorage.hub import Hub

    # I want to follow these 2 Feeds and be notified when there are new entries
    Hub.subscribe('https://www.djangoproject.com/rss/community/blogs/', new_entries_detected, 'my_app')
    Hub.subscribe('https://www.djangoproject.com/rss/community/jobs/', new_entries_detected, 'my_app')

    # Now, every time there are new entries, I will be notified and my callback will handle them.

    # Later on, I can unsubscribe to a Feed to not be notified anymore about new entries.
    Hub.unsubscribe('https://www.djangoproject.com/rss/community/blogs/', new_entries_detected, 'my_app')

    # Now, I will just get notified when there are new entries for the django jobs Feed.


Scheduling: automatic fetching
==============================

You can manually launch the fetching of the Feeds from the admin but to really make it powerful, you should make it automatic.

For now, the application does not take care of scheduling so you can set up a cron job and use the ``feedstorage_fetch_all`` management command. 
This management command fetches all the enabled Feeds.
Make sure you have the ``DJANGO_SETTINGS_MODULE`` environment variable set and add the following to your crontab::

    * * * * * /full/path/to/manage.py feedstorage_fetch_all
    

Logging
=======

By default, the feedstorage application creates a log file to track what is going on.
It also saves the Feed as a file when an error occurs while parsing.
This ensures that no version of the Feed will be lost and allows an administrator to go through it later on.

By default, a logs folder is created in the outer directory containing your project.
It contains the log file and a folder to save the files.
For example, based on the Django tutorial, the structure would look like this::

    mysite/
        manage.py
        logs/
            feedstorage.log     # the log file
            feedstorage_files/  # the folder where files are saved
        mysite/
            __init__.py
            settings.py
            urls.py
            wsgi.py

You can use your own logger if you already have own. (see below)
         
            
Configuration
=============

The feedstorage application has one optional setting that can be set in ``settings.py``
It mainly controls the way logging is managed.
You can change the default behavior by adding a dict 
called ``FEED_STORAGE_SETTINGS`` to your ``settings.py`` file.

``USE_HTTP_COMPRESSION``
------------------------

Default: ``True``.

If ``True``, HTTP compression will be used to download data if the remote server hosting the Feed handles it.

``FILE_STORAGE``
----------------

Default: ``'django.core.files.storage.FileSystemStorage'``

The storage class to use to save files when an error occurs in parsing.
It is based on the Django File storage API, you must be able to use any storage implementing this API.

``FILE_STORAGE_ARGS``
---------------------

Default: a dict with the location key being the path to the logs/feedstorage_files/ folder as discussed above.

A dict listing the arguments for the storage class.

For a FileSystemStorage class, the location is required.::

    'FILE_STORAGE_ARGS': {
            'location': '/my/path/to/logs/files/',
    }
    
``LOGGER_NAME``
---------------

Default: ``'feedstorage'``

The name of the logger. 
If you have defined a logger somewhere else and want to use it, this is possible by changing this setting.

If you provide an existing logger which has at least one handler, 
it will be used and the following settings will be ignored.

``LOGGER_FORMAT``
-----------------

Default: ``'%(asctime)s %(levelname)s %(module)s %(message)s'``
The format used to log.

.. admonition:: 

    This setting is ignored if the logger name references an existing logger containing at least one handler.

``LOG_FILE``
------------

Default: the path to the logs/feedstorage.log file as discussed above.

The path to the log file.

.. admonition:: 

    This setting is ignored if the logger name references an existing logger containing at least one handler.

``LOG_SIZE``
------------

Default: ``5 * 1024 * 2 ** 10, #5 MB``

The maximum size of one log file.
When the size is reached, the file is archived and a new file is created.


``LOG_LEVEL``
-------------

Default: logging.INFO

The level of the logger.

* Example:

For most of the users, you will just want to change where the log and files are saved, all you have to do is::

    FEED_STORAGE_SETTINGS = {
        'FILE_STORAGE_ARGS': {
            # I want to change the location of the saved files
            'location': '/my/path/logs/files/',
        },
        # I want to change the location of the log file
        'LOG_FILE': '/my/path/logs/mylogfile.log',
    }
