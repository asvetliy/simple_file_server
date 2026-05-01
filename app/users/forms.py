from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm, UsernameField
from django.utils.translation import gettext_lazy as _

from .models import User


class UserAuthenticationForm(AuthenticationForm):
    username = UsernameField(
        widget=forms.TextInput(attrs={
            'class': 'input input-bordered w-full',
            'placeholder': _('Username'),
            'autocomplete': 'username',
        }),
    )
    password = forms.CharField(
        strip=False,
        widget=forms.PasswordInput(attrs={
            'class': 'input input-bordered w-full',
            'placeholder': _('Password'),
            'autocomplete': 'current-password',
        }),
    )


class UserSignupForm(UserCreationForm):
    username = UsernameField(
        widget=forms.TextInput(attrs={
            'class': 'input input-bordered w-full',
            'placeholder': _('Username'),
            'autocomplete': 'username',
        }),
    )
    password1 = forms.CharField(
        label=_('Password'),
        strip=False,
        widget=forms.PasswordInput(attrs={
            'class': 'input input-bordered w-full',
            'placeholder': _('Password'),
            'autocomplete': 'new-password',
        }),
    )
    password2 = forms.CharField(
        label=_('Password confirmation'),
        strip=False,
        widget=forms.PasswordInput(attrs={
            'class': 'input input-bordered w-full',
            'placeholder': _('Confirm password'),
            'autocomplete': 'new-password',
        }),
    )

    class Meta:
        model = User
        fields = ('username',)
