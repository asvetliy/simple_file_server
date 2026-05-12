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
                'autofocus': 'autofocus',
            }),
        }


class ItemRenameForm(forms.Form):
    name = forms.CharField(
        max_length=128,
        widget=forms.TextInput(attrs={
            'class': 'input input-bordered w-full',
            'placeholder': 'Name',
            'maxlength': 128,
            'autofocus': 'autofocus',
        }),
    )


class ItemMoveForm(forms.Form):
    destination = forms.ChoiceField(
        required=False,
        widget=forms.Select(attrs={
            'class': 'select select-bordered w-full',
        }),
    )

    def get_descendant_folder_ids(self, folder):
        ids = set()
        for child in folder.children.all():
            ids.add(child.id)
            ids.update(self.get_descendant_folder_ids(child))
        return ids

    def __init__(self, *args, user, excluded_folder=None, **kwargs):
        super().__init__(*args, **kwargs)
        folders = Folder.objects.filter(user=user, deleted_at__isnull=True).order_by('name')
        excluded_ids = set()
        if excluded_folder is not None:
            excluded_ids = self.get_descendant_folder_ids(excluded_folder)
            excluded_ids.add(excluded_folder.id)
        choices = [('', 'root')]
        choices.extend(
            (str(folder.id), folder.name)
            for folder in folders
            if folder.id not in excluded_ids
        )
        self.fields['destination'].choices = choices
