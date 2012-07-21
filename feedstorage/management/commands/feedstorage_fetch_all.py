# Django
from django.core.management.base import BaseCommand

# Internal
from ...models import Feed


class Command(BaseCommand):
    """Django command to fetch all the enabled Feeds."""
    help = 'Fetch all the enabled Feeds.'

    def handle(self, *args, **options):
        feeds = Feed.objects.filter(enabled=True)
        Feed.fetch_collection(feeds, '[Commands]')
