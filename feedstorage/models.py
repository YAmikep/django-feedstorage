# Django
from django.db import models, DatabaseError
from django.utils import timezone
from django.utils.translation import ugettext as _
from django.dispatch import receiver
from django.db.models.signals import pre_delete

# Third-party apps
from lxml import etree

# Internal
from .settings import USE_HTTP_COMPRESSION
from .utils import http, md5
from .log import default_logger as logger
from .managers import FeedManager, FetchStatusManager, EntryManager, SubscriptionManager
import signals
from .utils.serializers import deserialize_function, serialize_function

FEED_FORMAT = {
    'RSS': {
        'entries': '/rss/channel/item',
        'id': 'guid'
    },
    'Atom': {
        'entries': '/feed/entry',
        'id': 'id'
    },
#    'RDF': {
#        'entries': '/rdf/item',
#        'id': 'about'
#    }
}


class Feed(models.Model):
    """A Feed"""
    url = models.URLField(unique=True, db_index=True)
    etag = models.CharField(max_length=255, null=True, blank=True)
    # Whether it must be fetched automatically when using the ``feedstorage_fetch_all`` management command, Default: True
    enabled = models.BooleanField(default=True)

    objects = FeedManager()

    def natural_key(self):
        return (self.url,)

    def __unicode__(self):
        return _('%(url)s') % {
            'url': self.url,
        }

    @property
    def log_desc(self):
        return '<Feed: %s>' % (self,)

    def nb_entries(self):
        """Returns the number of entries."""
        return self.entry_set.count()

    nb_entries.short_description = _('Nb Entries')

    @classmethod
    def fetch_collection(cls, feeds, prefix_log):
        """Fetches a collection of Feed."""
        start = timezone.now()
        log_desc = _('%(prefix_log)s - Fetching %(nb_feed)s Feeds') % {'prefix_log': prefix_log, 'nb_feed': feeds.count()}

        logger.info(_('%s => start') % (log_desc,))

        for feed in feeds:
            try:
                feed.fetch()
            except Exception as err:
                logger.error(_('%(feed)s - Fetching => [KO]\n%(error)s') % {'feed': feed.log_desc, 'error': err})

        delta = timezone.now() - start
        logger.info(_('%(log_desc)s in %(exec_time)ss => end') % {'log_desc': log_desc, 'exec_time': delta.total_seconds()})

    def fetch(self):
        """Fetches a Feed and creates the new entries. A Fetch status report is also created."""
        data = etag = status_code = entries = None
        status = FetchStatus(feed=self)
        status.timestamp_start = timezone.now()
        status.save()  # Important to save it here because we need an ID

        try:
            # Get content
            data, etag, status_code = http.get_content(
                url=self.url,
                etag=self.etag,
                use_http_compression=USE_HTTP_COMPRESSION,
                return_etag=True,
                return_status_code=True
            )
        except Exception as e:
            logger.append_msg(_('Error while getting the content.\n%s') % (e,))

        status.http_status_code = status_code
        if status_code != 200 and status_code != 304:
            logger.append_msg(_('HTTP Status code = %s != 200 or 304.') % (status_code,))
        elif status_code == 200:  # There is data to parse
            status.size_bytes = len(data)

            try:
                # Parse the xml and get the entries
                entries = self._get_entries(data)
            except Exception as e:
                logger.append_msg(_('Feed cannot be parsed.\n%s') % (e, ))

            if not entries:
                logger.append_msg(_('No entries found.'))
            else:  # There are entries to parse
                status.nb_entries = len(entries)
                new_entries = []
                # Get all the existing uid hash to compare
                # Not very efficient but OK for now
                existing_entries_uid_hash = [v for v in self.entry_set.values_list('uid_hash', flat=True)]  # Use of list comprehension because values_list returns a ValuesListQuerySet which does not have an append attribute.

                # Foreach entry, check whether it must be saved
                for i, entry in enumerate(entries):
                    uid = self._get_uid(entry)
                    if not uid:
                        logger.append_msg(_('Entry #%s: no ID can be found.') % (i, ))
                    else:  # The entry has an ID
                        uid_hash = md5(uid)
                        if uid_hash not in existing_entries_uid_hash:
                            try:
                                e_xml = etree.tostring(entry, encoding=unicode)
                                new_entry = self.entry_set.create(fetch_status=status, xml=e_xml, uid_hash=uid_hash)  # Do not use bulk_create because the size of the requests can be too big and leads to an error!
                                new_entries.append(new_entry)
                                existing_entries_uid_hash.append(uid_hash)
                            except Exception as err:
                                logger.append_msg(_('Entry #%(entry_num)s cannot be parsed.\n%(error)s') % {'entry_num': i, 'error': err})

                status.nb_new_entries = len(new_entries)
                if new_entries:
                    try:
                        Subscription.notify(self, new_entries)
                    except Exception as err:
                        logger.append_msg(_('New entries cannot be notified to the subscribers.\n%s') % (err,))

        if etag:
            self.etag = etag
            self.save()

        status.timestamp_end = timezone.now()

        # Log
        log_desc = _('%s - Fetching') % (self.log_desc,)
        error_msg = logger.flush_messages()
        if error_msg:
            # Store the file if it has been downloaded
            if data:
                error_msg += '\n' + logger.store(logger.make_filename(self.url, status.timestamp_start), data)
            status.error_msg = error_msg
            logger.error(log_desc + error_msg)
        else:
            if status_code == 304:
                logger.info(_('%s => 304 Feed not modified.') % (log_desc,))
            else:
                delta = status.timestamp_end - status.timestamp_start
                logger.info(_('%(log_desc)s => %(size)s bytes fetched in %(exec_time)ss. %(nb_new_entries)s new entries out of %(nb_entries)s.') % {
                    'log_desc': log_desc,
                    'size': status.size_bytes,
                    'exec_time': delta.total_seconds(),
                    'nb_new_entries': status.nb_new_entries,
                    'nb_entries': status.nb_entries
                })

        status.save()  # At the end to save all changes
        return error_msg == ''  # Whether there was an error

    def _get_entries(self, xml):
        """Get all the entries."""
        parser = etree.XMLParser(strip_cdata=False)  # Do not replace CDATA sections by normal text content (on by default)
        doc = etree.fromstring(xml, parser=parser)
        for k, v in FEED_FORMAT.items():
            entries = doc.xpath(v['entries'])
            if entries:
                return entries
        return None

    def _get_uid(self, entry):
        """Get the uid of an entry."""
        for k, v in FEED_FORMAT.items():
            try:
                id = entry.xpath(v['id'])[0].text
                if id:
                    return id
            except:
                pass

        return None


