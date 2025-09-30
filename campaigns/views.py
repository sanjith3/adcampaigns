from django.shortcuts import render, redirect, get_object_or_404 #type: ignore
from django.contrib.auth.decorators import login_required, user_passes_test #type: ignore
from django.contrib import messages #type: ignore
from django.http import JsonResponse #type: ignore
from django.db import transaction #type: ignore
from .models import AdRecord, Day1FollowUp, Day2FollowUp,UserProfile  
from django.utils import timezone #type: ignore
from django.db.models import Count, Sum,Q, Max #type: ignore
from django.db.models.functions import Coalesce #type: ignore
from datetime import date, timedelta
from .forms import AdRecordForm, PaymentDetailsForm, AdminVerificationForm, ActivateAdForm, AdminCreateUserForm, AdminSetPasswordForm, HoldDetailsForm, EditEnquiryForm, EditHoldForm, SetTargetForm
from django.contrib.auth.models import User #type: ignore
from django.contrib.auth.views import LoginView #type: ignore
from django.contrib.auth import logout #type: ignore
import time
from django.views.decorators.http import require_GET #type: ignore
from django.core.mail import send_mail, EmailMessage #type: ignore
from django.views.decorators.cache import never_cache #type: ignore
import os
from datetime import date,datetime #type:ignore

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
    if request.user.is_superuser:
        return redirect('admin_dashboard')

    show_follow = request.GET.get('view') == 'follow'
    status_filter = request.GET.get('status', 'all')

    user_ads = AdRecord.objects.filter(user=request.user)

    # Get today's date for filtering
    today = timezone.now().date()
    
    # Today's enquiries only
    enquiries = user_ads.filter(status='enquiry', entry_date__date=today)
    hold_ads = user_ads.filter(status='hold')
    pending_ads = user_ads.filter(status='pending')
    active_ads = user_ads.filter(status='active')
    completed_ads = user_ads.filter(status='completed')
    follow_up_ads = completed_ads.filter(renewals__isnull=True)

    stats_range_start = request.GET.get('start')
    stats_range_end = request.GET.get('end')
    
    stats_range_count = None
    stats_range_amount = 0
    range_ads = user_ads

    if stats_range_start and stats_range_end:
        try:
            start_date = datetime.strptime(stats_range_start, '%Y-%m-%d').date()
            end_date = datetime.strptime(stats_range_end, '%Y-%m-%d').date()
            range_ads = user_ads.filter(
                start_date__gte=start_date,
                start_date__lte=end_date
            )
            
            range_stats = range_ads.aggregate(
                count=Count('id'),
                total_amount=Coalesce(Sum('amount'), 0)
            )
            stats_range_count = range_stats['count']
            stats_range_amount = range_stats['total_amount']
            
        except ValueError:
            pass

    now = timezone.now()
    month_start = date(now.year, now.month, 1)
    monthly_stats = user_ads.filter(
        start_date__gte=month_start,
        start_date__lte=now
    ).aggregate(
        count=Count('id'),
        total_amount=Coalesce(Sum('amount'), 0)
    )

    try:
        user_profile = UserProfile.objects.get(user=request.user)
        target_amount = user_profile.target_amount
    except UserProfile.DoesNotExist:
        target_amount = 0

    achieved_amount = monthly_stats['total_amount'] or 0
    remaining_amount = max(0, target_amount - achieved_amount)
    
    if target_amount > 0:
        progress_percentage = min(100, (achieved_amount / target_amount) * 100)
    else:
        progress_percentage = 0

    target_progress = {
        'target': target_amount,
        'achieved': achieved_amount,
        'remaining': remaining_amount,
        'progress_percentage': progress_percentage
    }

    context = {
        'enquiries': enquiries,
        'hold_ads': hold_ads,
        'pending_ads': pending_ads,
        'active_ads': active_ads,
        'completed_ads': completed_ads,
        'follow_up_ads': follow_up_ads,
        'status_filter': status_filter,
        'show_follow': show_follow,
        'stats_active_today_count': monthly_stats['count'],
        'stats_active_today_amount': monthly_stats['total_amount'],
        'target_progress': target_progress,
        'stats_range_start': stats_range_start,
        'stats_range_end': stats_range_end,
        'stats_range_count': stats_range_count,
        'stats_range_amount': stats_range_amount,
    }
    return render(request, 'campaigns/dashboard.html', context)


