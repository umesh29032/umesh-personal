from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect
from django.contrib import messages  # Added import
from accounts.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from allauth.socialaccount.providers.google import provider
from django.views.generic import TemplateView
from django.contrib.auth import get_user_model
from accounts.serializers import UserSerializer
from .forms import UserEditForm
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponseRedirect, HttpResponse
import json
from django.core.serializers.json import DjangoJSONEncoder
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
    # import allauth.socialaccount.views
    # print("121324435",dir(allauth.socialaccount.views))
    # import allauth.account
    # print(dir(allauth.account))
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']
        user = authenticate(request, username=email, password=password)
        if user is not None:
            login(request, user)
            return redirect('accounts:home')
        else:
            messages.error(request, "Invalid credentials")
            return render(request, 'accounts/login.html', {'error': 'Invalid credentials'})
    return render(request, 'accounts/login.html')

def register_view(request):
    print("hererer",User.objects.all())
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        email = request.POST['email']
        password = request.POST['password']
        confirm_password = request.POST['confirm_password']
        
        # Validation
        if not name:
            messages.error(request, "Name is required")
            return render(request, 'accounts/register.html')
        
        if password != confirm_password:
            messages.error(request, "Passwords do not match")
            return render(request, 'accounts/register.html')
        
        if User.objects.filter(email=email).exists():
            messages.error(request, "Email is already registered")
            return render(request, 'accounts/register.html')
        
        try:
            # Split name into first and last name
            name_parts = name.split(' ', 1)
            first_name = name_parts[0]
            last_name = name_parts[1] if len(name_parts) > 1 else ''
            
            user = User.objects.create_user(
                email=email, 
                password=password,
                first_name=first_name,
                last_name=last_name
            )
            user.save()
            messages.success(request, "Registration successful. Please log in.")
            return redirect('accounts:login')
        except Exception as e:
            messages.error(request, f"Registration failed: {str(e)}")
            return render(request, 'accounts/register.html')
    
    return render(request, 'accounts/register.html')

def custom_logout(request):
    logout(request)
    return redirect('accounts:login')  # Redirect to login page after logout

# def google_login(request):
#     if request.GET.get('process') == 'login':
#         return redirect('/accounts/google/login/continue/')
#     try:
#         template = get_template('socialaccount/google_login.html')
#         print("Template found:", template.origin.name)
#     except Exception as e:
#         print("Template error:", str(e))
#     return render(request, 'socialaccount/google_login.html')

@login_required(login_url="accounts:login")
def home(request):
    from django.urls import reverse
    print(reverse('account_logout'))  # Should print /accounts/logout/
    User = get_user_model()
    users = User.objects.all()
    for user in users:
        print(user.id, user.email, user.is_active)
    users = User.objects.all()
    # Current user ko request.user se milta hai
    # current_user = request.user 
    # user_data = {
    #     'id': current_user.id,
    #     'email': current_user.email,
    #     'first_name': current_user.first_name,
    #     'last_name': current_user.last_name,
    #     'is_active': current_user.is_active,
    #     'is_staff': current_user.is_staff,
    #     'is_superuser': current_user.is_superuser,
    #     'last_login': current_user.last_login,
    #     'date_joined': current_user.date_joined,
    #     'phone_number': current_user.phone_number,
    #     'birth_date': current_user.birth_date,
    #     'bio': current_user.bio,
    #     'profile_picture': str(current_user.profile_picture) if current_user.profile_picture else None,
    #     'salary': float(current_user.salary) if current_user.salary else None,
    # }
    # user_json = json.dumps(user_data, indent=2, cls=DjangoJSONEncoder)
    serializer = UserSerializer(request.user,many=False)
    print("json data",serializer.data)
    return render(request, 'accounts/home.html')

def test_page(request):
    """Test page to verify Tailwind CSS is working"""
    return render(request, 'accounts/test.html')

def custom_google_login(request):
    if request.GET.get('process') == 'login':
        return redirect('/accounts/google/login/continue/')
    return render(request, 'socialaccount/custom_google_login.html', {'next': request.GET.get('next', '')})

def user_list_view(request):
    users = User.objects.all()
    search_name = request.GET.get('search_name', '')
    if search_name:
        users = users.filter(first_name__icontains=search_name) | users.filter(last_name__icontains=search_name)
    return render(request, 'accounts/user_list.html', {'users': users})

def user_detail_view(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if request.method == 'POST':
        form = UserEditForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            return redirect('accounts:user_list')
    else:
        form = UserEditForm(instance=user)
    return render(request, 'accounts/user_detail.html', {'form': form, 'user': user})

def inventory(request):
    return render(request, 'accounts/inventory.html')  # Create this later