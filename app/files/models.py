from os.path import splitext

from django.db import models
from django.db.models import Q
from django.conf import settings
from django.urls import reverse
from django.utils.crypto import get_random_string
from django.utils import formats, timezone

from .validators import validate_file
from .formaters import HumanBytes


class StorageQuote(models.Model):
    name = models.CharField(max_length=80, unique=True)
    quota_bytes = models.PositiveBigIntegerField(default=settings.DEFAULT_STORAGE_QUOTA_BYTES)
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.is_default:
            StorageQuote.objects.exclude(pk=self.pk).update(is_default=False)

    class Meta:
        db_table = 'storage_quotes'
        ordering = ('quota_bytes', 'name')


class Folder(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, models.CASCADE)
    parent = models.ForeignKey('self', models.CASCADE, blank=True, null=True, related_name='children')
    name = models.CharField(max_length=128)
    created_at = models.DateTimeField(auto_now_add=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return self.name

    @property
    def total_folder_count(self):
        return sum(1 + child.total_folder_count for child in self.children.filter(deleted_at__isnull=True))

    @property
    def total_file_count(self):
        return self.files.filter(deleted_at__isnull=True).count() + sum(
            child.total_file_count for child in self.children.filter(deleted_at__isnull=True)
        )

    @property
    def total_size(self):
        files_size = sum(file.file.size for file in self.files.filter(deleted_at__isnull=True) if file.file)
        return files_size + sum(child.total_size for child in self.children.filter(deleted_at__isnull=True))

    class Meta:
        db_table = 'folders'
        ordering = ('name',)
        constraints = [
            models.UniqueConstraint(
                fields=('user', 'parent', 'name'),
                name='unique_folder_name_per_parent',
                condition=Q(deleted_at__isnull=True),
            ),
        ]


def user_directory_path(instance, old_file_name):
    filename = get_random_string(length=32)
    name, extension = splitext(old_file_name)
    return f'files/{instance.user.id}/{filename}{extension}'


class File(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, models.CASCADE)
    folder = models.ForeignKey(Folder, models.CASCADE, blank=True, null=True, related_name='files')
    created_at = models.DateTimeField(auto_now_add=True)
    old_file_name = models.CharField(max_length=128, blank=False, null=False)
    deleted_at = models.DateTimeField(blank=True, null=True)
    file = models.FileField(
        upload_to=user_directory_path,
        blank=False,
        null=False,
        validators=[validate_file],
        verbose_name='file',
        name='file',
        db_column='file'
    )

    def __str__(self):
        return str(self.id)

    def get_color_id(self):
        size_part = (settings.MAX_FILESIZE*1024*1024)/3

        if self.file.size <= size_part:
            return 1
        if size_part <= self.file.size <= size_part*2:
            return 2
        if size_part*2 <= self.file.size <= settings.MAX_FILESIZE or self.file.size > settings.MAX_FILESIZE:
            return 3

        return 1

    @property
    def active_share(self):
        return self.shares.filter(expires_at__gt=timezone.now()).order_by('-created_at').first()

    def to_dict(self):

        return {
            'id': self.id,
            'created_at': formats.localize(self.created_at),
            'old_file_name': self.old_file_name,
            'human_file_size': HumanBytes.format(self.file.size, True, 2),
            'badge_color_id': self.get_color_id(),
            'file_size': self.file.size,
            'folder_id': self.folder_id,
        }

    class Meta:
        db_table = 'files'


def generate_share_token():
    return get_random_string(length=48)


class FileShare(models.Model):
    file = models.ForeignKey(File, models.CASCADE, related_name='shares')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, models.CASCADE, related_name='file_shares')
    token = models.CharField(max_length=64, unique=True, default=generate_share_token)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    @property
    def is_expired(self):
        return self.expires_at <= timezone.now()

    def __str__(self):
        return self.token

    def get_absolute_url(self):
        return reverse('public-share', args=[self.token])

    def get_download_url(self):
        return reverse('public-share-download', args=[self.token])

    class Meta:
        db_table = 'file_shares'
        ordering = ('-created_at',)