class FetchStatus(models.Model):
    """A fetch status"""
    feed = models.ForeignKey(Feed)
    http_status_code = models.PositiveSmallIntegerField(null=True)
    size_bytes = models.PositiveIntegerField(null=True)
    timestamp_start = models.DateTimeField(db_index=True)
    timestamp_end = models.DateTimeField(null=True)
    nb_entries = models.PositiveIntegerField(null=True, blank=True)
    nb_new_entries = models.PositiveIntegerField(null=True, blank=True)
    error_msg = models.TextField(null=True)

    class Meta:
        verbose_name_plural = _('Fetch statuses')
        unique_together = (('feed', 'timestamp_start'),)

    objects = FetchStatusManager()

    def natural_key(self):
        return self.feed.natural_key() + (self.timestamp_start,)
    natural_key.dependencies = ['feedstorage.feed']

    def __unicode__(self):
        return _('Fetch status of %(feed)s') % {
            'feed': self.feed,
        }


class Entry(models.Model):
    """An entry"""
    feed = models.ForeignKey(Feed)
    fetch_status = models.ForeignKey(FetchStatus)
    xml = models.TextField()
    uid_hash = models.CharField(max_length=32, db_index=True)

    add_date = models.DateTimeField(_('date created'), auto_now_add=True)  # auto_now_add gives error while loading fixtures
    edit_date = models.DateTimeField(_('date last modified'), auto_now=True)

    class Meta:
        verbose_name_plural = _('Entries')
        unique_together = (('feed', 'uid_hash'),)

    objects = EntryManager()

    def natural_key(self):
        return self.feed.natural_key() + (self.uid_hash,)
    natural_key.dependencies = ['feedstorage.feed']

    def __unicode__(self):
        return _('Entry of %(feed)s') % {
            'feed': self.feed,
        }


