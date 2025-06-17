from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect
from django.contrib import messages  # Added import
from accounts.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from allauth.socialaccount.providers.google import provider
from django.views.generic import TemplateView
# from allauth.socialaccount.providers.google.views import GoogleLoginView
# from allauth.socialaccount.views import SocialLoginView
# class GoogleLoginContinueView(SocialLoginView):
#     provider_id = 'google'
class CustomGoogleLoginView(TemplateView):
    template_name = 'socialaccount/custom_google_login.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['next'] = self.request.GET.get('next', '')
        return context

    def post(self, request, *args, **kwargs):
        next_url = request.POST.get('next', request.GET.get('next', ''))
        return redirect(f'/accounts/google/login/?process=login{"&next=" + next_url if next_url else ""}')

class GoogleLoginContinueView(TemplateView):
    def get(self, request, *args, **kwargs):
        return redirect('/accounts/google/login/')

def login_view(request):
    import allauth.socialaccount.views
    print("121324435",dir(allauth.socialaccount.views))
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']
        user = authenticate(request, username=email, password=password)
        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            return render(request, 'accounts/login.html', {'error': 'Invalid credentials'})
    return render(request, 'accounts/login.html')

def register_view(request):
    print("hererer",User.objects.all())
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']
        confirm_password = request.POST['confirm_password']
        
        if password != confirm_password:
            messages.error(request, "Passwords do not match")
            return render(request, 'accounts/register.html')
        
        if User.objects.filter(email=email).exists():
            messages.error(request, "Email is already registered")
            return render(request, 'accounts/register.html')
        
        try:
            user = User.objects.create_user(email=email, password=password)
            user.save()
            messages.success(request, "Registration successful. Please log in.")
            return redirect('login')
        except Exception as e:
            messages.error(request, f"Registration failed: {str(e)}")
            return render(request, 'accounts/register.html')
    
    return render(request, 'accounts/register.html')

def custom_logout(request):
    logout(request)
    return redirect('login')  # Redirect to login page after logout

# def google_login(request):
#     if request.GET.get('process') == 'login':
#         return redirect('/accounts/google/login/continue/')
#     try:
#         template = get_template('socialaccount/google_login.html')
#         print("Template found:", template.origin.name)
#     except Exception as e:
#         print("Template error:", str(e))
#     return render(request, 'socialaccount/google_login.html')

@login_required(login_url="login")
def home(request):
    from django.urls import reverse
    print(reverse('account_logout'))  # Should print /accounts/logout/
    return render(request, 'accounts/home.html')

def custom_google_login(request):
    if request.GET.get('process') == 'login':
        return redirect('/accounts/google/login/continue/')
    return render(request, 'socialaccount/custom_google_login.html', {'next': request.GET.get('next', '')})