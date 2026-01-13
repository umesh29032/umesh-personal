import random
from django.shortcuts import render, redirect
from django.views import View
from django.contrib.auth import login
from django.core.mail import send_mail
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.utils.decorators import method_decorator
from django.conf import settings
from django.contrib import messages
from accounts.decorators import login_required_view
from .models import User, Skill
from .forms import UserEditForm, SignupForm, SkillForm
from django.views.generic import ListView, UpdateView, DeleteView, FormView, CreateView
from django.db.models import Q
from django.contrib.auth.views import LoginView as DjangoLoginView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy, reverse
from django.contrib import messages
from django.shortcuts import render, redirect
from django.contrib import messages
from django.shortcuts import render, redirect
import time



class LoginView(View):
    """
    Login with Email + OTP
    """

    def get(self, request):
        if request.user.is_authenticated:
            return redirect("accounts:home")
        return render(request, "accounts/login.html")

    def post(self, request):
        email = request.POST.get("email")

        # 1️⃣ Create user if not exists
        user, created = User.objects.get_or_create(email=email)

        current_time = int(time.time())

        # check resend cooldown (60 sec)
        last_sent = request.session.get("otp_last_sent_at")

        if last_sent and current_time - last_sent < 60:
            return redirect("accounts:verify_otp")

        otp = random.randint(100000, 999999)

        request.session["otp"] = str(otp)
        request.session["email"] = email
        request.session["otp_created_at"] = current_time
        request.session["otp_last_sent_at"] = current_time



        # 4️⃣ Send OTP via Gmail SMTP
        send_mail(
            subject="Your Login OTP",
            message=f"""
                    Hello,
                    Your OTP for login is: {otp}

                    This OTP is valid for a short time.
                    If you did not request this, ignore this email.

                    Thanks,
                    Inventory App
                    """,
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[email],
            fail_silently=False,
        )

        # 5️⃣ Redirect to OTP page
        return redirect("accounts:verify_otp")

class ResendOTPView(View):
    """
    Resend OTP after 60 seconds cooldown
    """

    def get(self, request):
        email = request.session.get("email")

        if not email:
            return redirect("accounts:login")

        current_time = int(time.time())
        last_sent = request.session.get("otp_last_sent_at")

        # block resend if within 60 seconds
        if last_sent and current_time - last_sent < 60:
            return redirect("accounts:verify_otp")

        # generate new OTP
        otp = random.randint(100000, 999999)

        request.session["otp"] = str(otp)
        request.session["otp_created_at"] = current_time
        request.session["otp_last_sent_at"] = current_time

        send_mail(
            subject="Your Login OTP (Resent)",
            message=f"Your new OTP is: {otp}",
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[email],
            fail_silently=False,
        )

        return redirect("accounts:verify_otp")


class VerifyOTPView(View):

    def get(self, request):
        return render(request, "accounts/otp.html")

    def post(self, request):
        entered_otp = request.POST.get("otp")
        saved_otp = request.session.get("otp")
        otp_time = request.session.get("otp_created_at")
        email = request.session.get("email")

        # 🔒 1️⃣ Validate session data
        if not saved_otp or not otp_time or not email:
            messages.error(request, "Session expired. Please login again.")
            return redirect("accounts:login")


        # OTP valid for 1 minutes (60 seconds)
        if int(time.time()) - otp_time > 60:
            self._clear_otp_session(request)
            messages.error(request, "OTP expired. Please request a new one.")
            return redirect("accounts:login")
        # OTP mismatch
        if entered_otp != saved_otp:
            messages.error(request, "Invalid OTP. Please try again.")
            return redirect("accounts:verify_otp")
        # otp valid ---> login
        user = User.objects.get(email=email)

        login(request,
        user,
        backend="django.contrib.auth.backends.ModelBackend"
        )

        # Clear OTP after success
        self._clear_otp_session(request)

        return redirect("accounts:home")

    def _clear_otp_session(self, request):
        """Utility method to clear OTP-related session data"""
        request.session.pop("otp", None)
        request.session.pop("otp_created_at", None)
        request.session.pop("otp_last_sent_at", None)
        request.session.pop("email", None)