class Subscription(models.Model):
    """A subscription from a callback to a Feed."""
    feed = models.ForeignKey(Feed)
    callback = models.TextField()
    dispatch_uid = models.CharField(max_length=255)

    add_date = models.DateTimeField(_('date created'), auto_now_add=True)
    edit_date = models.DateTimeField(_('date last modified'), auto_now=True)

    class Meta:
        unique_together = (('feed', 'callback'),)

    objects = SubscriptionManager()

    def natural_key(self):
        return self.feed.natural_key() + (self.callback,)
    natural_key.dependencies = ['feedstorage.feed']

    def __unicode__(self):
        dispatch_uid = ''
        if self.dispatch_uid:
            dispatch_uid = ' - %s' % (self.dispatch_uid,)
        return _('#%(pk)s %(feed)s - <%(callback)s>%(dispatch_uid)s)') % {
            'pk': self.pk,
            'feed': self.feed.log_desc,
            'callback': self.callback,
            'dispatch_uid': dispatch_uid
        }

    @property
    def log_desc(self):
        return '<Subscription: %s>' % (self,)

    def save(self, *args, **kwargs):
        """Overrides the save method.
        Converts the callback and ensures a dispatch_uid is used."""
        self.callback = self.create_callack(self.callback)
        self.dispatch_uid = self.create_dispatch_uid(self.dispatch_uid, self.callback)

        super(Subscription, self).save(*args, **kwargs)  # Call the "real" save() method.

    def load(self):
        """Loads the subscription, i.e. connects it to the signal so that the receiver will be notified."""
        try:
            signals.new_entries_connect(self.feed, deserialize_function(self.callback), self.dispatch_uid)
            logger.info(_('%s - Loading => [OK]') % (self.log_desc,))
        except Exception as e:
            logger.error(_('%(subscription)s - Loading => The receiver cannot be connected. [KO]\n%(error)s') % {'subscription': self.log_desc, 'error': e})

    def unload(self):
        """Unloads the subscription, i.e. disconnects it from the  signal."""
        try:
            signals.new_entries_disconnect(self.feed, deserialize_function(self.callback), self.dispatch_uid)
            logger.info(_('%s - Unloading => [OK]') % (self.log_desc,))
        except Exception as e:
            logger.error(_('%(subscription)s - Unloading => The receiver cannot be disconnected. [KO]\n%(error)s') % {'subscription': self.log_desc, 'error': e})

    @classmethod
    def notify(cls, feed, new_entries):
        """Notifies all the subscribers."""
        try:
            receivers_responses = signals.new_entries_send(feed, new_entries)

            # If there are no receivers, be quiet.
            if not receivers_responses:
                logger.info(_('New entries for %(feed)s - No receivers to notify') % {'feed': feed.log_desc})
                return

            # Otherwise check their response.
            for receiver, response in receivers_responses:
                if not response:
                    logger.info(_('New entries for %(feed)s - Notifying receiver %(receiver)s => [OK]') % {'feed': feed.log_desc, 'receiver': receiver})
                else:
                    logger.error(_('New entries for %(feed)s - Notifying receiver %(receiver)s => [KO]\n %s') % {'feed': feed.log_desc, 'receiver': receiver})
        except Exception as e:
            logger.error(_('New entries for %(feed)s - Notifying all subscribers => [KO]\n%(error)s') % {'feed': feed.log_desc, 'error': e})

    @classmethod
    def create_callack(cls, callback):
        """Prepares the callback for the DB."""
        if callable(callback):
            callback = serialize_function(callback)
        return callback

    @classmethod
    def create_dispatch_uid(cls, dispatch_uid, callback):
        """Creates a dispatch_uid."""
        if not dispatch_uid:
            dispatch_uid = md5(cls.create_callack(callback))
        return dispatch_uid


# Unload the subscription when being deleted.
# To ensure customized delete logic gets executed, you can use pre_delete and/or post_delete signals instead of overriding the delete method.
# See note in Django doc: Note that the delete() method for an object is not necessarily called when deleting objects in bulk using a QuerySet.
@receiver(pre_delete, sender=Subscription)
def subscription_deleted(sender, **kwargs):
    instance = kwargs.get('instance')
    instance.unload()

# Load the existing subscriptions when starting.
# You must ignore the errors when syncdb is used for the first time: this is normal because the DB is not created yet
try:
    logger.info(_('[Subscriptions] - Loading existing subscriptions => init'))
    for s in Subscription.objects.all():
        s.load()
    logger.info(_('[Subscriptions] - Loading existing subscriptions => ready'))

except DatabaseError as err:
    logger.error(_('[Subscriptions] - Loading existing subscriptions => failed [KO]\n%s') % (err,))
