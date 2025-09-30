# campaigns/management/commands/create_test_followups.py
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from campaigns.models import AdRecord, Day1FollowUp, Day2FollowUp
from django.utils import timezone
from datetime import datetime, timedelta
import random

class Command(BaseCommand):
    help = 'Create test data for automatic follow-up system'

    def handle(self, *args, **options):
        self.stdout.write("Creating test data for automatic follow-up system...")
        
        # Get or create test user
        user, created = User.objects.get_or_create(
            username='test_user',
            defaults={
                'email': 'test@example.com',
                'first_name': 'Test',
                'last_name': 'User'
            }
        )
        if created:
            user.set_password('testpass123')
            user.save()
            self.stdout.write(self.style.SUCCESS("Created test user"))
        
        # Business names for variety
        business_names = [
            "Tech Solutions Inc", "Global Marketing", "Food Palace", 
            "Fashion Store", "Auto Services", "Home Decor", "Health Clinic",
            "Education Center", "Travel Agency", "Real Estate Pro"
        ]
        
        # Ad names
        ad_names = [
            "Summer Sale", "New Product Launch", "Special Offer", 
            "Limited Time Deal", "Exclusive Discount", "Premium Service",
            "Business Promotion", "Brand Awareness", "Customer Acquisition"
        ]
        
        # Clear existing test data (optional)
        AdRecord.objects.filter(user=user).delete()
        self.stdout.write("Cleared existing test data")
        
        # Create enquiries for different dates
        today = timezone.now().date()
        
        # 1. Today's enquiries (should appear in main dashboard)
        self.stdout.write("\n1. Creating TODAY's enquiries...")
        for i in range(3):
            try:
                ad = AdRecord.objects.create(
                    user=user,
                    ad_name=f"{random.choice(ad_names)} - Today {i+1}",
                    business_name=random.choice(business_names),
                    mobile_number=f"98{random.randint(10000000, 99999999)}",
                    notes=f"Test enquiry created today - {i+1}",
                    status='enquiry'
                )
                self.stdout.write(f"   - Created: {ad.ad_name}")
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"   - Error creating today's enquiry: {e}"))
        
        # 2. Yesterday's enquiries (should appear in Day 1 Follow-ups)
        self.stdout.write("\n2. Creating YESTERDAY's enquiries...")
        yesterday = today - timedelta(days=1)
        for i in range(4):
            try:
                ad = AdRecord.objects.create(
                    user=user,
                    ad_name=f"{random.choice(ad_names)} - Yesterday {i+1}",
                    business_name=random.choice(business_names),
                    mobile_number=f"97{random.randint(10000000, 99999999)}",
                    notes=f"Test enquiry created yesterday - {i+1}",
                    status='enquiry'
                )
                # Manually set entry_date to yesterday
                ad.entry_date = timezone.make_aware(datetime.combine(yesterday, datetime.min.time()))
                ad.save()
                
                # Create Day1 follow-up for today
                Day1FollowUp.objects.create(
                    ad_record=ad,
                    follow_up_date=today,  # Follow up today for yesterday's enquiries
                    notes="Automatic Day 1 follow-up"
                )
                self.stdout.write(f"   - Created: {ad.ad_name} (Day 1 Follow-up)")
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"   - Error creating yesterday's enquiry: {e}"))
        
        # 3. Day before yesterday's enquiries (should appear in Day 2 Follow-ups)
        self.stdout.write("\n3. Creating DAY BEFORE YESTERDAY's enquiries...")
        day_before_yesterday = today - timedelta(days=2)
        for i in range(3):
            try:
                ad = AdRecord.objects.create(
                    user=user,
                    ad_name=f"{random.choice(ad_names)} - Day Before {i+1}",
                    business_name=random.choice(business_names),
                    mobile_number=f"96{random.randint(10000000, 99999999)}",
                    notes=f"Test enquiry created day before yesterday - {i+1}",
                    status='enquiry'
                )
                # Manually set entry_date to day before yesterday
                ad.entry_date = timezone.make_aware(datetime.combine(day_before_yesterday, datetime.min.time()))
                ad.save()
                
                # Create Day2 follow-up for today
                Day2FollowUp.objects.create(
                    ad_record=ad,
                    follow_up_date=today,  # Follow up today for day before yesterday's enquiries
                    notes="Automatic Day 2 follow-up"
                )
                self.stdout.write(f"   - Created: {ad.ad_name} (Day 2 Follow-up)")
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"   - Error creating day before yesterday's enquiry: {e}"))
        
        # 4. Create some with different statuses to test filtering
        self.stdout.write("\n4. Creating enquiries with different statuses...")
        statuses = ['hold', 'pending', 'active', 'completed']
        for status in statuses:
            try:
                ad = AdRecord.objects.create(
                    user=user,
                    ad_name=f"Test {status.title()} Ad",
                    business_name=random.choice(business_names),
                    mobile_number=f"95{random.randint(10000000, 99999999)}",
                    notes=f"Test {status} status enquiry",
                    status=status
                )
                self.stdout.write(f"   - Created: {ad.ad_name} (Status: {status})")
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"   - Error creating {status} enquiry: {e}"))
        
        # 5. Create some follow-ups with different contact status for testing
        self.stdout.write("\n5. Creating follow-ups with different contact status...")
        
        # Get some Day1 follow-ups and update their status
        day1_followups = Day1FollowUp.objects.filter(ad_record__user=user)[:2]
        if day1_followups:
            # First one: Contacted successfully
            followup1 = day1_followups[0]
            followup1.contacted = True
            followup1.contact_method = "Phone"
            followup1.response = "Customer interested, will call back tomorrow"
            followup1.save()
            self.stdout.write(f"   - Updated: {followup1.ad_record.ad_name} (Contacted: Yes)")
            
            # Second one: Different contact method
            if len(day1_followups) > 1:
                followup2 = day1_followups[1]
                followup2.contacted = True
                followup2.contact_method = "WhatsApp"
                followup2.response = "Sent details, waiting for response"
                followup2.save()
                self.stdout.write(f"   - Updated: {followup2.ad_record.ad_name} (Contacted: Yes)")
        
        # Update one Day2 follow-up
        day2_followups = Day2FollowUp.objects.filter(ad_record__user=user)[:1]
        if day2_followups:
            followup = day2_followups[0]
            followup.contacted = True
            followup.contact_method = "Email"
            followup.response = "Customer requested more information"
            followup.save()
            self.stdout.write(f"   - Updated: {followup.ad_record.ad_name} (Contacted: Yes)")
        
        # Print summary
        self.stdout.write(self.style.SUCCESS(f"\n✅ Test data creation complete!"))
        self.stdout.write(f"📊 Summary:")
        self.stdout.write(f"   - Today's enquiries: {AdRecord.objects.filter(user=user, status='enquiry', entry_date__date=today).count()}")
        self.stdout.write(f"   - Day 1 Follow-ups: {Day1FollowUp.objects.filter(ad_record__user=user).count()}")
        self.stdout.write(f"   - Day 2 Follow-ups: {Day2FollowUp.objects.filter(ad_record__user=user).count()}")
        self.stdout.write(f"   - Total ads: {AdRecord.objects.filter(user=user).count()}")
        
        self.stdout.write(f"\n🔑 Test User Credentials:")
        self.stdout.write(f"   Username: test_user")
        self.stdout.write(f"   Password: testpass123")
        
        self.stdout.write(f"\n📍 What to test:")
        self.stdout.write(f"   1. Login as 'test_user'")
        self.stdout.write(f"   2. Check Dashboard - should see 3 TODAY's enquiries")
        self.stdout.write(f"   3. Check Day 1 Follow-ups - should see 4 YESTERDAY's enquiries") 
        self.stdout.write(f"   4. Check Day 2 Follow-ups - should see 3 DAY BEFORE YESTERDAY's enquiries")
        self.stdout.write(f"   5. Test 'Add to Hold' and 'Add Payment' buttons")