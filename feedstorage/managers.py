# Django
from django.db import models


class FeedManager(models.Manager):
    def get_by_natural_key(self, url):
        return self.get(url=url)


class FetchStatusManager(models.Manager):
    def get_by_natural_key(self, feed_url, timestamp_start):
        return self.get(feed__url=feed_url, timestamp_start=timestamp_start)


class EntryManager(models.Manager):
    def get_by_natural_key(self, feed_url, uid_hash):
        return self.get(feed__url=feed_url, uid_hash=uid_hash)


class SubscriptionManager(models.Manager):
    def get_by_natural_key(self, feed_url, callback):
        return self.get(feed__url=feed_url, callback=callback)
