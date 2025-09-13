"""
URL configuration for adsoft project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin #type: ignore
from django.urls import path, include #type: ignore
from django.contrib.auth import views as auth_views #type: ignore
from django.views.generic import RedirectView #type: ignore
from campaigns.views import AlwaysLoginView #type: ignore
from django_eventstream import eventstream #type: ignore

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', RedirectView.as_view(url='/login/', permanent=False)),
    path('dashboard/', include('campaigns.urls')),
    path('login/', AlwaysLoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='/login/'), name='logout'),
    path('events/', include('django_eventstream.urls'))
]