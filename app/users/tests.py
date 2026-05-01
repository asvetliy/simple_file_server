from django.test import TestCase
from django.urls import reverse

from files.models import StorageQuote

from .models import User


class SignupTests(TestCase):
    def test_storage_quote_default_is_unique(self):
        first_plan = StorageQuote.objects.create(name='First', quota_bytes=1024, is_default=True)
        second_plan = StorageQuote.objects.create(name='Second', quota_bytes=2048, is_default=True)

        first_plan.refresh_from_db()
        second_plan.refresh_from_db()

        self.assertFalse(first_plan.is_default)
        self.assertTrue(second_plan.is_default)

    def test_login_htmx_get_returns_auth_panel_partial(self):
        response = self.client.get(reverse('user-login'), HTTP_HX_REQUEST='true')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="auth-panel"')
        self.assertNotContains(response, '<html')

    def test_signup_htmx_get_returns_auth_panel_partial(self):
        response = self.client.get(reverse('user-signup'), HTTP_HX_REQUEST='true')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="auth-panel"')
        self.assertNotContains(response, '<html')

    def test_signup_creates_and_logs_in_user(self):
        response = self.client.post(reverse('user-signup'), {
            'username': 'new-user',
            'password1': 'strong-password-123',
            'password2': 'strong-password-123',
        })

        self.assertRedirects(response, reverse('files-index'))
        self.assertTrue(User.objects.filter(username='new-user').exists())
        self.assertEqual(int(self.client.session['_auth_user_id']), User.objects.get(username='new-user').id)

    def test_signup_assigns_default_storage_quote(self):
        StorageQuote.objects.update(is_default=False)
        default_quote = StorageQuote.objects.create(name='Starter', quota_bytes=1024, is_default=True)

        response = self.client.post(reverse('user-signup'), {
            'username': 'plan-user',
            'password1': 'strong-password-123',
            'password2': 'strong-password-123',
        })

        self.assertRedirects(response, reverse('files-index'))
        self.assertEqual(User.objects.get(username='plan-user').storage_quote, default_quote)

    def test_authenticated_user_is_redirected_from_signup(self):
        user = User.objects.create_user(username='alex', password='password123')
        self.client.force_login(user)

        response = self.client.get(reverse('user-signup'))

        self.assertRedirects(response, reverse('files-index'))
