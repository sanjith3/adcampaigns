from django.core.management.base import BaseCommand  # type: ignore
from django.utils import timezone  # type: ignore
from campaigns.models import AdRecord
from django_eventstream import eventstream  # type: ignore


class Command(BaseCommand):
    help = 'Release ads from hold when hold_until date has passed (move back to enquiry)'

    def handle(self, *args, **options):
        today = timezone.now().date()
        expired_holds = AdRecord.objects.filter(status='hold', hold_until__lt=today)

        count = expired_holds.count()
        # Move back to enquiry and clear hold fields
        expired_holds.update(status='enquiry', hold_reason='', hold_until=None)

        if count > 0:
            # Notify clients (admin/user dashboards) to refresh
            eventstream.send_event('general', 'message', {'type': 'reload'})

        self.stdout.write(
            self.style.SUCCESS(f'Successfully released {count} expired holds back to enquiries')
        )