@login_required
def create_ad(request):
    if not request.user.is_authenticated:
        messages.error(request, 'You must be logged in to create an enquiry.')
        return redirect('login')
    
    if request.user.is_superuser:
        messages.error(request, 'Admins cannot create enquiries. Use the admin dashboard to view records.')
        return redirect('admin_dashboard')
    
    if request.method == 'POST':
        form = AdRecordForm(request.POST)
        if form.is_valid():
            ad = form.save(commit=False)
            ad.user = request.user
            ad.save()
            
            # Automatically create Day1 follow-up for tomorrow
            tomorrow = timezone.now().date() + timedelta(days=1)
            Day1FollowUp.objects.create(ad_record=ad, follow_up_date=tomorrow)
            
            messages.success(request, 'Ad enquiry created successfully!')
            return redirect('dashboard')
        else:
            messages.error(request, f'Form validation failed: {form.errors}')
    else:
        form = AdRecordForm()

    return render(request, 'campaigns/create_ad.html', {'form': form})


@login_required
def add_payment_details(request, ad_id):
    if request.user.is_superuser:
        messages.error(request, 'Admins cannot add payment details for enquiries.')
        return redirect('admin_dashboard')
    ad = get_object_or_404(AdRecord, id=ad_id, user=request.user)
    if ad.status not in ['enquiry', 'hold']:
        messages.error(request, 'Payment can only be added for enquiries or holds.')
        return redirect('dashboard')

    if request.method == 'POST':
        form = PaymentDetailsForm(request.POST, instance=ad)
        if form.is_valid():
            ad = form.save(commit=False)
            predefined_mapping_amounts = set(AdRecord.AMOUNT_DAYS_MAPPING.keys())
            if ad.amount == 0 or ad.amount not in predefined_mapping_amounts:
                ad.custom_amount = form.cleaned_data.get('custom_amount')
                ad.custom_days = form.cleaned_data.get('custom_days')
                # Store amount field as entered custom amount for visibility
                ad.amount = ad.custom_amount
            else:
                ad.custom_amount = None
                ad.custom_days = None
            ad.status = 'pending'
            ad.save()
            messages.success(request, 'Payment details submitted! Waiting for admin verification.')
            return redirect('dashboard')
    else:
        form = PaymentDetailsForm(instance=ad)

    return render(request, 'campaigns/add_payment.html', {'form': form, 'ad': ad})


@login_required
def add_hold(request, ad_id):
    if request.user.is_superuser:
        messages.error(request, 'Admins cannot change hold for user enquiries here.')
        return redirect('admin_dashboard')
    ad = get_object_or_404(AdRecord, id=ad_id, user=request.user)
    if ad.status not in ['enquiry', 'hold']:
        messages.error(request, 'Only enquiries or existing holds can be updated.')
        return redirect('dashboard')

    if request.method == 'POST':
        form = HoldDetailsForm(request.POST, instance=ad)
        if form.is_valid():
            ad = form.save(commit=False)
            ad.status = 'hold'
            ad.save()
            messages.success(request, 'Enquiry placed on hold.')
            return redirect('dashboard')
    else:
        form = HoldDetailsForm(instance=ad)

    return render(request, 'campaigns/add_hold.html', {'form': form, 'ad': ad})


@login_required
def remove_hold(request, ad_id):
    if request.user.is_superuser:
        messages.error(request, 'Admins cannot change hold for user enquiries here.')
        return redirect('admin_dashboard')
    ad = get_object_or_404(AdRecord, id=ad_id, user=request.user, status='hold')

    if request.method == 'POST':
        ad.status = 'enquiry'
        ad.hold_reason = ''
        ad.hold_until = None
        ad.save()
        messages.success(request, 'Hold removed. Enquiry returned to queue.')
        return redirect('dashboard')

    return redirect('dashboard')


