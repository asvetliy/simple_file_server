from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('login', views.UserLoginView.as_view(), name='user-login'),
    path('logout', auth_views.LogoutView.as_view(), name='user-logout'),
]
