from os.path import splitext

from django.db import models
from django.conf import settings
from django.utils.crypto import get_random_string
from django.utils import formats

from .validators import validate_file
from .formaters import HumanBytes


def user_directory_path(instance, old_file_name):
    filename = get_random_string(length=32)
    name, extension = splitext(old_file_name)
    return f'files/{instance.user.id}/{filename}{extension}'


class File(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    old_file_name = models.CharField(max_length=128, blank=False, null=False)
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

    def to_dict(self):
        return {
            'id': self.id,
            'created_at': formats.localize(self.created_at),
            'old_file_name': self.old_file_name,
            'file_size': HumanBytes.format(self.file.size),
        }

    class Meta:
        db_table = 'files'
