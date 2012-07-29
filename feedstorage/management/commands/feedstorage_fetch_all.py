# Django
from django.core.management.base import BaseCommand

# Internal
from ...models import Feed


class Command(BaseCommand):
    """Django command to fetch all the enabled Feeds."""
    help = 'Fetch all the enabled Feeds.'

    def handle(self, *args, **options):

        try:
            feeds = Feed.objects.filter(enabled=True)
            t = Feed.fetch_collection(feeds, '[Commands]')
            self.stdout.write('%s enabled Feeds fetched in %ss.' % (feeds.count(), t))
        except Exception as err:
            self.stderr.write('Cannot fetch the enabled Feeds. \n%s' % (err,))
