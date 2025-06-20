from django.contrib import admin
from django.urls import path, include
from django.views.generic.base import RedirectView
from django.contrib.auth import views as auth_views
from accounts.views import  GoogleLoginContinueView
from accounts.views import user_list_view, user_detail_view,CustomGoogleLoginView
urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),  # Added for password reset
    path('accounts/', include('allauth.urls')),
    path('myaccounts/', include('accounts.urls',namespace='accounts')),  # Avoid conflict with allauth
    path('users/',user_list_view,name='user_list'),
    path('user/<int:user_id>/',user_detail_view,name='user_detail')
    # path('accounts/google/login/', CustomGoogleLoginView.as_view(), name='custom_google_login'),
    # path('accounts/google/login/', custom_google_login, name='custom_google_login'),
    # path('accounts/google/login/continue/', GoogleLoginContinueView.as_view(), name='google_login_continue'),
    # path('login/', RedirectView.as_view(url='/myaccounts/login/', permanent=False)),
    # path('register/', RedirectView.as_view(url='/myaccounts/register/', permanent=False)),
    
    #  path('accounts/password_reset/', 
    #      auth_views.PasswordResetView.as_view(
    #          template_name='accounts/password_reset.html',
    #          email_template_name='accounts/password_reset_email.html',
    #          subject_template_name='accounts/password_reset_subject.txt'
    #      ), 
    #      name='password_reset'),
    
    # path('accounts/password_reset/done/', 
    #      auth_views.PasswordResetDoneView.as_view(
    #          template_name='accounts/password_reset_done.html'
    #      ), 
    #      name='password_reset_done'),
    
    # path('accounts/reset/<uidb64>/<token>/', 
    #      auth_views.PasswordResetConfirmView.as_view(
    #          template_name='accounts/password_reset_confirm.html'
    #      ), 
    #      name='password_reset_confirm'),
    
    # path('accounts/reset/done/', 
    #      auth_views.PasswordResetCompleteView.as_view(
    #          template_name='accounts/password_reset_complete.html'
    #      ), 
    #      name='password_reset_complete'),
]