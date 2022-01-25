from django import forms
from django.contrib.auth.forms import AuthenticationForm, UsernameField
from django.conf import settings
from django.utils.translation import gettext_lazy as _

from snowpenguin.django.recaptcha2.fields import ReCaptchaField
from snowpenguin.django.recaptcha2.widgets import ReCaptchaWidget


class UserAuthenticationForm(AuthenticationForm):
    username = UsernameField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('USERS_LOGIN_FORM_USERNAME')}),
    )
    password = forms.CharField(
        strip=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': _('USERS_LOGIN_FORM_PWD')}),
    )

    def __init__(self, request, *args, **kwargs):
        super(UserAuthenticationForm, self).__init__(request, *args, **kwargs)
        if settings.RECAPTCHA_ENABLED:
            if self.request.session.get('login_count', 0) > settings.RECAPTCHA_LOGIN_FAILED_TRIES:
                self.fields['captcha'] = ReCaptchaField(
                    widget=ReCaptchaWidget()
                )
