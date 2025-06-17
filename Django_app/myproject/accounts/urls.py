from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('home/', views.home, name='home'),
    path('logout/', views.custom_logout, name='account_logout'),  # Override allauth logout
    # path('google/login/', views.google_login, name='google_login'),
]