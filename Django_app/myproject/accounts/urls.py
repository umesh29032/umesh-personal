from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('home/', views.home, name='home'),
    path('logout/', views.custom_logout, name='account_logout'),  # Override allauth logout
    path('users/', views.user_list_view, name='user_list'),
    path('user/<int:user_id>/', views.user_detail_view, name='user_detail'),
    # path('google/login/', views.google_login, name='google_login'),
]