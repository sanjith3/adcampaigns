from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse
from django.db import transaction
from .models import AdRecord
from .forms import AdRecordForm, PaymentDetailsForm, AdminVerificationForm, ActivateAdForm


def is_admin(user):
    return user.is_superuser


@login_required
def dashboard(request):
    user_ads = AdRecord.objects.filter(user=request.user)

    # Separate ads by status for different sections
    enquiries = user_ads.filter(status='enquiry')
    pending_ads = user_ads.filter(status='pending')
    active_ads = user_ads.filter(status='active')
    completed_ads = user_ads.filter(status='completed')
    follow_up_ads = completed_ads.filter(renewals__isnull=True)

    context = {
        'enquiries': enquiries,
        'pending_ads': pending_ads,
        'active_ads': active_ads,
        'completed_ads': completed_ads,
        'follow_up_ads': follow_up_ads,
    }
    return render(request, 'campaigns/dashboard.html', context)


@login_required
def create_ad(request):
    if request.method == 'POST':
        form = AdRecordForm(request.POST)
        if form.is_valid():
            ad = form.save(commit=False)
            ad.user = request.user
            ad.save()
            messages.success(request, 'Ad enquiry created successfully!')
            return redirect('dashboard')
    else:
        form = AdRecordForm()

    return render(request, 'campaigns/create_ad.html', {'form': form})


@login_required
def add_payment_details(request, ad_id):
    ad = get_object_or_404(AdRecord, id=ad_id, user=request.user, status='enquiry')

    if request.method == 'POST':
        form = PaymentDetailsForm(request.POST, instance=ad)
        if form.is_valid():
            ad = form.save(commit=False)
            ad.status = 'pending'
            ad.save()
            messages.success(request, 'Payment details submitted! Waiting for admin verification.')
            return redirect('dashboard')
    else:
        form = PaymentDetailsForm(instance=ad)

    return render(request, 'campaigns/add_payment.html', {'form': form, 'ad': ad})


@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    # Get all ads with filters
    status_filter = request.GET.get('status', 'all')

    all_ads = AdRecord.objects.all().order_by('-entry_date')

    if status_filter != 'all':
        all_ads = all_ads.filter(status=status_filter)

    # Count by status for filters
    status_counts = {
        'all': AdRecord.objects.count(),
        'enquiry': AdRecord.objects.filter(status='enquiry').count(),
        'pending': AdRecord.objects.filter(status='pending').count(),
        'active': AdRecord.objects.filter(status='active').count(),
        'completed': AdRecord.objects.filter(status='completed').count(),
    }

    context = {
        'all_ads': all_ads,
        'status_filter': status_filter,
        'status_counts': status_counts,
        'pending_ads': AdRecord.objects.filter(status='pending'),  # Keep for backward compatibility
    }
    return render(request, 'campaigns/admin_dashboard.html', context)

@login_required
@user_passes_test(is_admin)
def verify_payment(request, ad_id):
    ad = get_object_or_404(AdRecord, id=ad_id, status='pending')

    if request.method == 'POST':
        form = AdminVerificationForm(request.POST)
        if form.is_valid():
            full_upi_id = form.cleaned_data['full_upi_id']
            last_four_provided = ad.upi_last_four

            # Verify last 4 digits match
            if full_upi_id[-4:] == last_four_provided:
                ad.admin_upi_id = full_upi_id
                ad.save()
                messages.success(request, 'Payment verified successfully!')
                return redirect('activate_ad', ad_id=ad.id)
            else:
                messages.error(request, 'Last 4 digits do not match. Please check the UPI ID.')
    else:
        form = AdminVerificationForm()

    return render(request, 'campaigns/verify_payment.html', {'form': form, 'ad': ad})


@login_required
@user_passes_test(is_admin)
def activate_ad(request, ad_id):
    ad = get_object_or_404(AdRecord, id=ad_id, status='pending')

    if not ad.admin_upi_id:
        messages.error(request, 'Payment must be verified first.')
        return redirect('admin_dashboard')

    if request.method == 'POST':
        form = ActivateAdForm(request.POST, instance=ad)
        if form.is_valid():
            ad = form.save(commit=False)
            ad.status = 'active'
            ad.save()
            messages.success(request, 'Ad activated successfully!')
            return redirect('admin_dashboard')
    else:
        form = ActivateAdForm(instance=ad)

    return render(request, 'campaigns/activate_ad.html', {'form': form, 'ad': ad})


@login_required
def renew_ad(request, ad_id):
    original_ad = get_object_or_404(AdRecord, id=ad_id, user=request.user, status='completed')

    # Create a new enquiry based on the completed ad
    new_ad = AdRecord(
        user=request.user,
        ad_name=original_ad.ad_name,
        business_name=original_ad.business_name,
        notes=f"Renewal of {original_ad.ad_name}. Previous notes: {original_ad.notes}",
        renewed_from=original_ad
    )
    new_ad.save()

    messages.success(request, 'Ad renewed successfully! New enquiry created.')
    return redirect('dashboard')