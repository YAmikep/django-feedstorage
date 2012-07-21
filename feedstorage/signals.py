# Python stdlib
import threading

# Django
import django.dispatch

SENDER = 'feedstorage'
FEED_NEW_ENTRIES_SIGNALS = {}  # Store all the new entries signals: 1 new entries signal per feed
LOCK = threading.Lock()  # Used to control the access to the FEED_NEW_ENTRIES_SIGNALS dict


def make_new_entries_signal():
    """Factory to create a new entries signal."""
    return django.dispatch.Signal(providing_args=['feed_url', 'new_entries'])


def new_entries_connect(feed, callback, dispatch_uid):
    """Connects a callback to a feed."""
    LOCK.acquire()
    try:
        if not feed.pk in FEED_NEW_ENTRIES_SIGNALS:
            FEED_NEW_ENTRIES_SIGNALS[feed.pk] = make_new_entries_signal()
        FEED_NEW_ENTRIES_SIGNALS[feed.pk].connect(callback, dispatch_uid=dispatch_uid)
    finally:
        LOCK.release()


def new_entries_disconnect(feed, callback, dispatch_uid):
    """Disconnects a callback to a feed."""
    LOCK.acquire()
    try:
        if feed.pk in FEED_NEW_ENTRIES_SIGNALS:
            FEED_NEW_ENTRIES_SIGNALS[feed.pk].disconnect(callback, dispatch_uid=dispatch_uid)
    finally:
        LOCK.release()


def new_entries_send(feed, new_entries):
    """Sends notifications to the receivers of the new entries signals.
    
    Uses send_robust to ensure all receivers are notified of the signal.

    Returns:
        A list of tuple pairs [(receiver, response), ... ], representing the list of called receiver functions and their response values.
        See the Django documentation about signals for further information.
    """
    if feed.pk in FEED_NEW_ENTRIES_SIGNALS:
        return FEED_NEW_ENTRIES_SIGNALS[feed.pk].send_robust(sender=SENDER, feed_url=feed.url, new_entries=new_entries)
