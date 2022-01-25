# from os.path import splitext

from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.conf import settings


def validate_file(instance):
    file_size = instance.size
    max_file_size = settings.MAX_FILESIZE

    if file_size > max_file_size * 1024 * 1024:
        raise ValidationError(
            _('The maximum file size that can be uploaded is %d(max_file_size)MB') % max_file_size)

    # name, extension = splitext(instance.name)
    # if extension not in settings.MEDIA_FILES_EXT:
    #     raise ValidationError(_('File upload is only available for permitted file types (%(media_files_list))') % {
    #         'media_files_list': settings.MEDIA_FILES_EXT})

    return instance
