# test_history.py
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'adsoft.settings')
django.setup()

from django.contrib.auth.models import User
from campaigns.models import AdRecord
from django.utils import timezone
from datetime import datetime, timedelta

def create_test_history():
    print("=== Creating Test Data for Enquiry History ===")
    
    # Get or create user
    user, created = User.objects.get_or_create(
        username='history_test_user',
        defaults={'email': 'history@test.com'}
    )
    if created:
        user.set_password('test123')
        user.save()
        print("✅ Created test user")
    
    # Clear old data
    AdRecord.objects.filter(user=user).delete()
    print("✅ Cleared old data")
    
    today = timezone.now().date()
    
    # Create enquiries for different dates
    dates_data = [
        (today, "TODAY", "Should appear in Dashboard"),
        (today - timedelta(days=1), "YESTERDAY", "Should appear in Day 1 Follow-ups"), 
        (today - timedelta(days=2), "DAY BEFORE", "Should appear in Day 2 Follow-ups"),
        (today - timedelta(days=3), "3 DAYS AGO", "Should appear in Enquiry History"),
        (today - timedelta(days=5), "5 DAYS AGO", "Should appear in Enquiry History"),
        (today - timedelta(days=7), "1 WEEK AGO", "Should appear in Enquiry History"),
        (today - timedelta(days=10), "10 DAYS AGO", "Should appear in Enquiry History"),
    ]
    
    for target_date, label, expected_location in dates_data:
        ad = AdRecord.objects.create(
            user=user,
            ad_name=f"Test Ad - {label}",
            business_name=f"Business {label}",
            mobile_number=f"98{random.randint(10000000, 99999999)}",
            notes=f"Expected: {expected_location}",
            status='enquiry'
        )
        # Set custom entry date
        ad.entry_date = timezone.make_aware(datetime.combine(target_date, datetime.min.time()))
        ad.save()
        print(f"✅ Created: {ad.ad_name}")
    
    # Create some with different statuses for history
    statuses = ['hold', 'completed']
    for status in statuses:
        ad = AdRecord.objects.create(
            user=user,
            ad_name=f"Test {status.title()} - OLD",
            business_name=f"Business {status.title()}",
            mobile_number=f"97{random.randint(10000000, 99999999)}",
            notes=f"Status: {status} - Should appear in History",
            status=status
        )
        # Set to 4 days ago
        old_date = today - timedelta(days=4)
        ad.entry_date = timezone.make_aware(datetime.combine(old_date, datetime.min.time()))
        ad.save()
        print(f"✅ Created: {ad.ad_name}")
    
    print(f"\n📊 Test Data Summary:")
    print(f"   User: {user.username}")
    print(f"   Password: test123")
    print(f"   Total AdRecords: {AdRecord.objects.filter(user=user).count()}")
    
    print(f"\n📍 What to test:")
    print(f"   1. Login as 'history_test_user'")
    print(f"   2. Dashboard - Should see 1 'TODAY' enquiry")
    print(f"   3. Day 1 Follow-ups - Should see 1 'YESTERDAY' enquiry")
    print(f"   4. Day 2 Follow-ups - Should see 1 'DAY BEFORE' enquiry") 
    print(f"   5. Enquiry History - Should see 5 older enquiries (3+ days old + status ones)")

if __name__ == "__main__":
    import random
    create_test_history()