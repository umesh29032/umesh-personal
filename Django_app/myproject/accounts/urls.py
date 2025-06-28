from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
from django.urls import reverse_lazy

app_name = 'accounts'

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('home/', views.home, name='home'),
    path('test/', views.test_page, name='test'),  # Test page for Tailwind
    path('logout/', views.custom_logout, name='account_logout'),  # Override allauth logout
    path('users/', views.user_list_view, name='user_list'),
    path('user/<int:user_id>/', views.user_detail_view, name='user_detail'),
    path('user/delete/<int:user_id>/', views.delete_user, name='delete_user'),
    path('inventory/', views.inventory, name='inventory'),
    path('skills/', views.skill_management, name='skill_management'),
    path('skills/delete/<int:pk>/', views.delete_skill, name='delete_skill'),  # For DELETE action
    
    # path('google/login/', views.google_login, name='google_login'),
    
    # Password Reset URLs
    path('password_reset/', auth_views.PasswordResetView.as_view(
        template_name='accounts/password_reset.html',
        email_template_name='accounts/password_reset_email.html',
        subject_template_name='accounts/password_reset_subject.txt',
        success_url=reverse_lazy('accounts:password_reset_done')
    ), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='accounts/password_reset_done.html'
    ), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='accounts/password_reset_confirm.html'
    ), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(
        template_name='accounts/password_reset_complete.html'
    ), name='password_reset_complete'),

    # Password Change URL
    path('password_change/', auth_views.PasswordChangeView.as_view(
        template_name='accounts/password_change.html',
        success_url=reverse_lazy('accounts:password_change_done')
    ), name='password_change'),
    path('password_change/done/', auth_views.PasswordChangeDoneView.as_view(
        template_name='accounts/password_change_done.html'
    ), name='password_change_done'),
]