# Python stdlib
import threading

# Django
import django.dispatch

SENDER = 'feedstorage'
FEED_NEW_ENTRIES_SIGNALS = {}  # Store all the new entries signals: 1 new entries signal per feed
LOCK = threading.Lock()  # Used to control the access to the FEED_NEW_ENTRIES_SIGNALS dict


from django.dispatch.dispatcher import _make_id


def receiver_exist(receiver, signal, dispatch_uid):
    """Code adapted from Django code to test whether a receiver already exists."""
    if dispatch_uid:
        lookup_key = (dispatch_uid, _make_id(None))  # _make_id(sender) not use of sender
    else:
        lookup_key = (_make_id(receiver), _make_id(None))

    LOCK.acquire()
    try:
        for r_key, _ in signal.receivers:
            if r_key == lookup_key:
                return True
    finally:
        LOCK.release()

    return False


def make_new_entries_signal():
    """Factory to create a new entries signal."""
    return django.dispatch.Signal(providing_args=['feed_url', 'new_entries'])


def new_entries_connect(feed, callback, dispatch_uid):
    """Connects a callback to a feed only if it is not connected already.

    Returns:
        A boolen saying if it has been newly connected.
    """
    LOCK.acquire()
    try:
        if not feed.pk in FEED_NEW_ENTRIES_SIGNALS:
            FEED_NEW_ENTRIES_SIGNALS[feed.pk] = make_new_entries_signal()

        if not receiver_exist(callback, FEED_NEW_ENTRIES_SIGNALS[feed.pk], dispatch_uid):
            FEED_NEW_ENTRIES_SIGNALS[feed.pk].connect(callback, dispatch_uid=dispatch_uid)
            return True
    finally:
        LOCK.release()

    return False


def new_entries_disconnect(feed, callback, dispatch_uid):
    """Disconnects a callback to a feed only if it is already connected.

    Returns:
        A boolen saying if it was connected and has been disconnected.
    """
    LOCK.acquire()
    try:
        if feed.pk in FEED_NEW_ENTRIES_SIGNALS and receiver_exist(callback, FEED_NEW_ENTRIES_SIGNALS[feed.pk], dispatch_uid):
            FEED_NEW_ENTRIES_SIGNALS[feed.pk].disconnect(callback, dispatch_uid=dispatch_uid)
            return True
    finally:
        LOCK.release()

    return False


def new_entries_send(feed, new_entries):
    """Sends notifications to the receivers of the new entries signals.

    Uses send_robust to ensure all receivers are notified of the signal.

    Returns:
        A list of tuple pairs [(receiver, response), ... ], representing the list of called receiver functions and their response values.
        See the Django documentation about signals for further information.
    """
    if feed.pk in FEED_NEW_ENTRIES_SIGNALS:
        return FEED_NEW_ENTRIES_SIGNALS[feed.pk].send_robust(sender=SENDER, feed_url=feed.url, new_entries=new_entries)