class LogoutView(View):
    """
    Logout user and clear session
    """

    def get(self, request):
        logout(request)
        return redirect("accounts:login")


@method_decorator(login_required(login_url="/"), name="dispatch")
# @method_decorator(login_required_view, name="dispatch")

class HomeView(View):
    """
    Protected Home Page
    """

    def get(self, request):
        return render(request, "accounts/home.html")

class SuperuserRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_superuser

class UserListView(LoginRequiredMixin, SuperuserRequiredMixin, ListView):
    model = User
    template_name = "accounts/user_list.html"
    context_object_name = "users"
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset()
        q = self.request.GET.get('q')
        skills = self.request.GET.getlist('skills')

        if q:
            queryset = queryset.filter(
                Q(first_name__icontains=q) | 
                Q(last_name__icontains=q) | 
                Q(email__icontains=q)
            )
        
        if skills:
            queryset = queryset.filter(skills__id__in=skills).distinct()
            
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['skills'] = Skill.objects.all()
        # Convert string IDs from GET to integers for correct template comparison
        try:
            context['selected_skills'] = [int(x) for x in self.request.GET.getlist('skills')]
        except ValueError:
            context['selected_skills'] = []
            
        context['search_query'] = self.request.GET.get('q', '')
        return context



class UserUpdateView(LoginRequiredMixin, SuperuserRequiredMixin, UpdateView):
    model = User
    form_class = UserEditForm
    template_name = "accounts/user_form.html"
    success_url = reverse_lazy('accounts:user_list')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        # If the user is updating their own profile and changed the password,
        # update the session so they don't get logged out.
        if self.object == self.request.user and form.cleaned_data.get('new_password'):
            from django.contrib.auth import update_session_auth_hash
            update_session_auth_hash(self.request, self.object)
            
        messages.success(self.request, "User details updated successfully.")
        return response

class UserDeleteView(LoginRequiredMixin, SuperuserRequiredMixin, DeleteView):
    model = User
    template_name = "accounts/user_confirm_delete.html"
    success_url = reverse_lazy('accounts:user_list')

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, "User deleted successfully.")
        return super().delete(request, *args, **kwargs)

class PasswordLoginView(DjangoLoginView):
    template_name = "accounts/login_password.html"
    redirect_authenticated_user = True
    
    def get_success_url(self):
        return reverse_lazy('accounts:home')

class SignupView(FormView):
    template_name = "accounts/signup.html"
    form_class = SignupForm
    success_url = reverse_lazy('accounts:signup_verify')

    def form_valid(self, form):
        # Store data in session temporarily
        self.request.session['signup_data'] = form.cleaned_data
        
        # Generate OTP
        email = form.cleaned_data['email']
        otp = random.randint(100000, 999999)
        current_time = int(time.time())
        
        self.request.session["signup_otp"] = str(otp)
        self.request.session["signup_email"] = email
        self.request.session["otp_created_at"] = current_time
        
        # Send OTP
        send_mail(
            subject="Verify your Account",
            message=f"Your OTP for account creation is: {otp}",
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[email],
            fail_silently=False,
        )
        return super().form_valid(form)

class SignupVerifyView(View):
    def get(self, request):
        return render(request, "accounts/signup_otp.html")
        
    def post(self, request):
        entered_otp = request.POST.get("otp")
        saved_otp = request.session.get("signup_otp")
        signup_data = request.session.get("signup_data")
        
        if not saved_otp or not signup_data:
            messages.error(request, "Session expired. Please sign up again.")
            return redirect("accounts:signup")
            
        if entered_otp != saved_otp:
            messages.error(request, "Invalid OTP.")
            return redirect("accounts:signup_verify")
            
        # Create User
        user = User.objects.create_user(
            email=signup_data['email'],
            password=signup_data['password']
        )
        
        # Login
        login(request, user, backend="django.contrib.auth.backends.ModelBackend")
        
        # Cleanup
        request.session.pop('signup_otp', None)
        request.session.pop('signup_data', None)
        
        messages.success(request, "Account created successfully!")
        return redirect("accounts:home")

