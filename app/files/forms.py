from django import forms
from django.forms.utils import ErrorList
from django.utils.datastructures import MultiValueDict

from .models import File


class FileUploadForm(forms.ModelForm):
    def __init__(self, data=None, files=None, auto_id='id_%s', prefix=None, initial=None, error_class=ErrorList,
                 label_suffix=None, empty_permitted=False, instance=None, use_required_attribute=None, renderer=None):
        files = MultiValueDict({'file': files.pop('file[]')})
        super().__init__(data, files, auto_id, prefix, initial, error_class, label_suffix, empty_permitted, instance,
                         use_required_attribute, renderer)

    class Meta:
        model = File
        fields = '__all__'
