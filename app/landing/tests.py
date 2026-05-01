from django.test import TestCase
from django.urls import reverse

from users.models import User


class HomePageTests(TestCase):
    def test_home_page_is_public(self):
        response = self.client.get(reverse('home'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Your files, folders, and drive overview')
        self.assertContains(response, reverse('user-login'))
        self.assertContains(response, reverse('user-signup'))

    def test_home_page_links_authenticated_user_to_app(self):
        user = User.objects.create_user(username='alex', password='password123')
        self.client.force_login(user)

        response = self.client.get(reverse('home'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse('files-dashboard'))
        self.assertContains(response, reverse('files-index'))
        self.assertContains(response, reverse('user-logout'))
        self.assertContains(response, 'Logout')
