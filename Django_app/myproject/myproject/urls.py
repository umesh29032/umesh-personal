from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic.base import RedirectView
from django.contrib.auth import views as auth_views
from accounts.views import  GoogleLoginContinueView
from accounts.views import user_list_view, user_detail_view,CustomGoogleLoginView

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    
    # Authentication
    path('accounts/', include('allauth.urls')),
    path('myaccounts/', include('accounts.urls', namespace='accounts')),
    
    # Redirects
    path('', RedirectView.as_view(url='/myaccounts/home/', permanent=False), name='index'),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    
    # Add debug toolbar if installed
    try:
        import debug_toolbar
        urlpatterns += [
            path('__debug__/', include(debug_toolbar.urls)),
        ]
    except ImportError:
        pass