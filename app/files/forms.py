from django import forms

from .models import File, Folder


class FileUploadForm(forms.ModelForm):
    file = forms.FileField(
        widget=forms.ClearableFileInput(attrs={
            'class': 'file-input file-input-bordered w-full',
            'name': 'file',
        })
    )

    class Meta:
        model = File
        fields = ('file',)


class FolderCreateForm(forms.ModelForm):
    class Meta:
        model = Folder
        fields = ('name',)
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': 'Folder name',
                'maxlength': 128,
            }),
        }
