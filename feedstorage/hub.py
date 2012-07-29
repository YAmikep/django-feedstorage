# Django
from django.core.exceptions import ObjectDoesNotExist

# Internal
import models
from .log import default_logger as logger


class Hub(object):
    """Interface to use the feed storage."""
    log_desc = '[Hub]'

    @classmethod
    def subscribe(cls, feed_url, callback, dispatch_uid=None):
        """Subscribes a callback to a feed to get notified of new entries.
        The susbscription is loaded and ready right away.

        Args:
            feed_url: the URL of the feed
            callback: a callable function which will be called when there are new entries Must be a function in a module or a classmethod. Do not use a staticmethod.
            dispatch_uid: A unique identifier for a signal receiver in cases where duplicate signals may be sent. See Preventing duplicate signals for more information in Django documentation.

        Returns:
            A Boolean to tell whether something went wrong.
        """

        log_desc = '%s - Subscribing to %s' % (cls.log_desc, feed_url)

        # Get or create the Feed
        f, created = models.Feed.objects.get_or_create(url=feed_url)

        callback = models.Subscription.prepare_callback(callback)
        dispatch_uid = models.Subscription.prepare_dispatch_uid(dispatch_uid, callback)

        try:
            # Get or create the subscription
            sub, sub_created = models.Subscription.objects.get_or_create(
                feed=f,
                callback=callback,
                dispatch_uid=dispatch_uid
            )

            if sub_created:
                logger.info('%s => <Subscription: %s> created' % (log_desc, sub))

            # Load it
            sub.load()
            return True

        except Exception as e:
            logger.error('%s => Cannot get or create a Subscription: callback=%s (dispatch_uid=%s) [KO]\n%s' % (
                    log_desc,
                    callback,
                    dispatch_uid,
                    e
                )
            )
            return False

    @classmethod
    def unsubscribe(cls, feed_url, callback, dispatch_uid=None):
        """Unsubscribes a callback to a Feed to not be notified anymore about new entries.

        Args:
            feed_url: the URL of the feed
            callback: a callable function which will be called when there are new entries
            dispatch_uid: A unique identifier for a signal receiver in cases where duplicate signals may be sent. See Preventing duplicate signals for more information in Django documentation.

        Returns:
            A Boolean to tell whether something went wrong.

        """

        log_desc = '%s - Unsubscribing to %s' % (cls.log_desc, feed_url)

        callback = models.Subscription.prepare_callback(callback)
        dispatch_uid = models.Subscription.prepare_dispatch_uid(dispatch_uid, callback)

        try:
            # Get the subscription
            sub = models.Subscription.objects.get(
                    feed__url=feed_url,
                    callback=callback,
                    dispatch_uid=dispatch_uid
                )

            # Delete it
            sub.delete()
            logger.info('%s => <Subscription: %s> deleted' % (log_desc, sub))
            return True

        except ObjectDoesNotExist:
            pass

        except Exception as e:
            logger.error('%s => Subscription cannot be deleted: callback=%s (dispatch_uid=%s) [KO]\n%s' % (
                    log_desc,
                    callback,
                    dispatch_uid,
                    e
                )
            )
            return False
