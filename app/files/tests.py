import shutil
import tempfile
from datetime import timedelta

from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone

from users.models import User

from .models import File, FileShare, Folder


TEST_MEDIA_ROOT = tempfile.mkdtemp()


@override_settings(MEDIA_ROOT=TEST_MEDIA_ROOT, MAX_FILESIZE=1)
class FileViewsTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEST_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.user = User.objects.create_user(username='alex', password='password123')
        self.other_user = User.objects.create_user(username='casey', password='password123')

    def make_file(self, user=None, folder=None, name='notes.txt', content=b'hello'):
        upload = SimpleUploadedFile(name, content, content_type='text/plain')
        return File.objects.create(
            user=user or self.user,
            folder=folder,
            old_file_name=name,
            file=upload,
        )

    def test_anonymous_users_are_redirected_from_file_views(self):
        file = self.make_file()
        urls = [
            reverse('files-dashboard'),
            reverse('files-index'),
            reverse('files-list'),
            reverse('files-upload'),
            reverse('files-delete', args=[file.id]),
            reverse('files-download', args=[file.id]),
        ]

        for url in urls:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 302)
            self.assertIn(reverse('user-login'), response['Location'])

    def test_upload_accepts_valid_file(self):
        self.client.force_login(self.user)
        upload = SimpleUploadedFile('report.txt', b'file body', content_type='text/plain')

        response = self.client.post(reverse('files-upload'), {'file': upload}, HTTP_HX_REQUEST='true')

        self.assertEqual(response.status_code, 200)
        saved_file = File.objects.get(user=self.user)
        self.assertEqual(saved_file.old_file_name, 'report.txt')
        self.assertContains(response, 'report.txt')

    def test_upload_rejects_file_over_max_size(self):
        self.client.force_login(self.user)
        too_large = SimpleUploadedFile('large.txt', b'x' * ((1024 * 1024) + 1), content_type='text/plain')

        response = self.client.post(reverse('files-upload'), {'file': too_large}, HTTP_HX_REQUEST='true')

        self.assertEqual(response.status_code, 400)
        self.assertFalse(File.objects.filter(user=self.user).exists())

    def test_file_list_only_shows_current_user_files_and_supports_search(self):
        self.client.force_login(self.user)
        own_file = self.make_file(name='budget.txt')
        self.make_file(user=self.other_user, name='private.txt')
        self.make_file(name='photo.jpg')

        response = self.client.get(reverse('files-list'), {'q': 'budget'}, HTTP_HX_REQUEST='true')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, own_file.old_file_name)
        self.assertNotContains(response, 'private.txt')
        self.assertNotContains(response, 'photo.jpg')

    def test_user_can_download_own_file_with_original_filename(self):
        self.client.force_login(self.user)
        file = self.make_file(name='original.txt')

        response = self.client.get(reverse('files-download', args=[file.id]))

        self.assertEqual(response.status_code, 200)
        self.assertIn('filename="original.txt"', response['Content-Disposition'])

    def test_user_can_create_expiring_share_for_own_file(self):
        self.client.force_login(self.user)
        file = self.make_file(name='shared.txt')

        response = self.client.post(reverse('files-share', args=[file.id]), HTTP_HX_REQUEST='true')

        self.assertEqual(response.status_code, 200)
        share = FileShare.objects.get(file=file)
        self.assertEqual(share.created_by, self.user)
        self.assertGreater(share.expires_at, timezone.now())
        self.assertContains(response, reverse('public-share', args=[share.token]))
        self.assertContains(response, 'data-qr-url')

    def test_share_reuses_existing_active_share(self):
        self.client.force_login(self.user)
        file = self.make_file(name='shared.txt')
        first_response = self.client.post(reverse('files-share', args=[file.id]), HTTP_HX_REQUEST='true')
        first_share = FileShare.objects.get(file=file)

        second_response = self.client.post(reverse('files-share', args=[file.id]), HTTP_HX_REQUEST='true')

        self.assertEqual(first_response.status_code, 200)
        self.assertEqual(second_response.status_code, 200)
        self.assertEqual(FileShare.objects.filter(file=file).count(), 1)
        self.assertContains(second_response, first_share.token)

    def test_share_reissue_creates_new_share(self):
        self.client.force_login(self.user)
        file = self.make_file(name='shared.txt')
        self.client.post(reverse('files-share', args=[file.id]), HTTP_HX_REQUEST='true')
        first_share = FileShare.objects.get(file=file)

        response = self.client.post(reverse('files-share', args=[file.id]), {'reissue': '1'}, HTTP_HX_REQUEST='true')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(FileShare.objects.filter(file=file).count(), 2)
        self.assertNotEqual(FileShare.objects.filter(file=file).order_by('-created_at').first().token, first_share.token)
        self.assertContains(response, 'fresh share link')

    def test_unshare_removes_active_share(self):
        self.client.force_login(self.user)
        file = self.make_file(name='shared.txt')
        active_share = FileShare.objects.create(
            file=file,
            created_by=self.user,
            expires_at=timezone.now() + timedelta(hours=1),
        )

        response = self.client.post(reverse('files-unshare', args=[file.id]), HTTP_HX_REQUEST='true')

        self.assertEqual(response.status_code, 200)
        self.assertFalse(FileShare.objects.filter(id=active_share.id).exists())
        self.assertContains(response, 'removed')
        self.assertContains(response, 'Create share link')

    def test_unshare_does_not_touch_other_users_file(self):
        self.client.force_login(self.user)
        other_file = self.make_file(user=self.other_user, name='other.txt')
        FileShare.objects.create(
            file=other_file,
            created_by=self.other_user,
            expires_at=timezone.now() + timedelta(hours=1),
        )

        response = self.client.post(reverse('files-unshare', args=[other_file.id]), HTTP_HX_REQUEST='true')

        self.assertEqual(response.status_code, 404)
        self.assertEqual(FileShare.objects.filter(file=other_file).count(), 1)

    def test_file_list_shows_unshare_button_for_active_share(self):
        self.client.force_login(self.user)
        file = self.make_file(name='shared.txt')
        FileShare.objects.create(
            file=file,
            created_by=self.user,
            expires_at=timezone.now() + timedelta(hours=1),
        )

        response = self.client.get(reverse('files-list'), HTTP_HX_REQUEST='true')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse('files-unshare', args=[file.id]))

    def test_row_unshare_refresh_hides_button_when_share_removed(self):
        self.client.force_login(self.user)
        file = self.make_file(name='shared.txt')
        FileShare.objects.create(
            file=file,
            created_by=self.user,
            expires_at=timezone.now() + timedelta(hours=1),
        )

        response = self.client.post(
            reverse('files-unshare', args=[file.id]),
            {'refresh_list': '1'},
            HTTP_HX_REQUEST='true',
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(FileShare.objects.filter(file=file, expires_at__gt=timezone.now()).exists())
        self.assertNotContains(response, reverse('files-unshare', args=[file.id]))

    def test_user_cannot_share_another_users_file(self):
        self.client.force_login(self.user)
        other_file = self.make_file(user=self.other_user, name='other.txt')

        response = self.client.post(reverse('files-share', args=[other_file.id]), HTTP_HX_REQUEST='true')

        self.assertEqual(response.status_code, 404)
        self.assertFalse(FileShare.objects.exists())

    def test_public_share_downloads_file_until_expired(self):
        file = self.make_file(name='public.txt')
        share = FileShare.objects.create(
            file=file,
            created_by=self.user,
            expires_at=timezone.now() + timedelta(hours=1),
        )

        page_response = self.client.get(reverse('public-share', args=[share.token]))
        download_response = self.client.get(reverse('public-share-download', args=[share.token]))

        self.assertEqual(page_response.status_code, 200)
        self.assertContains(page_response, 'public.txt')
        self.assertEqual(download_response.status_code, 200)
        self.assertIn('filename="public.txt"', download_response['Content-Disposition'])

    def test_expired_public_share_returns_gone(self):
        file = self.make_file(name='expired.txt')
        share = FileShare.objects.create(
            file=file,
            created_by=self.user,
            expires_at=timezone.now() - timedelta(minutes=1),
        )

        page_response = self.client.get(reverse('public-share', args=[share.token]))
        download_response = self.client.get(reverse('public-share-download', args=[share.token]))

        self.assertEqual(page_response.status_code, 410)
        self.assertEqual(download_response.status_code, 410)
        self.assertContains(page_response, 'expired', status_code=410)

    def test_user_cannot_download_or_delete_another_users_file(self):
        self.client.force_login(self.user)
        other_file = self.make_file(user=self.other_user, name='other.txt')

        download_response = self.client.get(reverse('files-download', args=[other_file.id]))
        delete_response = self.client.post(reverse('files-delete', args=[other_file.id]), HTTP_HX_REQUEST='true')

        self.assertEqual(download_response.status_code, 404)
        self.assertEqual(delete_response.status_code, 404)
        self.assertTrue(File.objects.filter(id=other_file.id).exists())

    def test_delete_requires_post_and_csrf(self):
        file = self.make_file()
        csrf_client = Client(enforce_csrf_checks=True)
        csrf_client.force_login(self.user)

        get_response = csrf_client.get(reverse('files-delete', args=[file.id]))
        post_response = csrf_client.post(reverse('files-delete', args=[file.id]), HTTP_HX_REQUEST='true')

        self.assertEqual(get_response.status_code, 405)
        self.assertEqual(post_response.status_code, 403)
        self.assertTrue(File.objects.filter(id=file.id).exists())

    def test_delete_removes_own_file_and_returns_partial(self):
        self.client.force_login(self.user)
        file = self.make_file(name='remove-me.txt')

        response = self.client.post(reverse('files-delete', args=[file.id]), HTTP_HX_REQUEST='true')

        self.assertEqual(response.status_code, 200)
        self.assertFalse(File.objects.filter(id=file.id).exists())
        self.assertContains(response, 'files-panel')

    def test_dashboard_shows_drive_totals(self):
        self.client.force_login(self.user)
        Folder.objects.create(user=self.user, name='Projects')
        self.make_file(name='summary.txt', content=b'hello world')

        response = self.client.get(reverse('files-dashboard'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Drive dashboard')
        self.assertContains(response, 'summary.txt')
        self.assertContains(response, 'Projects')

    def test_folder_create_and_browse(self):
        self.client.force_login(self.user)

        create_response = self.client.post(
            reverse('folder-create'),
            {'name': 'Projects'},
            HTTP_HX_REQUEST='true',
        )
        folder = Folder.objects.get(user=self.user, name='Projects')
        browse_response = self.client.get(reverse('files-index'), {'folder': folder.id})

        self.assertEqual(create_response.status_code, 200)
        self.assertContains(create_response, 'Projects')
        self.assertContains(browse_response, 'Projects')
        self.assertContains(browse_response, 'Upload files')

    def test_upload_into_folder_only_appears_in_that_folder(self):
        self.client.force_login(self.user)
        folder = Folder.objects.create(user=self.user, name='Projects')
        upload = SimpleUploadedFile('inside.txt', b'folder file', content_type='text/plain')

        self.client.post(reverse('files-upload'), {'folder': folder.id, 'file': upload}, HTTP_HX_REQUEST='true')
        root_response = self.client.get(reverse('files-list'), HTTP_HX_REQUEST='true')
        folder_response = self.client.get(reverse('files-list'), {'folder': folder.id}, HTTP_HX_REQUEST='true')

        self.assertEqual(File.objects.get(old_file_name='inside.txt').folder, folder)
        self.assertNotContains(root_response, 'inside.txt')
        self.assertContains(folder_response, 'inside.txt')

    def test_folder_delete_removes_nested_files(self):
        self.client.force_login(self.user)
        folder = Folder.objects.create(user=self.user, name='Archive')
        self.make_file(name='old.txt', user=self.user, folder=folder)

        response = self.client.post(reverse('folder-delete', args=[folder.id]), HTTP_HX_REQUEST='true')

        self.assertEqual(response.status_code, 200)
        self.assertFalse(Folder.objects.filter(id=folder.id).exists())
        self.assertFalse(File.objects.filter(old_file_name='old.txt').exists())

    def test_folder_row_shows_nested_file_folder_and_size_totals(self):
        self.client.force_login(self.user)
        folder = Folder.objects.create(user=self.user, name='Projects')
        nested = Folder.objects.create(user=self.user, parent=folder, name='Designs')
        self.make_file(name='root.txt', user=self.user, folder=folder, content=b'12345')
        self.make_file(name='nested.txt', user=self.user, folder=nested, content=b'1234567890')

        response = self.client.get(reverse('files-list'), HTTP_HX_REQUEST='true')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Projects')
        self.assertContains(response, '2 files')
        self.assertContains(response, '1 folders')
        self.assertContains(response, '15.00 B')
