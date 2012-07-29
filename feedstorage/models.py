# Python stdlib
import hashlib

# Django
from django.db import models, DatabaseError
from django.utils import timezone
from django.dispatch import receiver
from django.db.models.signals import pre_delete

# Third-party apps
from lxml import etree

# Internal
from .settings import USE_HTTP_COMPRESSION
from .log import default_logger as logger
from .managers import FeedManager, FetchStatusManager, EntryManager, SubscriptionManager
import signals
from .utils import http
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
        return '%s' % (
            self.url,
        )

    @property
    def log_desc(self):
        return '<Feed: %s>' % (self,)

    def nb_entries(self):
        """Returns the number of entries."""
        return self.entry_set.count()

    nb_entries.short_description = 'Nb Entries'

    @classmethod
    def fetch_collection(cls, feeds, prefix_log):
        """Fetches a collection of Feed.

        Args:
            feeds: the collection of Feed to fetch
            prefix_log: a prefix to use in the log to know who called it

        Returns:
            The time elapsed in seconds.
        """
        start = timezone.now()
        log_desc = '%s - Fetching %s Feeds' % (prefix_log, feeds.count())

        logger.info('%s => start' % (log_desc,))

        for feed in feeds:
            try:
                feed.fetch()
            except Exception as err:
                logger.error('%s - Fetching => [KO]\n%s' % (feed.log_desc, err))

        delta = timezone.now() - start
        logger.info('%s in %ss => end' % (log_desc, delta.total_seconds()))

        return delta

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
            logger.append_msg('Error while getting the content.\n%s' % (e,))

        status.http_status_code = status_code
        if status_code != 200 and status_code != 304:
            logger.append_msg('HTTP Status code = %s != 200 or 304.' % (status_code,))
        elif status_code == 200:  # There is data to parse
            status.size_bytes = len(data)

            try:
                # Parse the xml and get the entries
                entries = self._get_entries(data)
            except Exception as e:
                logger.append_msg('Feed cannot be parsed.\n%s' % (e, ))

            if not entries:
                logger.append_msg('No entries found.')
            else:  # There are entries to parse
                status.nb_entries = len(entries)
                new_entries = []
                # Get all the existing uid hash to compare
                # Not very efficient but OK for now
                # Later, assumes that taking the X (TBD) last entries is sufficient
                existing_entries_uid_hash = [v for v in self.entry_set.values_list('uid_hash', flat=True)]  # Use of list comprehension because values_list returns a ValuesListQuerySet which does not have an append attribute.

                # Foreach entry, check whether it must be saved
                for i, entry in enumerate(entries):
                    uid = self.make_uid(entry)
                    if not uid:
                        logger.append_msg('Entry #%s: UID cannot be made.' % (i, ))
                    elif uid not in existing_entries_uid_hash:
                        try:
                            e_xml = etree.tostring(entry, encoding=unicode)
                            new_entry = self.entry_set.create(fetch_status=status, xml=e_xml, uid_hash=uid)  # Do not use bulk_create because the size of the requests can be too big and leads to an error!
                            new_entries.append(new_entry)
                            existing_entries_uid_hash.append(uid)
                        except Exception as err:
                            logger.append_msg('Entry #%s cannot be parsed.\n%s' % (i, err))

                status.nb_new_entries = len(new_entries)
                if new_entries:
                    try:
                        Subscription.notify(self, new_entries)
                    except Exception as err:
                        logger.append_msg('New entries cannot be notified to the subscribers.\n%s' % (err,))

        if etag:
            self.etag = etag
            self.save()

        status.timestamp_end = timezone.now()

        # Log
        log_desc = '%s - Fetching' % (self.log_desc,)
        error_msg = logger.flush_messages()
        if error_msg:
            # Store the file if it has been downloaded
            if data:
                error_msg += '\n' + logger.store(data, self.url, status.timestamp_start)
            status.error_msg = error_msg
            logger.error(log_desc + '\n' + error_msg)
        else:
            if status_code == 304:
                logger.info('%s => 304 Feed not modified.' % (log_desc,))
            else:
                delta = status.timestamp_end - status.timestamp_start
                logger.info('%s => %s bytes fetched in %ss. %s new entries out of %s.' % (
                    log_desc,
                    status.size_bytes,
                    delta.total_seconds(),
                    status.nb_new_entries,
                    status.nb_entries
                ))

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

    @classmethod
    def _get_entry_id(cls, entry):
        """Get the ID of an entry."""
        for k, v in FEED_FORMAT.items():
            try:
                id = entry.xpath(v['id'])[0].text
                if id:
                    return id
            except:
                pass

        return None

    @classmethod
    def calc_hash(cls, data):
        """Calculates hash."""
        m = hashlib.md5()
        m.update(data)
        return m.hexdigest()

    @classmethod
    def make_uid(cls, entry):
        """Make a suitable uid for the storage."""
        uid = cls._get_entry_id(entry)
        if uid:
            return cls.calc_hash(uid)

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
        verbose_name_plural = 'Fetch statuses'
        unique_together = (('feed', 'timestamp_start'),)

    objects = FetchStatusManager()

    def natural_key(self):
        return self.feed.natural_key() + (self.timestamp_start,)
    natural_key.dependencies = ['feedstorage.feed']

    def __unicode__(self):
        return 'Fetch status of %s' % (
            self.feed,
        )


