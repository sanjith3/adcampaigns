from django.db import models #type: ignore
from django.contrib.auth.models import User #type: ignore
from django.utils import timezone #type: ignore
from datetime import timedelta

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    target_amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0,
        verbose_name="Monthly Target (₹)"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - Target: ₹{self.target_amount}"

    class Meta:
        verbose_name = "User Profile"
        verbose_name_plural = "User Profiles"


class AdRecord(models.Model):
    STATUS_CHOICES = [
        ('enquiry', 'Enquiry'),
        ('hold', 'On Hold'),
        ('pending', 'Pending Payment Verification'),
        ('active', 'Active'),
        ('completed', 'Completed'),
    ]

    AMOUNT_CHOICES = [
        (1000, '1000 INR (5 days)'),
        (2000, '2000 INR (10 days)'),
        (4000, '4000 INR (20 days)'),
        (6000, '6000 INR (30 days)'),
        (0, 'Other (custom)'),
    ]

    AMOUNT_DAYS_MAPPING = {
        1000: 5,
        2000: 10,
        4000: 20,
        6000: 30
    }

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='ad_records')
    ad_name = models.CharField(max_length=200)
    business_name = models.CharField(max_length=200)
    mobile_number = models.CharField(max_length=10, blank=True)
    notes = models.TextField(blank=True)

    entry_date = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)

    amount = models.IntegerField(choices=AMOUNT_CHOICES, null=True, blank=True)
    upi_last_four = models.CharField(max_length=4, blank=True)
    admin_upi_id = models.CharField(max_length=50, blank=True)
    # Custom pricing support
    custom_amount = models.IntegerField(null=True, blank=True)
    custom_days = models.IntegerField(null=True, blank=True)

    # Hold details
    hold_reason = models.TextField(blank=True)
    hold_until = models.DateField(null=True, blank=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='enquiry')
    renewed_from = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='renewals')
    
    # ADD THE MISSING FIELD HERE ⬇️⬇️⬇️
    # follow_up_completed = models.BooleanField(default=False, null=True, blank=True)

    class Meta:
        ordering = ['-entry_date']

    def __str__(self):
        return f"{self.ad_name} - {self.business_name}"

    def save(self, *args, **kwargs):
        # Auto-calculate end date when start_date and amount/custom_days are set
        days = 0
        if self.amount in self.AMOUNT_DAYS_MAPPING:
            days = self.AMOUNT_DAYS_MAPPING.get(self.amount, 0)
        elif self.custom_days:
            days = int(self.custom_days or 0)
        if self.start_date and days:
            self.end_date = self.start_date + timedelta(days=days)

        # Auto-complete if end date has passed (only for active)
        if self.status == 'active' and self.end_date and self.end_date < timezone.now().date():
            self.status = 'completed'

        # If on hold and a hold_until date is set and passed, move back to enquiry
        if self.status == 'hold' and self.hold_until and self.hold_until < timezone.now().date():
            self.status = 'enquiry'

        super().save(*args, **kwargs)

    def get_status_display_class(self):
        status_classes = {
            'enquiry': 'secondary',
            'hold': 'dark',
            'pending': 'warning',
            'active': 'success',
            'completed': 'info'
        }
        return status_classes.get(self.status, 'secondary')

    def get_duration_days(self):
        """Get the duration in days based on amount"""
        return self.AMOUNT_DAYS_MAPPING.get(self.amount, 0)


class Day1FollowUp(models.Model):
    """First day follow-up for enquiries"""
    ad_record = models.OneToOneField(AdRecord, on_delete=models.CASCADE, related_name='day1_followup')
    follow_up_date = models.DateField()  # REMOVED auto_now_add=True
    notes = models.TextField(blank=True)
    contacted = models.BooleanField(default=False)
    contact_method = models.CharField(max_length=50, blank=True)
    response = models.TextField(blank=True)
    # REMOVED created_at field - we don't really need it
    
    class Meta:
        ordering = ['follow_up_date']
    
    def __str__(self):
        return f"Day 1 Follow-up: {self.ad_record.ad_name} ({self.follow_up_date})"

class Day2FollowUp(models.Model):
    """Second day follow-up for enquiries"""
    ad_record = models.OneToOneField(AdRecord, on_delete=models.CASCADE, related_name='day2_followup')
    follow_up_date = models.DateField()  # REMOVED auto_now_add=True
    notes = models.TextField(blank=True)
    contacted = models.BooleanField(default=False)
    contact_method = models.CharField(max_length=50, blank=True)
    response = models.TextField(blank=True)
    # REMOVED created_at field - we don't really need it
    
    class Meta:
        ordering = ['follow_up_date']
    
    def __str__(self):
        return f"Day 2 Follow-up: {self.ad_record.ad_name} ({self.follow_up_date})"


# Add signals to automatically create UserProfile when User is created
from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, 'profile'):
        instance.profile.save()


# NEW: Signal to automatically create follow-ups when AdRecord is created
@receiver(post_save, sender=AdRecord)
def create_automatic_followups(sender, instance, created, **kwargs):
    if created and instance.status == 'enquiry':
        today = timezone.now().date()
        
        try:
            # Create Day1 follow-up for tomorrow
            tomorrow = today + timedelta(days=1)
            day1_followup, day1_created = Day1FollowUp.objects.get_or_create(
                ad_record=instance,
                defaults={
                    'follow_up_date': tomorrow,
                    'notes': 'Automatic Day 1 follow-up created'
                }
            )
            if day1_created:
                print(f"Created Day1 follow-up for ad_record {instance.id}")
            else:
                print(f"Day1 follow-up already exists for ad_record {instance.id}")
                
        except Exception as e:
            print(f"Error creating Day1 follow-up for ad_record {instance.id}: {e}")
        
        try:
            # Create Day2 follow-up for day after tomorrow
            day_after_tomorrow = today + timedelta(days=2)
            day2_followup, day2_created = Day2FollowUp.objects.get_or_create(
                ad_record=instance,
                defaults={
                    'follow_up_date': day_after_tomorrow,
                    'notes': 'Automatic Day 2 follow-up created'
                }
            )
            if day2_created:
                print(f"Created Day2 follow-up for ad_record {instance.id}")
            else:
                print(f"Day2 follow-up already exists for ad_record {instance.id}")
                
        except Exception as e:
            print(f"Error creating Day2 follow-up for ad_record {instance.id}: {e}")