class ForgotPasswordView(View):
    def get(self, request):
        return render(request, "accounts/forgot_password.html")
        
    def post(self, request):
        email = request.POST.get("email")
        if not User.objects.filter(email=email).exists():
            messages.error(request, "No user found with this email.")
            return redirect("accounts:forgot_password")
            
        otp = random.randint(100000, 999999)
        request.session["reset_otp"] = str(otp)
        request.session["reset_email"] = email
        
        send_mail(
            subject="Password Reset OTP",
            message=f"Your OTP for password reset is: {otp}",
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[email],
            fail_silently=False,
        )
        return redirect("accounts:reset_password_verify")

class ResetPasswordVerifyView(View):
    def get(self, request):
        return render(request, "accounts/reset_otp.html")

    def post(self, request):
        otp = request.POST.get("otp")
        password = request.POST.get("password")
        saved_otp = request.session.get("reset_otp")
        email = request.session.get("reset_email")
        
        if not saved_otp or not email or otp != saved_otp:
            messages.error(request, "Invalid OTP or session expired.")
            return redirect("accounts:reset_password_verify")
            
        user = User.objects.get(email=email)
        user.set_password(password)
        user.save()
        
        # Cleanup
        request.session.pop('reset_otp', None)
        request.session.pop('reset_email', None)
        
        messages.success(request, "Password reset successfully. Please login.")
        return redirect("accounts:login_password")

class ResendSignupOTPView(View):
    def get(self, request):
        email = request.session.get("signup_email")
        if not email:
            messages.error(request, "Session expired.")
            return redirect("accounts:signup")
            
        # Cooldown check
        last_sent = request.session.get("otp_created_at")
        current_time = int(time.time())
        if last_sent and current_time - last_sent < 60:
             messages.warning(request, "Please wait 60 seconds before resending.")
             return redirect("accounts:signup_verify")
             
        # Generate new OTP
        otp = random.randint(100000, 999999)
        request.session["signup_otp"] = str(otp)
        request.session["otp_created_at"] = current_time
        
        send_mail(
            subject="Resend: Verify your Account",
            message=f"Your new OTP is: {otp}",
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[email],
            fail_silently=False,
        )
        messages.success(request, "OTP resent successfully.")
        return redirect("accounts:signup_verify")



class SkillListView(LoginRequiredMixin, SuperuserRequiredMixin, ListView):
    model = Skill
    template_name = "accounts/skill_list.html"
    context_object_name = "skills"
    ordering = ['name']

class SkillCreateView(LoginRequiredMixin, SuperuserRequiredMixin, CreateView):
    model = Skill
    form_class = SkillForm
    template_name = "accounts/skill_form.html"
    success_url = reverse_lazy('accounts:skill_list')
    
    def form_valid(self, form):
        messages.success(self.request, "Skill added successfully.")
        return super().form_valid(form)

class SkillUpdateView(LoginRequiredMixin, SuperuserRequiredMixin, UpdateView):
    model = Skill
    form_class = SkillForm
    template_name = "accounts/skill_form.html"
    success_url = reverse_lazy('accounts:skill_list')
    
    def form_valid(self, form):
        messages.success(self.request, "Skill updated successfully.")
        return super().form_valid(form)

class SkillDeleteView(LoginRequiredMixin, SuperuserRequiredMixin, DeleteView):
    model = Skill
    template_name = "accounts/skill_confirm_delete.html"
    success_url = reverse_lazy('accounts:skill_list')

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, "Skill deleted successfully.")
        return super().delete(request, *args, **kwargs)
