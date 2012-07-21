# Django
from django.contrib import admin
from django.utils.translation import ugettext as _

# Internal
from .models import Feed, FetchStatus, Entry, Subscription


class FeedAdmin(admin.ModelAdmin):
    fields = ('url', 'enabled',)
    list_display = ('id', 'url', 'nb_entries', 'enabled', 'etag',)
    list_editable = ('url', 'enabled',)
    search_fields = ('url', 'enabled',)
    list_filter = ('enabled',)
    actions = ('fetch',)

    def fetch(self, request, queryset):
        Feed.fetch_collection(queryset, '[FeedAdmin]')

    fetch.short_description = _('Fetch')


class FetchStatusAdmin(admin.ModelAdmin):
    list_display = ('feed', 'http_status_code', 'size_bytes', 'timestamp_start', 'timestamp_end', 'nb_entries', 'nb_new_entries', 'error_msg',)
    list_filter = ('feed', 'http_status_code', 'feed__enabled',)


class EntryAdmin(admin.ModelAdmin):
    list_display = ('xml',)
    list_filter = ('feed',)


class SubscriptionAdmin(admin.ModelAdmin):
    fields = ('feed', 'callback', 'dispatch_uid',)
    list_display = ('id', 'feed', 'callback', 'dispatch_uid',)
    list_filter = ('feed', 'feed__enabled',)

admin.site.register(Feed, FeedAdmin)
admin.site.register(FetchStatus, FetchStatusAdmin)
admin.site.register(Entry, EntryAdmin)
admin.site.register(Subscription, SubscriptionAdmin)
