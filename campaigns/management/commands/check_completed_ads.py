from django.core.management.base import BaseCommand #type: ignore
from django.utils import timezone #type: ignore
from campaigns.models import AdRecord
from django_eventstream import eventstream  # type: ignore


class Command(BaseCommand):
    help = 'Check and mark completed ads whose end date has passed'

    def handle(self, *args, **options):
        today = timezone.now().date()
        active_ads = AdRecord.objects.filter(status='active', end_date__lt=today)

        count = active_ads.count()
        active_ads.update(status='completed')

        # Notify clients to reload if any status changed
        if count > 0:
            eventstream.send_event('general', 'message', {'type': 'reload'})

        self.stdout.write(
            self.style.SUCCESS(f'Successfully marked {count} ads as completed')
        )