from django.contrib.auth import views as auth_views
from django.utils.translation import gettext_lazy as _

from .forms import *


class UserLoginView(auth_views.LoginView):
    form_class = UserAuthenticationForm
    template_name = 'users/login.html'
    redirect_authenticated_user = True

    def dispatch(self, request, *args, **kwargs):
        if settings.RECAPTCHA_ENABLED:
            if 'login_count' not in self.request.session:
                request.session['login_count'] = 0

        return super(UserLoginView, self).dispatch(request, *args, **kwargs)

    def render_to_response(self, context, **response_kwargs):
        if settings.RECAPTCHA_ENABLED:
            if self.request.session['login_count'] >= settings.RECAPTCHA_LOGIN_FAILED_TRIES:
                context['captcha'] = True
                context['form'].fields['captcha'] = ReCaptchaField(
                    widget=ReCaptchaWidget()
                )
            else:
                context['captcha'] = False
            self.request.session['login_count'] += 1
            context['title'] = _('USER_LOGIN_PAGE_TITLE')
        else:
            context['captcha'] = False
        return super(UserLoginView, self).render_to_response(context, **response_kwargs)
