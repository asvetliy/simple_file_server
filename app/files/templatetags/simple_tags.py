from os.path import splitext

from django import template
from django.utils.dateformat import format as date_format
from django.utils import timezone

from ..formaters import HumanBytes


register = template.Library()


@register.simple_tag
def human_file_size(file_size: int):
    return HumanBytes.format(file_size, True, 2)


@register.filter
def human_bytes(file_size: int):
    return HumanBytes.format(file_size, True, 2)


@register.simple_tag
def file_extension(file_name: str):
    name, extension = splitext(file_name)
    return extension.replace('.', '')


@register.filter
def file_type_label(file_name: str):
    name, extension = splitext(file_name)
    extension = extension.replace('.', '').upper()
    return extension or 'FILE'


@register.filter
def local_datetime(value, fmt='Y-m-d H:i'):
    if not value:
        return ''
    return date_format(timezone.localtime(value), fmt)


@register.filter
def local_iso(value):
    if not value:
        return ''
    return timezone.localtime(value).isoformat()
