from django.urls import path #type: ignore
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('create/', views.create_ad, name='create_ad'),
    path('add-payment/<int:ad_id>/', views.add_payment_details, name='add_payment'),
    path('renew/<int:ad_id>/', views.renew_ad, name='renew_ad'),

    # Admin URLs
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('verify-payment/<int:ad_id>/', views.verify_payment, name='verify_payment'),
    path('activate-ad/<int:ad_id>/', views.activate_ad, name='activate_ad'),
    path('admin-users/', views.admin_users, name='admin_users'),
    path('admin-users/<int:user_id>/delete/', views.admin_delete_user, name='admin_delete_user'),
    path('admin-users/<int:user_id>/set-password/', views.admin_set_password, name='admin_set_password'),
    path('notifications/', views.notifications, name='notifications'),
    path('admin-ad-history/<int:ad_id>/', views.admin_ad_history, name='admin_ad_history'),
]