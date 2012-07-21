# Django
from django.utils.translation import ugettext as _

# Internal
import models
from .log import default_logger as logger


class Hub(object):
    """Interface to use the feed storage."""
    log_desc = _('[Hub]')

    @classmethod
    def subscribe(cls, feed_url, callback, dispatch_uid=None):
        """Subscribes to a feed to get notified of new entries."""

        log_desc = _('%(log_desc)s - Subscribing to %(feed_url)s') % {'log_desc': cls.log_desc, 'feed_url': feed_url}

        # Get or create the Feed
        f, created = models.Feed.objects.get_or_create(url=feed_url)

        callback = models.Subscription.create_callack(callback)
        dispatch_uid = models.Subscription.create_dispatch_uid(dispatch_uid, callback)

        try:
            # Get or create the subscription
            sub, sub_created = models.Subscription.objects.get_or_create(
                feed=f,
                callback=callback,
                dispatch_uid=dispatch_uid
            )

            if sub_created:
                logger.info(_('%(log_desc)s => <Subscription: %(subscription)s> created') % {'log_desc': log_desc, 'subscription': sub})

            # Load it
            sub.load()
            return True

        except Exception as e:
            logger.error(_('%(log_desc)s => Cannot get or create a Subscription: callback=%(callback)s (dispatch_uid=%(dispatch_uid)s) [KO]\n%(error)s') % {
                'log_desc': log_desc,
                'callback': callback,
                'dispatch_uid': dispatch_uid,
                'error': e
            })
            return False

    @classmethod
    def unsubscribe(cls, feed_url, callback, dispatch_uid=None):
        """Unsubscribes to a Feed to not be notified anymore about new entries."""

        log_desc = _('%(log_desc)s - Unsubscribing to %(feed_url)s') % {'log_desc': cls.log_desc, 'feed_url': feed_url}

        callback = models.Subscription.create_callack(callback)
        dispatch_uid = models.Subscription.create_dispatch_uid(dispatch_uid, callback)

        try:
            # Delete the subscription
            sub = models.Subscription.objects.get(
                    feed__url=feed_url,
                    callback=callback,
                    dispatch_uid=dispatch_uid
                )
            sub.delete()
            logger.info(_('%(log_desc)s => <Subscription: %(subscription)s> deleted') % {'log_desc': log_desc, 'subscription': sub})
            return True

        except Exception as e:
            logger.error(_('%(log_desc)s => Subscription cannot be deleted: callback=%(callback)s (dispatch_uid=%(dispatch_uid)s) [KO]\n%(error)s') % {
                'log_desc': log_desc,
                'callback': callback,
                'dispatch_uid': dispatch_uid,
                'error': e
            })
            return False
