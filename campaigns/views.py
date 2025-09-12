from django.shortcuts import render, redirect, get_object_or_404 #type: ignore
from django.contrib.auth.decorators import login_required, user_passes_test #type: ignore
from django.contrib import messages #type: ignore
from django.http import JsonResponse #type: ignore
from django.db import transaction #type: ignore
from .models import AdRecord
from .forms import AdRecordForm, PaymentDetailsForm, AdminVerificationForm, ActivateAdForm, AdminCreateUserForm, AdminSetPasswordForm
from django.contrib.auth.models import User #type: ignore
from django.contrib.auth.views import LoginView #type: ignore
from django.contrib.auth import logout #type: ignore


def is_admin(user):
    return user.is_superuser


class AlwaysLoginView(LoginView):
    redirect_authenticated_user = True

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            logout(request)
        return super().dispatch(request, *args, **kwargs)


@login_required
def dashboard(request):
    # Redirect admins to admin dashboard by default
    if request.user.is_superuser:
        return redirect('admin_dashboard')

    show_follow = request.GET.get('view') == 'follow'

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
        'show_follow': show_follow,
    }
    return render(request, 'campaigns/dashboard.html', context)


@login_required
def create_ad(request):
    # Prevent admins from creating enquiries
    if request.user.is_superuser:
        messages.error(request, 'Admins cannot create enquiries. Use the admin dashboard to view records.')
        return redirect('admin_dashboard')
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
    # Prevent admins from adding payment details
    if request.user.is_superuser:
        messages.error(request, 'Admins cannot add payment details for enquiries.')
        return redirect('admin_dashboard')
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
    show_follow = request.GET.get('view') == 'follow'

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

    # Follow-up ads: completed ads that do not have any renewals yet
    follow_up_ads = AdRecord.objects.filter(status='completed', renewals__isnull=True).order_by('-end_date')

    context = {
        'all_ads': all_ads,
        'status_filter': status_filter,
        'status_counts': status_counts,
        'pending_ads': AdRecord.objects.filter(status='pending'),  # Keep for backward compatibility
        'show_follow': show_follow,
        'follow_up_ads': follow_up_ads,
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
    # Prevent admins from renewing enquiries
    if request.user.is_superuser:
        messages.error(request, 'Admins cannot renew enquiries.')
        return redirect('admin_dashboard')

    original_ad = get_object_or_404(AdRecord, id=ad_id, user=request.user, status='completed')

    if request.method == 'POST':
        form = PaymentDetailsForm(request.POST)
        if form.is_valid():
            # Create a new pending ad based on the completed ad with provided payment details
            new_ad = AdRecord(
                user=request.user,
                ad_name=original_ad.ad_name,
                business_name=original_ad.business_name,
                mobile_number=original_ad.mobile_number,
                notes=f"Renewal of {original_ad.ad_name}. Previous notes: {original_ad.notes}",
                renewed_from=original_ad,
                status='pending',
                amount=form.cleaned_data['amount'],
                upi_last_four=form.cleaned_data['upi_last_four']
            )
            new_ad.save()

            messages.success(request, 'Renewal submitted! Waiting for admin verification.')
            return redirect('dashboard')
    else:
        form = PaymentDetailsForm()

    context = {
        'form': form,
        'original_ad': original_ad,
    }
    return render(request, 'campaigns/renew_ad.html', context)


@login_required
@user_passes_test(is_admin)
def admin_users(request):
    # List users and handle creation
    users = User.objects.order_by('username')

    if request.method == 'POST':
        form = AdminCreateUserForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'User created successfully.')
            return redirect('admin_users')
    else:
        form = AdminCreateUserForm()

    context = {
        'users': users,
        'form': form,
    }
    return render(request, 'campaigns/admin_users.html', context)


@login_required
@user_passes_test(is_admin)
def admin_delete_user(request, user_id):
    # Only accept POST deletes and protect against self-deletion of the only superuser
    if request.method != 'POST':
        messages.error(request, 'Invalid request method.')
        return redirect('admin_users')

    user = get_object_or_404(User, id=user_id)

    if user == request.user:
        messages.error(request, 'You cannot delete your own account while logged in.')
        return redirect('admin_users')

    # Prevent deleting the last superuser account
    if user.is_superuser and User.objects.filter(is_superuser=True).count() <= 1:
        messages.error(request, 'Cannot delete the last admin account.')
        return redirect('admin_users')

    user.delete()
    messages.success(request, 'User deleted successfully.')
    return redirect('admin_users')


@login_required
@user_passes_test(is_admin)
def admin_set_password(request, user_id):
    target_user = get_object_or_404(User, id=user_id)
    if request.method == 'POST':
        form = AdminSetPasswordForm(request.POST)
        if form.is_valid():
            new_password = form.cleaned_data['new_password1']
            target_user.set_password(new_password)
            target_user.save()
            messages.success(request, f"Password updated for {target_user.username}.")
            return redirect('admin_users')
    else:
        form = AdminSetPasswordForm()

    return render(request, 'campaigns/admin_set_password.html', {'form': form, 'target_user': target_user})