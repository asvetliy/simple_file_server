from os.path import splitext

from django import template

from ..formaters import HumanBytes


register = template.Library()


@register.simple_tag
def human_file_size(file_size: int):
    return HumanBytes.format(file_size, True, 2)


@register.simple_tag
def file_extension(file_name: str):
    name, extension = splitext(file_name)
    return extension.replace('.', '')
