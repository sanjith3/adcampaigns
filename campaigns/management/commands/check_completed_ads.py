from django.core.management.base import BaseCommand
from django.utils import timezone
from campaigns.models import AdRecord


class Command(BaseCommand):
    help = 'Check and mark completed ads whose end date has passed'

    def handle(self, *args, **options):
        today = timezone.now().date()
        active_ads = AdRecord.objects.filter(status='active', end_date__lt=today)

        count = active_ads.count()
        active_ads.update(status='completed')

        self.stdout.write(
            self.style.SUCCESS(f'Successfully marked {count} ads as completed')
        )