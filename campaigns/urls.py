from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('create/', views.create_ad, name='create_ad'),
    path('add-payment/<int:ad_id>/', views.add_payment_details, name='add_payment'),
    path('hold/<int:ad_id>/', views.add_hold, name='add_hold'),
    path('hold/<int:ad_id>/remove/', views.remove_hold, name='remove_hold'),
    path('renew/<int:ad_id>/', views.renew_ad, name='renew_ad'),
    # Add this to your urlpatterns
    path('enquiry-history/', views.enquiry_history, name='enquiry_history'),

    # Admin URLs
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('verify-payment/<int:ad_id>/', views.verify_payment, name='verify_payment'),
    path('activate-ad/<int:ad_id>/', views.activate_ad, name='activate_ad'),
    path('admin-users/', views.admin_users, name='admin_users'),
    path('admin-users/<int:user_id>/delete/', views.admin_delete_user, name='admin_delete_user'),
    path('admin-users/<int:user_id>/set-password/', views.admin_set_password, name='admin_set_password'),
    path('admin-users/<int:user_id>/set-target/', views.admin_set_target, name='admin_set_target'),

    # Long-polling endpoint for admin dashboard
    path('admin-dashboard/poll/', views.poll_admin_status, name='poll_admin_status'),

    # ✅ FIXED: User poll endpoint (removed the extra 'dashboard/')
    path('poll/', views.poll_user_status, name='poll_user_status'),

    path('notifications/', views.notifications, name='notifications'),
    path('generate-report/', views.admin_generate_report, name='admin_generate_report'),
    path('admin-ad-history/<int:ad_id>/', views.admin_ad_history, name='admin_ad_history'),
    path('lookup-by-mobile/', views.lookup_by_mobile, name='lookup_by_mobile'),
    
    # Edit URLs
    path('edit-enquiry/<int:ad_id>/', views.edit_enquiry, name='edit_enquiry'),
    path('edit-hold/<int:ad_id>/', views.edit_hold, name='edit_hold'),
    
    # Admin Edit URLs
    path('admin-edit-enquiry/<int:ad_id>/', views.admin_edit_enquiry, name='admin_edit_enquiry'),
    path('admin-edit-hold/<int:ad_id>/', views.admin_edit_hold, name='admin_edit_hold'),
    
    # Follow-up URLs
    path('user/day1-followup/', views.user_day1_followup, name='user_day1_followup'),
    path('user/day2-followup/', views.user_day2_followup, name='user_day2_followup'),
    path('user/dashboard/', views.user_dashboard, name='user_dashboard'),
    path('update-followup/<int:followup_id>/<str:followup_type>/', views.update_followup, name='update_followup'),

    path('.well-known/<path:path>', views.well_known_handler),
    
]
