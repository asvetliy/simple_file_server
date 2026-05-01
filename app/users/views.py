from django.contrib.auth import views as auth_views
from django.contrib.auth import login
from django.shortcuts import redirect, render
from django.views import View

from .forms import UserAuthenticationForm, UserSignupForm


class UserLoginView(auth_views.LoginView):
    form_class = UserAuthenticationForm
    template_name = 'users/login.html'
    redirect_authenticated_user = True

    def get_template_names(self):
        if self.request.headers.get('HX-Request'):
            return ['users/partials/login_form.html']
        return [self.template_name]


class UserSignupView(View):
    def get(self, request):
        if request.user.is_authenticated:
            return redirect('files-index')
        template_name = 'users/partials/signup_form.html' if request.headers.get('HX-Request') else 'users/signup.html'
        return render(request, template_name, {
            'form': UserSignupForm(),
            'title': 'Sign up',
            'page': 'signup',
        })

    def post(self, request):
        if request.user.is_authenticated:
            return redirect('files-index')
        form = UserSignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('files-index')
        template_name = 'users/partials/signup_form.html' if request.headers.get('HX-Request') else 'users/signup.html'
        return render(request, template_name, {
            'form': form,
            'title': 'Sign up',
            'page': 'signup',
        })