@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    status_filter = request.GET.get('status', 'all')
    user_filter = request.GET.get('user')
    show_follow = request.GET.get('view') == 'follow'
    history_start = request.GET.get('history_start')
    history_end = request.GET.get('history_end')

    all_ads = AdRecord.objects.all().order_by('-entry_date')

    if status_filter != 'all':
        all_ads = all_ads.filter(status=status_filter)

    selected_user = None
    if user_filter:
        try:
            selected_user = User.objects.get(id=int(user_filter))
            if not selected_user.is_superuser:
                all_ads = all_ads.filter(user=selected_user)
            else:
                selected_user = None
        except (User.DoesNotExist, ValueError):
            selected_user = None

    filtered_totals = all_ads.aggregate(total_amount=Coalesce(Sum('amount'), 0))
    filtered_total_amount = filtered_totals['total_amount']

    today = timezone.now().date()
    active_today_qs = AdRecord.objects.filter(status='active', start_date__lte=today, end_date__gte=today)
    daily_stats = active_today_qs.aggregate(
        count=Count('id'),
        total_amount=Coalesce(Sum('amount'), 0)
    )

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
        if selected_user:
            range_qs = range_qs.filter(user=selected_user)
        range_stats = range_qs.aggregate(
            count=Count('id'),
            total_amount=Coalesce(Sum('amount'), 0)
        )
        range_count = range_stats['count']
        range_amount = range_stats['total_amount']

        if status_filter == 'active':
            all_ads = all_ads.filter(
                start_date__gte=range_start,
                end_date__lte=range_end
            )
            filtered_total_amount = all_ads.aggregate(
                total_amount=Coalesce(Sum('amount'), 0)
            )['total_amount']

    status_counts = {
        'all': AdRecord.objects.count(),
        'enquiry': AdRecord.objects.filter(status='enquiry').count(),
        'hold': AdRecord.objects.filter(status='hold').count(),
        'pending': AdRecord.objects.filter(status='pending').count(),
        'active': AdRecord.objects.filter(status='active').count(),
        'completed': AdRecord.objects.filter(status='completed').count(),
    }

    follow_up_ads = AdRecord.objects.filter(status='completed', renewals__isnull=True).order_by('-end_date')

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

    quick_filter = request.GET.get('quick_filter')
    completed_history = None
    if quick_filter == 'yesterday':
        yesterday = today - timedelta(days=1)
        completed_history = AdRecord.objects.filter(
            status='completed',
            end_date=yesterday
        )
        if selected_user:
            completed_history = completed_history.filter(user=selected_user)
        completed_history = completed_history.order_by('-end_date')
    elif quick_filter == 'before_yesterday':
        before_yesterday = today - timedelta(days=2)
        completed_history = AdRecord.objects.filter(
            status='completed',
            end_date=before_yesterday
        )
        if selected_user:
            completed_history = completed_history.filter(user=selected_user)
        completed_history = completed_history.order_by('-end_date')
    elif history_start_date and history_end_date:
        completed_history = AdRecord.objects.filter(
            status='completed',
            end_date__gte=history_start_date,
            end_date__lte=history_end_date
        )
        if selected_user:
            completed_history = completed_history.filter(user=selected_user)
        completed_history = completed_history.order_by('-end_date')

    users_for_filter = User.objects.filter(is_superuser=False).order_by('username')

    context = {
        'all_ads': all_ads,
        'status_filter': status_filter,
        'user_filter': user_filter or '',
        'selected_user': selected_user,
        'users_for_filter': users_for_filter,
        'status_counts': status_counts,
        'pending_ads': AdRecord.objects.filter(status='pending'), 
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



def get_counts_and_signature(queryset):
    agg = queryset.aggregate(
        total=Count('id'),
        enquiry=Count('id', filter=Q(status='enquiry')),
        hold=Count('id', filter=Q(status='hold')),
        pending=Count('id', filter=Q(status='pending')),
        active=Count('id', filter=Q(status='active')),
        completed=Count('id', filter=Q(status='completed')),
        latest=Max('id'),
        last_update=Max('updated_at'),
    )
    counts = {
        'total': agg['total'],
        'enquiry': agg['enquiry'],
        'hold': agg['hold'],
        'pending': agg['pending'],
        'active': agg['active'],
        'completed': agg['completed'],
    }
    signature = (
        f"{agg['total']}:{agg['enquiry']}:{agg['hold']}:{agg['pending']}:" \
        f"{agg['active']}:{agg['completed']}:{agg['latest'] or 0}:" \
        f"{agg['last_update'].timestamp() if agg['last_update'] else 0}"
    )
    return counts, signature


@never_cache
@login_required
@user_passes_test(lambda u: u.is_staff)
def poll_admin_status(request):
    
    timeout_seconds = 15 
    client_token = request.GET.get('token', '')
    start_time = time.time()

    counts, current_sig = get_counts_and_signature(AdRecord.objects.all())
    if client_token and client_token != current_sig:
        return JsonResponse({'changed': True, 'token': current_sig, 'counts': counts})

    while time.time() - start_time < timeout_seconds:
        time.sleep(1)

        counts, new_sig = get_counts_and_signature(AdRecord.objects.all())
        if new_sig != current_sig:
            return JsonResponse({'changed': True, 'token': new_sig, 'counts': counts})

    return JsonResponse({'changed': False, 'token': current_sig, 'counts': counts})


@never_cache
@login_required
def poll_user_status(request):
    timeout_seconds = 15 
    client_token = request.GET.get('token', '')
    start_time = time.time()

    counts, current_sig = get_counts_and_signature(
        AdRecord.objects.filter(user=request.user)
    )
    if client_token and client_token != current_sig:
        return JsonResponse({'changed': True, 'token': current_sig, 'counts': counts})

    while time.time() - start_time < timeout_seconds:
        time.sleep(1)

        counts, new_sig = get_counts_and_signature(
            AdRecord.objects.filter(user=request.user)
        )
        if new_sig != current_sig:
            return JsonResponse({'changed': True, 'token': new_sig, 'counts': counts})

    return JsonResponse({'changed': False, 'token': current_sig, 'counts': counts})


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
    if request.user.is_superuser:
        messages.error(request, 'Admins cannot renew enquiries.')
        return redirect('admin_dashboard')

    original_ad = get_object_or_404(AdRecord, id=ad_id, user=request.user, status='completed')

    if request.method == 'POST':
        form = PaymentDetailsForm(request.POST)
        if form.is_valid():
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
            
            predefined_mapping_amounts = set(AdRecord.AMOUNT_DAYS_MAPPING.keys())
            if new_ad.amount == 0 or new_ad.amount not in predefined_mapping_amounts:
                new_ad.custom_amount = form.cleaned_data.get('custom_amount')
                new_ad.custom_days = form.cleaned_data.get('custom_days')
                new_ad.amount = new_ad.custom_amount
            else:
                new_ad.custom_amount = None
                new_ad.custom_days = None
                
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
    if request.method != 'POST':
        messages.error(request, 'Invalid request method.')
        return redirect('admin_users')

    user = get_object_or_404(User, id=user_id)

    if user == request.user:
        messages.error(request, 'You cannot delete your own account while logged in.')
        return redirect('admin_users')

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
    
    today = timezone.now().date()

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

    recipient = os.getenv('recipient','sanjithmit@gmail.com')
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
    ad = get_object_or_404(AdRecord, id=ad_id)

    history_qs = AdRecord.objects.filter(business_name=ad.business_name).order_by('-entry_date')

    return render(request, 'campaigns/_ad_history.html', {
        'subject_ad': ad,
        'history_ads': history_qs,
    })

@login_required
@require_GET
def lookup_by_mobile(request):
    mobile = request.GET.get('mobile', '').strip()
    if not (mobile.isdigit() and len(mobile) == 10):
        return JsonResponse({'ok': False, 'results': [], 'error': 'Invalid mobile'}, status=400)
    qs = AdRecord.objects.filter(user=request.user, mobile_number=mobile).order_by('-entry_date')
    results = [
        {
            'id': ad.id,
            'ad_name': ad.ad_name,
            'status': ad.get_status_display(),
            'notes': ad.notes or '',
        }
        for ad in qs
    ]
    return JsonResponse({'ok': True, 'results': results})


@login_required
def user_day1_followup(request):
    today = timezone.now().date()
    yesterday = today - timedelta(days=1)
    
    # Get followups for yesterday's enquiries
    followups = Day1FollowUp.objects.filter(
        ad_record__user=request.user,
        ad_record__status='enquiry',
        ad_record__entry_date__date=yesterday  # Enquiries created yesterday
    ).order_by('follow_up_date')
    
    return render(request, 'campaigns/followup_table.html', {
        'followups': followups,
        'title': 'Day 1 Follow-ups (Yesterday\'s Enquiries)',
        'followup_type': 'day1'
    })


@login_required
def user_day2_followup(request):
    today = timezone.now().date()
    day_before_yesterday = today - timedelta(days=2)
    
    # Get followups for day before yesterday's enquiries
    followups = Day2FollowUp.objects.filter(
        ad_record__user=request.user,
        ad_record__status='enquiry',
        ad_record__entry_date__date=day_before_yesterday  # Enquiries created day before yesterday
    ).order_by('follow_up_date')
    
    return render(request, 'campaigns/followup_table.html', {
        'followups': followups,
        'title': 'Day 2 Follow-ups (Day Before Yesterday\'s Enquiries)',
        'followup_type': 'day2'
    })

@login_required
def user_dashboard(request):
    return render(request, 'user/dashboard.html')



@login_required
def update_followup(request, followup_id, followup_type):
    if followup_type == 'day1':
        followup = get_object_or_404(Day1FollowUp, id=followup_id)
    elif followup_type == 'day2':
        followup = get_object_or_404(Day2FollowUp, id=followup_id)
    else:
        messages.error(request, 'Invalid follow-up type')
        return redirect('user_dashboard')  # fallback to user dashboard
    
    if request.method == 'POST':
        followup.contacted = request.POST.get('contacted') == 'on'
        followup.contact_method = request.POST.get('contact_method', '')
        followup.response = request.POST.get('response', '')
        followup.notes = request.POST.get('notes', '')
        followup.save()
        
        messages.success(request, 'Follow-up updated successfully!')
        
        if followup_type == 'day1':
            return redirect('user_day1_followup')
        elif followup_type == 'day2':
            return redirect('user_day2_followup')
        else:
            return redirect('user_dashboard')

    
    context = {
        'followup': followup,
        'followup_type': followup_type
    }
    return render(request, 'campaigns/update_followup.html', context)


@login_required
def edit_enquiry(request, ad_id):
    if request.user.is_superuser:
        messages.error(request, 'Admins cannot edit enquiries. Use the admin dashboard.')
        return redirect('admin_dashboard')
    
    ad = get_object_or_404(AdRecord, id=ad_id, user=request.user, status='enquiry')
    
    if request.method == 'POST':
        form = EditEnquiryForm(request.POST, instance=ad)
        if form.is_valid():
            form.save()
            messages.success(request, 'Enquiry updated successfully!')
            return redirect('dashboard')
    else:
        form = EditEnquiryForm(instance=ad)
    
    return render(request, 'campaigns/edit_enquiry.html', {'form': form, 'ad': ad})


@login_required
def edit_hold(request, ad_id):
    if request.user.is_superuser:
        messages.error(request, 'Admins cannot edit holds. Use the admin dashboard.')
        return redirect('admin_dashboard')
    
    ad = get_object_or_404(AdRecord, id=ad_id, user=request.user, status='hold')
    
    if request.method == 'POST':
        form = EditHoldForm(request.POST, instance=ad)
        if form.is_valid():
            form.save()
            messages.success(request, 'Hold record updated successfully!')
            return redirect('dashboard')
    else:
        form = EditHoldForm(instance=ad)
    
    return render(request, 'campaigns/edit_hold.html', {'form': form, 'ad': ad})


@login_required
@user_passes_test(is_admin)
def admin_edit_enquiry(request, ad_id):
    ad = get_object_or_404(AdRecord, id=ad_id, status='enquiry')
    
    if request.method == 'POST':
        form = EditEnquiryForm(request.POST, instance=ad)
        if form.is_valid():
            form.save()
            messages.success(request, 'Enquiry updated successfully!')
            return redirect('admin_dashboard')
    else:
        form = EditEnquiryForm(instance=ad)
    
    return render(request, 'campaigns/admin_edit_enquiry.html', {'form': form, 'ad': ad})


@login_required
@user_passes_test(is_admin)
def admin_edit_hold(request, ad_id):
    ad = get_object_or_404(AdRecord, id=ad_id, status='hold')
    
    if request.method == 'POST':
        form = EditHoldForm(request.POST, instance=ad)
        if form.is_valid():
            form.save()
            messages.success(request, 'Hold record updated successfully!')
            return redirect('admin_dashboard')
    else:
        form = EditHoldForm(instance=ad)
    
    return render(request, 'campaigns/admin_edit_hold.html', {'form': form, 'ad': ad})

@login_required
@user_passes_test(is_admin)
def admin_set_target(request, user_id):
    target_user = get_object_or_404(User, id=user_id)
    
    user_profile, created = UserProfile.objects.get_or_create(user=target_user)
    
    if request.method == 'POST':
        form = SetTargetForm(request.POST)
        if form.is_valid():
            target_amount = form.cleaned_data['target_amount']
            user_profile.target_amount = target_amount
            user_profile.save()
            
            messages.success(request, f'Target of ₹{target_amount} set successfully for {target_user.username}.')
            return redirect('admin_users')
    else:
        form = SetTargetForm(initial={'target_amount': user_profile.target_amount})
    
    return render(request, 'campaigns/admin_set_target.html', {
        'form': form, 
        'target_user': target_user
    })