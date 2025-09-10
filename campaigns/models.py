from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta


class AdRecord(models.Model):
    STATUS_CHOICES = [
        ('enquiry', 'Enquiry'),
        ('pending', 'Pending Payment Verification'),
        ('active', 'Active'),
        ('completed', 'Completed'),
    ]

    AMOUNT_CHOICES = [
        (1000, '1000 INR (5 days)'),
        (2000, '2000 INR (10 days)'),
        (4000, '4000 INR (20 days)'),
        (6000, '6000 INR (30 days)'),
    ]

    AMOUNT_DAYS_MAPPING = {
        1000: 5,
        2000: 10,
        4000: 20,
        6000: 30
    }

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ad_records')
    ad_name = models.CharField(max_length=200)
    business_name = models.CharField(max_length=200)
    notes = models.TextField(blank=True)

    entry_date = models.DateTimeField(auto_now_add=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)

    amount = models.IntegerField(choices=AMOUNT_CHOICES, null=True, blank=True)
    upi_last_four = models.CharField(max_length=4, blank=True)
    admin_upi_id = models.CharField(max_length=50, blank=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='enquiry')
    renewed_from = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='renewals')

    class Meta:
        ordering = ['-entry_date']

    def __str__(self):
        return f"{self.ad_name} - {self.business_name}"

    def save(self, *args, **kwargs):
        # Auto-calculate end date when start_date and amount are set
        if self.start_date and self.amount and self.status == 'active':
            days = self.AMOUNT_DAYS_MAPPING.get(self.amount, 0)
            self.end_date = self.start_date + timedelta(days=days)

        # Auto-complete if end date has passed
        if self.status == 'active' and self.end_date and self.end_date < timezone.now().date():
            self.status = 'completed'

        super().save(*args, **kwargs)

    def get_status_display_class(self):
        status_classes = {
            'enquiry': 'secondary',
            'pending': 'warning',
            'active': 'success',
            'completed': 'info'
        }
        return status_classes.get(self.status, 'secondary')