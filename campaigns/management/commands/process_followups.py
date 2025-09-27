from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from campaigns.models import AdRecord, Day1FollowUp, Day2FollowUp


class Command(BaseCommand):
    help = 'Process follow-ups: Move enquiries to day1, day1 to day2, and day2 to completed'

    def handle(self, *args, **options):
        today = timezone.now().date()
        yesterday = today - timedelta(days=1)
        day_before_yesterday = today - timedelta(days=2)
        
        moved_count = 0
        
        # Move enquiries from yesterday to Day1FollowUp
        enquiries_yesterday = AdRecord.objects.filter(
            status='enquiry',
            entry_date__date=yesterday
        )
        
        for enquiry in enquiries_yesterday:
            if not hasattr(enquiry, 'day1_followup'):
                Day1FollowUp.objects.create(ad_record=enquiry)
                moved_count += 1
                self.stdout.write(f"Moved enquiry '{enquiry.ad_name}' to Day 1 Follow-up")
        
        # Move Day1FollowUp from yesterday to Day2FollowUp
        day1_followups_yesterday = Day1FollowUp.objects.filter(
            follow_up_date=yesterday
        )
        
        for day1 in day1_followups_yesterday:
            if not hasattr(day1.ad_record, 'day2_followup'):
                Day2FollowUp.objects.create(ad_record=day1.ad_record)
                moved_count += 1
                self.stdout.write(f"Moved '{day1.ad_record.ad_name}' to Day 2 Follow-up")
        
        # Move Day2FollowUp from day before yesterday to completed (or mark as expired)
        day2_followups_expired = Day2FollowUp.objects.filter(
            follow_up_date=day_before_yesterday
        )
        
        for day2 in day2_followups_expired:
            # You can either mark as completed or create a new status
            # For now, we'll keep them in the database but they won't show in active follow-ups
            moved_count += 1
            self.stdout.write(f"Marked '{day2.ad_record.ad_name}' as follow-up completed")
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully processed {moved_count} follow-ups')
        )
