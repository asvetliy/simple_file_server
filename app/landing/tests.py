from django.test import TestCase
from django.urls import reverse

from files.models import StorageQuote
from users.models import User


class HomePageTests(TestCase):
    def test_seeded_storage_quotes_have_expected_sizes(self):
        self.assertEqual(StorageQuote.objects.get(name='Free').quota_bytes, 1024 * 1024 * 1024)
        self.assertEqual(StorageQuote.objects.get(name='Standard').quota_bytes, 10 * 1024 * 1024 * 1024)
        self.assertEqual(StorageQuote.objects.get(name='Premium').quota_bytes, 1024 * 1024 * 1024 * 1024)

    def test_home_page_is_public(self):
        response = self.client.get(reverse('home'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Secure file storage for your team')
        self.assertContains(response, reverse('user-login'))
        self.assertContains(response, reverse('user-signup'))
        self.assertContains(response, 'Storage plans')
        self.assertContains(response, 'Built for daily file work')
        self.assertContains(response, 'Free')
        self.assertContains(response, 'Standard')
        self.assertContains(response, 'Premium')

    def test_home_page_links_authenticated_user_to_app(self):
        user = User.objects.create_user(username='alex', password='password123')
        self.client.force_login(user)

        response = self.client.get(reverse('home'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse('files-dashboard'))
        self.assertContains(response, reverse('files-index'))
        self.assertContains(response, reverse('user-logout'))
        self.assertContains(response, 'Logout')
