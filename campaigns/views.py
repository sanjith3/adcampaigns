from django.shortcuts import render, redirect, get_object_or_404 #type: ignore
from django.contrib.auth.decorators import login_required, user_passes_test #type: ignore
from django.contrib import messages #type: ignore
from django.http import JsonResponse #type: ignore
from django.db import transaction #type: ignore
from .models import AdRecord
from django.utils import timezone #type: ignore
from django.db.models import Count, Sum #type: ignore
from django.db.models.functions import Coalesce #type: ignore
from datetime import date, timedelta
from .forms import AdRecordForm, PaymentDetailsForm, AdminVerificationForm, ActivateAdForm, AdminCreateUserForm, AdminSetPasswordForm
from django.contrib.auth.models import User #type: ignore
from django.contrib.auth.views import LoginView #type: ignore
from django.contrib.auth import logout #type: ignore
import time

from django.views.decorators.http import require_GET #type: ignore
from django.core.mail import send_mail, EmailMessage #type: ignore



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
    status_filter = request.GET.get('status', 'all')

    user_ads = AdRecord.objects.filter(user=request.user)

    # Separate ads by status for different sections
    enquiries = user_ads.filter(status='enquiry')
    pending_ads = user_ads.filter(status='pending')
    active_ads = user_ads.filter(status='active')
    completed_ads = user_ads.filter(status='completed')
    follow_up_ads = completed_ads.filter(renewals__isnull=True)

    # Daily stats for active campaigns (active today)
    today = timezone.now().date()
    active_today_qs = user_ads.filter(status='active', start_date__lte=today, end_date__gte=today)
    daily_stats = active_today_qs.aggregate(
        count=Count('id'),
        total_amount=Coalesce(Sum('amount'), 0)
    )

    # Date range stats (optional, when start/end provided)
    start_str = request.GET.get('start')
    end_str = request.GET.get('end')
    range_count = None
    range_amount = None
    range_start = None
    range_end = None
    try:
        if start_str:
            range_start = date.fromisoformat(start_str)
        if end_str:
            range_end = date.fromisoformat(end_str)
    except ValueError:
        range_start = None
        range_end = None

    if range_start and range_end:
        range_qs = user_ads.filter(
            status='active',
            start_date__gte=range_start,
            end_date__lte=range_end
        )
        range_stats = range_qs.aggregate(
            count=Count('id'),
            total_amount=Coalesce(Sum('amount'), 0)
        )
        range_count = range_stats['count']
        range_amount = range_stats['total_amount']

    context = {
        'enquiries': enquiries,
        'pending_ads': pending_ads,
        'active_ads': active_ads,
        'completed_ads': completed_ads,
        'follow_up_ads': follow_up_ads,
        'status_filter': status_filter,
        'show_follow': show_follow,
        'stats_active_today_count': daily_stats['count'],
        'stats_active_today_amount': daily_stats['total_amount'],
        'stats_range_count': range_count,
        'stats_range_amount': range_amount,
        'stats_range_start': start_str or '',
        'stats_range_end': end_str or '',
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
    user_filter = request.GET.get('user')  # user id as string or None
    show_follow = request.GET.get('view') == 'follow'
    history_start = request.GET.get('history_start')
    history_end = request.GET.get('history_end')

    all_ads = AdRecord.objects.all().order_by('-entry_date')

    if status_filter != 'all':
        all_ads = all_ads.filter(status=status_filter)

    # Optional user filter
    selected_user = None
    if user_filter:
        try:
            selected_user = User.objects.get(id=int(user_filter))
            # Do not allow filtering by admin accounts
            if not selected_user.is_superuser:
                all_ads = all_ads.filter(user=selected_user)
            else:
                selected_user = None
        except (User.DoesNotExist, ValueError):
            selected_user = None

    # Sum amount for current filtered ads (used for active/completed views)
    filtered_totals = all_ads.aggregate(total_amount=Coalesce(Sum('amount'), 0))
    filtered_total_amount = filtered_totals['total_amount']

    # Daily stats for active campaigns (active today)
    today = timezone.now().date()
    active_today_qs = AdRecord.objects.filter(status='active', start_date__lte=today, end_date__gte=today)
    daily_stats = active_today_qs.aggregate(
        count=Count('id'),
        total_amount=Coalesce(Sum('amount'), 0)
    )

    # Date range stats (optional, when start/end provided)
    start_str = request.GET.get('start')
    end_str = request.GET.get('end')
    range_count = None
    range_amount = None
    range_start = None
    range_end = None
    try:
        if start_str:
            range_start = date.fromisoformat(start_str)
        if end_str:
            range_end = date.fromisoformat(end_str)
    except ValueError:
        range_start = None
        range_end = None

    if range_start and range_end:
        range_qs = AdRecord.objects.filter(
            status='active',
            start_date__gte=range_start,
            end_date__lte=range_end
        )
        range_stats = range_qs.aggregate(
            count=Count('id'),
            total_amount=Coalesce(Sum('amount'), 0)
        )
        range_count = range_stats['count']
        range_amount = range_stats['total_amount']

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

    # Completed history filter
    completed_history = None
    history_start_date = None
    history_end_date = None
    try:
        if history_start:
            history_start_date = date.fromisoformat(history_start)
        if history_end:
            history_end_date = date.fromisoformat(history_end)
    except ValueError:
        history_start_date = None
        history_end_date = None

    # Quick filter for yesterday/before yesterday - show completed campaigns that finished on those days
    quick_filter = request.GET.get('quick_filter')
    completed_history = None
    if quick_filter == 'yesterday':
        yesterday = today - timedelta(days=1)
        completed_history = AdRecord.objects.filter(
            status='completed',
            end_date=yesterday
        ).order_by('-end_date')
    elif quick_filter == 'before_yesterday':
        before_yesterday = today - timedelta(days=2)
        completed_history = AdRecord.objects.filter(
            status='completed',
            end_date=before_yesterday
        ).order_by('-end_date')
    elif history_start_date and history_end_date:
        completed_history = AdRecord.objects.filter(
            status='completed',
            end_date__gte=history_start_date,
            end_date__lte=history_end_date
        ).order_by('-end_date')

    # Users list for filter dropdown
    # Exclude admin accounts from filter list
    users_for_filter = User.objects.filter(is_superuser=False).order_by('username')

    context = {
        'all_ads': all_ads,
        'status_filter': status_filter,
        'user_filter': user_filter or '',
        'selected_user': selected_user,
        'users_for_filter': users_for_filter,
        'status_counts': status_counts,
        'pending_ads': AdRecord.objects.filter(status='pending'),  # Keep for backward compatibility
        'show_follow': show_follow,
        'follow_up_ads': follow_up_ads,
        'stats_active_today_count': daily_stats['count'],
        'stats_active_today_amount': daily_stats['total_amount'],
        'stats_range_count': range_count,
        'stats_range_amount': range_amount,
        'stats_range_start': start_str or '',
        'stats_range_end': end_str or '',
        'completed_history': completed_history,
        'history_start': history_start or '',
        'history_end': history_end or '',
        'quick_filter': quick_filter,
        'filtered_total_amount': filtered_total_amount,
    }
    return render(request, 'campaigns/admin_dashboard.html', context)


@login_required
@user_passes_test(is_admin)
def poll_admin_status(request):
    """Long-poll endpoint for admin dashboard counters.

    Compares a lightweight signature of ads state (counts by status + latest id)
    and waits up to 25 seconds for a change. Returns immediately if a change is
    already detected.
    """
    timeout_seconds = 25

    def get_counts_and_signature():
        total = AdRecord.objects.count()
        enquiry = AdRecord.objects.filter(status='enquiry').count()
        pending = AdRecord.objects.filter(status='pending').count()
        active = AdRecord.objects.filter(status='active').count()
        completed = AdRecord.objects.filter(status='completed').count()
        latest = AdRecord.objects.order_by('-id').values_list('id', flat=True).first() or 0
        signature = f"{total}:{enquiry}:{pending}:{active}:{completed}:{latest}"
        counts = {
            'total': total,
            'enquiry': enquiry,
            'pending': pending,
            'active': active,
            'completed': completed,
        }
        return counts, signature

    client_token = request.GET.get('token') or ''
    start_time = time.time()
    counts, current_sig = get_counts_and_signature()

    # If client has a token and it doesn't match, state already changed
    if client_token and client_token != current_sig:
        return JsonResponse({
            'changed': True,
            'token': current_sig,
            'counts': counts,
        })

    # Otherwise, wait for changes until timeout
    while time.time() - start_time < timeout_seconds:
        time.sleep(1)
        new_counts, new_sig = get_counts_and_signature()
        if new_sig != current_sig:
            return JsonResponse({
                'changed': True,
                'token': new_sig,
                'counts': new_counts,
            })

    # Timeout reached, no changes
    return JsonResponse({
        'changed': False,
        'token': current_sig,
        'counts': counts,
    })


@login_required
def poll_user_status(request):
    """Long-poll endpoint for a user's own dashboard.

    Tracks only the current user's ads and returns when anything changes
    (counts by status or latest id).
    """
    timeout_seconds = 25

    def get_counts_and_signature(user):
        user_ads = AdRecord.objects.filter(user=user)
        total = user_ads.count()
        enquiry = user_ads.filter(status='enquiry').count()
        pending = user_ads.filter(status='pending').count()
        active = user_ads.filter(status='active').count()
        completed = user_ads.filter(status='completed').count()
        latest = user_ads.order_by('-id').values_list('id', flat=True).first() or 0
        signature = f"{total}:{enquiry}:{pending}:{active}:{completed}:{latest}"
        counts = {
            'total': total,
            'enquiry': enquiry,
            'pending': pending,
            'active': active,
            'completed': completed,
        }
        return counts, signature

    client_token = request.GET.get('token') or ''
    start_time = time.time()
    counts, current_sig = get_counts_and_signature(request.user)

    if client_token and client_token != current_sig:
        return JsonResponse({
            'changed': True,
            'token': current_sig,
            'counts': counts,
        })

    while time.time() - start_time < timeout_seconds:
        time.sleep(1)
        new_counts, new_sig = get_counts_and_signature(request.user)
        if new_sig != current_sig:
            return JsonResponse({
                'changed': True,
                'token': new_sig,
                'counts': new_counts,
            })

    return JsonResponse({
        'changed': False,
        'token': current_sig,
        'counts': counts,
    })

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


@login_required
@require_GET
def notifications(request):
    """Return lightweight counts for follow-up badges.

    - For admins: number of completed ads without renewals (global)
    - For users: number of their own completed ads without renewals
    """
    if request.user.is_superuser:
        follow_count = AdRecord.objects.filter(status='completed', renewals__isnull=True).count()
    else:
        follow_count = AdRecord.objects.filter(user=request.user, status='completed', renewals__isnull=True).count()

    return JsonResponse({
        'follow_up_count': follow_count,
        'is_admin': request.user.is_superuser,
    })


@login_required
@user_passes_test(is_admin)
@require_GET
def admin_generate_report(request):
    """Admin-only: email today's per-user enquiry and active counts, plus totals.

    - Recipient: fixed admin email
    - Content: For each non-admin user: enquiries created today, active today
      Then overall totals across all users
    """
    today = timezone.now().date()

    # Collect users (exclude superusers)
    users = User.objects.filter(is_superuser=False).order_by('username')

    lines = [f"Daily Report - {today:%b %d, %Y}"]
    total_enquiries = 0
    total_active = 0

    for u in users:
        user_ads = AdRecord.objects.filter(user=u)
        enquiries_today = user_ads.filter(status='enquiry', entry_date__date=today).count()
        active_today = user_ads.filter(status='active', start_date__lte=today, end_date__gte=today).count()
        total_enquiries += enquiries_today
        total_active += active_today
        lines.append(
            f"- {u.get_full_name() or u.username}: enquiries today {enquiries_today}, active today {active_today}"
        )

    lines.append("")
    lines.append(f"TOTAL enquiries today: {total_enquiries}")
    lines.append(f"TOTAL active today: {total_active}")

    subject = f"AdSoft Daily Report - {today.isoformat()}"
    body = "\n".join(lines)

    recipient = 'sanjithjin@gmail.com'
    from django.conf import settings  # type: ignore
    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', None)
    try:
        email = EmailMessage(
            subject=subject,
            body=body,
            from_email=from_email,
            to=[recipient],
        )
        email.send(fail_silently=False)
        return JsonResponse({'ok': True, 'message': 'Report generated and sent'})
    except Exception as e:
        return JsonResponse({'ok': False, 'error': str(e)}, status=500)


@login_required
@user_passes_test(is_admin)
@require_GET
def admin_ad_history(request, ad_id):
    """Return the client/ad history HTML snippet for display in modal."""
    ad = get_object_or_404(AdRecord, id=ad_id)

    # Group by business or by user depending on availability
    history_qs = AdRecord.objects.filter(business_name=ad.business_name).order_by('-entry_date')

    return render(request, 'campaigns/_ad_history.html', {
        'subject_ad': ad,
        'history_ads': history_qs,
    })