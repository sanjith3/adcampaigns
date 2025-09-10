from django.urls import path
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
]