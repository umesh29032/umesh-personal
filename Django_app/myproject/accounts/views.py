from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect
from django.contrib import messages  # Added import
from accounts.models import User,Skill
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
from .decorators import user_type_required,user_types_required
from django.forms.models import model_to_dict
from django.db.models import Count, Sum
from django.utils import timezone
from datetime import timedelta
def get_object_details_with_m2m(obj):
    """
    Returns a dictionary of all attributes including ManyToMany field data.
    """
    data = model_to_dict(obj)
    # Handle ManyToMany fields manually
    for field in obj._meta.many_to_many:
        data[field.name] = list(obj.__getattribute__(field.name).values_list('name', flat=True))
    return data
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
    """
    Dashboard home view showing key metrics and recent activity.
    """
    # Get user count
    user_count = User.objects.count()
    
    # Get user type distribution for potential chart data
    user_types = User.objects.values('user_type').annotate(count=Count('id'))
    
    # Get skills distribution
    skills = Skill.objects.annotate(user_count=Count('users'))
    
    # Sample data for demonstration (in a real app, this would come from your database)
    context = {
        'user_count': user_count,
        'order_count': 125,  # Example data
        'revenue': '1,25,000',  # Example data
        'inventory_count': 450,  # Example data
        'user_types': list(user_types),
        'skills': list(skills.values('name', 'user_count')),
        'recent_users': User.objects.order_by('-created_at')[:5],  # 5 most recent users
    }
    
    return render(request, 'accounts/home.html', context)

def test_page(request):
    """Test page to verify Tailwind CSS is working"""
    return render(request, 'accounts/test.html')

def custom_google_login(request):
    if request.GET.get('process') == 'login':
        return redirect('/accounts/google/login/continue/')
    return render(request, 'socialaccount/custom_google_login.html', {'next': request.GET.get('next', '')})

@login_required(login_url="accounts:login")
@user_types_required('admin')
def user_list_view(request):
    users = User.objects.all()
    search_name = request.GET.get('search_name', '')
    if search_name:
        users = users.filter(first_name__icontains=search_name) | users.filter(last_name__icontains=search_name)
    return render(request, 'accounts/user_list.html', {'users': users})

@login_required(login_url="accounts:login")
@user_types_required('admin')
def user_detail_view(request, user_id):
    edit_user = get_object_or_404(User, id=user_id)
    if request.method == 'POST':
        form = UserEditForm(request.POST, instance=edit_user)
        if form.is_valid():
            form.save()
            return redirect('accounts:user_list')
    else:
        form = UserEditForm(instance=edit_user)
    # print("form",form.fields['skills'])
    # print("form",form.fields['skills'].queryset)
    # print("user skills",edit_user.skills.all())
    # print("edit_user details using m2m",get_object_details_with_m2m(edit_user))
    return render(request, 'accounts/user_detail.html', {'form': form, 'user':request.user,'edit_user': edit_user})

@login_required(login_url="accounts:login")
@user_types_required('admin')
def inventory(request):
    return render(request, 'accounts/inventory.html')  # Create this later

@login_required
@user_types_required('admin')
def skill_management(request):
    for all_skill in Skill.objects.all():
        print("all_skill",all_skill.name)
    if request.method == 'POST':
        if 'name' in request.POST:
            name = request.POST['name'].strip()
            description = request.POST.get('description', '').strip()
            if not Skill.objects.filter(name=name).exists():
                Skill.objects.create(name=name, description=description)
                messages.success(request, f"Skill '{name}' added successfully.")
            else:
                messages.error(request, f"Skill '{name}' already exists.")
        
        return redirect('accounts:skill_management')
    
    skills = Skill.objects.all()
    return render(request, 'accounts/skills_management.html', {'skills': skills})

@login_required
@user_types_required('admin')
def delete_skill(request, pk):
    skill = get_object_or_404(Skill, id=pk)
    if request.method == 'POST':
        skill.delete()
        messages.success(request, f"Skill '{skill.name}' deleted successfully.")
        return redirect('accounts:skill_management')
    return render(request, 'accounts/skills_management.html', {'skills': Skill.objects.all()})


@login_required
@user_types_required('admin')
def delete_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if request.method == 'POST':
        user.delete()
        messages.success(request, f"User '{user.email}' deleted successfully.")
        return redirect('accounts:user_list')  # Redirect to user list after deletion
    return render(request, 'accounts/user_detail.html', {'edit_user': user})