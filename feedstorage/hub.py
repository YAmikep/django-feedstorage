# Internal
import models
from .log import default_logger as logger


class Hub(object):
    """Interface to use the feed storage."""
    log_desc = '[Hub]'

    @classmethod
    def subscribe(cls, feed_url, callback, dispatch_uid=None):
        """Subscribes callback to a feed to get notified of new entries.
        The susbscription is loaded and ready right away.     
        
        Returns:
            Boolean to tell whether something goes wrong. 
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
        """Unsubscribes callback to a Feed to not be notified anymore about new entries."""

        log_desc = '%s - Unsubscribing to %s' % (cls.log_desc, feed_url)

        callback = models.Subscription.prepare_callback(callback)
        dispatch_uid = models.Subscription.prepare_dispatch_uid(dispatch_uid, callback)

        try:
            # Delete the subscription
            sub = models.Subscription.objects.get(
                    feed__url=feed_url,
                    callback=callback,
                    dispatch_uid=dispatch_uid
                )
            sub.delete()
            logger.info('%s => <Subscription: %s> deleted' % (log_desc, sub))
            return True

        except Exception as e:
            logger.error('%s => Subscription cannot be deleted: callback=%s (dispatch_uid=%s) [KO]\n%s' % (
                    log_desc,
                    callback,
                    dispatch_uid,
                    e
                )
            )
            return False