class Entry(models.Model):
    """An entry"""
    feed = models.ForeignKey(Feed)
    fetch_status = models.ForeignKey(FetchStatus)
    xml = models.TextField()
    uid_hash = models.CharField(max_length=32, db_index=True)

    add_date = models.DateTimeField('date created', auto_now_add=True)  # auto_now_add gives error while loading fixtures
    edit_date = models.DateTimeField('date last modified', auto_now=True)

    class Meta:
        verbose_name_plural = 'Entries'
        unique_together = (('feed', 'uid_hash'),)

    objects = EntryManager()

    def natural_key(self):
        return self.feed.natural_key() + (self.uid_hash,)
    natural_key.dependencies = ['feedstorage.feed']

    def __unicode__(self):
        return 'Entry of %s' % (
            self.feed,
        )


class Subscription(models.Model):
    """A subscription from a callback to a Feed."""
    feed = models.ForeignKey(Feed)
    callback = models.TextField(db_index=True)
    dispatch_uid = models.CharField(max_length=255)

    add_date = models.DateTimeField('date created', auto_now_add=True)
    edit_date = models.DateTimeField('date last modified', auto_now=True)

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
        return '#%s %s - <%s>%s)' % (
            self.pk,
            self.feed.log_desc,
            self.callback,
            dispatch_uid
        )

    @property
    def log_desc(self):
        return '<Subscription: %s>' % (self,)

    def save(self, *args, **kwargs):
        """Overrides the save method.
        Converts the callback and ensures a dispatch_uid is used."""
        self.callback = self.prepare_callback(self.callback)
        self.dispatch_uid = self.prepare_dispatch_uid(self.dispatch_uid, self.callback)

        super(Subscription, self).save(*args, **kwargs)  # Call the "real" save() method.

    def load(self):
        """Loads the subscription, i.e. connects it to the signal so that the receiver will be notified."""
        try:
            if signals.new_entries_connect(self.feed, deserialize_function(self.callback), self.dispatch_uid):
                logger.info('%s - Loading => [OK]' % (self.log_desc,))
        except Exception as e:
            logger.error('%s - Loading => The receiver cannot be connected. [KO]\n%s' % (self.log_desc, e))

    def unload(self):
        """Unloads the subscription, i.e. disconnects it from the  signal."""
        try:
            if signals.new_entries_disconnect(self.feed, deserialize_function(self.callback), self.dispatch_uid):
                logger.info('%s - Unloading => [OK]' % (self.log_desc,))
        except Exception as e:
            logger.error('%s - Unloading => The receiver cannot be disconnected. [KO]\n%s' % (self.log_desc, e))

    @classmethod
    def notify(cls, feed, new_entries):
        """Notifies all the subscribers."""
        try:
            receivers_responses = signals.new_entries_send(feed, new_entries)

            # If there are no receivers, be quiet.
            if not receivers_responses:
                logger.info('New entries for %s - No receivers to notify' % (feed.log_desc))
                return

            # Otherwise check their response.
            for receiver, response in receivers_responses:
                if not response:
                    logger.info('New entries for %s - Notifying receiver %s => [OK]' % (feed.log_desc, receiver))
                else:
                    logger.error('New entries for %s - Notifying receiver %s => [KO]\n%s' % (feed.log_desc, receiver, response))
        except Exception as e:
            logger.error('New entries for %s - Notifying all subscribers => [KO]\n%s' % (feed.log_desc, e))

    @classmethod
    def prepare_callback(cls, callback):
        """Prepares a callback to be stored in the DB. i.e. converts it to a string.

        Returns:
            A string.
        """
        if callable(callback):
            callback = serialize_function(callback)
        return callback

    @classmethod
    def _calc_dispatch_uid_hash(cls, data):
        """Calculates hash."""
        m = hashlib.md5()
        m.update(data)
        return m.hexdigest()

    @classmethod
    def prepare_dispatch_uid(cls, dispatch_uid, callback):
        """Creates a dispatch_uid."""
        if not dispatch_uid:
            dispatch_uid = cls._calc_dispatch_uid_hash(cls.prepare_callback(callback))
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
    logger.info('[Subscriptions] - Loading existing subscriptions => init')
    for s in Subscription.objects.all():
        s.load()
    logger.info('[Subscriptions] - Loading existing subscriptions => ready')

except DatabaseError as err:
    logger.error('[Subscriptions] - Loading existing subscriptions => failed [KO]\n%s' % (err,))
