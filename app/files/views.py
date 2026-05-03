from datetime import timedelta

from django.contrib import messages
from django.shortcuts import get_object_or_404, render
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.translation import gettext_lazy as _
from django.http import HttpResponse, JsonResponse, FileResponse
from django.conf import settings
from django.utils import timezone
from django.db import models

from .models import File, FileShare, Folder
from .forms import FileUploadForm, FolderCreateForm, ItemMoveForm, ItemRenameForm
from .json_serializers import FileQuerySetJSONEncoder


def get_folder_id(request):
    return request.POST.get('folder') or request.GET.get('folder')


def get_current_folder(request):
    folder_id = get_folder_id(request)
    if not folder_id:
        return None
    return get_object_or_404(Folder, pk=folder_id, user_id=request.user.id, deleted_at__isnull=True)


def get_breadcrumbs(folder):
    breadcrumbs = []
    while folder is not None:
        breadcrumbs.append(folder)
        folder = folder.parent
    return list(reversed(breadcrumbs))


def get_user_files(request, current_folder=None):
    if current_folder is None:
        current_folder = get_current_folder(request)
    files = File.objects.filter(
        user_id=request.user.id,
        folder=current_folder,
        deleted_at__isnull=True,
    ).order_by('-created_at')
    query = request.GET.get('q', '').strip()
    if query:
        files = files.filter(old_file_name__icontains=query)
    return files


def get_user_folders(request, current_folder=None):
    if current_folder is None:
        current_folder = get_current_folder(request)
    folders = Folder.objects.filter(
        user_id=request.user.id,
        parent=current_folder,
        deleted_at__isnull=True,
    ).order_by('name')
    query = request.GET.get('q', '').strip()
    if query:
        folders = folders.filter(name__icontains=query)
    return folders


def get_drive_stats(user):
    files = File.objects.filter(user=user, deleted_at__isnull=True).order_by('-created_at')
    folders = Folder.objects.filter(user=user, deleted_at__isnull=True).order_by('-created_at')
    total_size = user.storage_used_bytes
    return {
        'file_count': files.count(),
        'folder_count': folders.count(),
        'total_size': total_size,
        **get_storage_context(user),
        'recent_files': files[:5],
        'recent_folders': folders[:5],
        'largest_files': sorted(files, key=lambda item: item.file.size if item.file else 0, reverse=True)[:5],
    }


def get_storage_context(user):
    return {
        'storage_quote': user.storage_quote,
        'storage_quota_bytes': user.storage_quota_bytes,
        'storage_used_bytes': user.storage_used_bytes,
        'storage_remaining_bytes': user.storage_remaining_bytes,
        'storage_usage_percent': user.storage_usage_percent,
    }


def get_files_context(request, current_folder=None):
    if current_folder is None:
        current_folder = get_current_folder(request)
    return {
        'files': get_user_files(request, current_folder),
        'folders': get_user_folders(request, current_folder),
        'current_folder': current_folder,
        'breadcrumbs': get_breadcrumbs(current_folder),
        'query': request.GET.get('q', '').strip(),
        **get_storage_context(request.user),
    }


def render_files_partial(request, status=200, current_folder=None):
    context = get_files_context(request, current_folder)
    return render(request, 'files/partials/file_list_response.html', context=context, status=status)


def get_destination_folder(request, form):
    destination_id = form.cleaned_data.get('destination')
    if not destination_id:
        return None
    return get_object_or_404(Folder, pk=destination_id, user_id=request.user.id, deleted_at__isnull=True)


def render_item_modal(request, template_context):
    return render(request, 'files/partials/item_modal_content.html', template_context)


def folder_name_exists(user, parent, name, exclude_id=None):
    folders = Folder.objects.filter(user=user, parent=parent, name=name, deleted_at__isnull=True)
    if exclude_id is not None:
        folders = folders.exclude(id=exclude_id)
    return folders.exists()


def soft_delete_folder_tree(folder, deleted_at):
    folder.deleted_at = deleted_at
    folder.save(update_fields=['deleted_at'])
    folder.files.filter(deleted_at__isnull=True).update(deleted_at=deleted_at)
    for child in folder.children.filter(deleted_at__isnull=True):
        soft_delete_folder_tree(child, deleted_at)


def restore_folder_tree(folder):
    folder.deleted_at = None
    folder.save(update_fields=['deleted_at'])
    folder.files.filter(deleted_at__isnull=False).update(deleted_at=None)
    for child in folder.children.filter(deleted_at__isnull=False):
        restore_folder_tree(child)


def get_trash_context(user):
    trashed_folders = Folder.objects.filter(
        user=user,
        deleted_at__isnull=False,
    ).filter(
        models.Q(parent__isnull=True) | models.Q(parent__deleted_at__isnull=True)
    ).order_by('-deleted_at', 'name')
    trashed_files = File.objects.filter(
        user=user,
        deleted_at__isnull=False,
    ).filter(
        models.Q(folder__isnull=True) | models.Q(folder__deleted_at__isnull=True)
    ).order_by('-deleted_at', 'old_file_name')
    return {
        'title_category': _('Trash'),
        'trashed_folders': trashed_folders,
        'trashed_files': trashed_files,
    }


def render_trash_partial(request, status=200):
    return render(request, 'files/partials/trash_response.html', get_trash_context(request.user), status=status)


class FilesDashboardView(LoginRequiredMixin, View):
    def get(self, request):
        context = {
            'title_category': _('Dashboard'),
            **get_drive_stats(request.user),
        }
        return render(request, 'files/dashboard.html', context=context)


class FilesTrashView(LoginRequiredMixin, View):
    def get(self, request):
        return render(request, 'files/trash.html', context=get_trash_context(request.user))


class EmptyTrashView(LoginRequiredMixin, View):
    def post(self, request):
        files = File.objects.filter(user=request.user, deleted_at__isnull=False)
        folders = Folder.objects.filter(user=request.user, deleted_at__isnull=False)
        file_count = files.count()
        folder_count = folders.count()
        files.delete()
        folders.delete()
        messages.success(request, _('Emptied trash: removed %(files)d file(s) and %(folders)d folder(s).') % {
            'files': file_count,
            'folders': folder_count,
        })
        return render_trash_partial(request)


class FilesIndexView(LoginRequiredMixin, View):
    def get(self, request):
        current_folder = get_current_folder(request)
        context = {
            'files': get_user_files(request, current_folder),
            'folders': get_user_folders(request, current_folder),
            'current_folder': current_folder,
            'breadcrumbs': get_breadcrumbs(current_folder),
            'query': request.GET.get('q', '').strip(),
            'upload_form': FileUploadForm(),
            'folder_form': FolderCreateForm(),
            'title_category': _('File Explorer'),
            'max_file_size': settings.MAX_FILESIZE,
            **get_storage_context(request.user),
        }
        return render(request, 'files/index.html', context=context)


class FilesUploadView(LoginRequiredMixin, View):
    def post(self, request):
        current_folder = get_current_folder(request)
        uploaded_files = request.FILES.getlist('file') or request.FILES.getlist('file[]')
        if not uploaded_files:
            messages.error(request, _('Choose at least one file to upload.'))
            return render_files_partial(request, status=400)

        created = 0
        used_bytes = request.user.storage_used_bytes
        quota_bytes = request.user.storage_quota_bytes
        for uploaded_file in uploaded_files:
            form = FileUploadForm(files={'file': uploaded_file})
            if form.is_valid():
                if used_bytes + uploaded_file.size > quota_bytes:
                    messages.error(request, _('Not enough storage for %(name)s. Upgrade your plan or delete files to free space.') % {
                        'name': uploaded_file.name,
                    })
                    continue
                File.objects.create(
                    user=request.user,
                    folder=current_folder,
                    old_file_name=uploaded_file.name,
                    file=form.cleaned_data['file'],
                )
                used_bytes += uploaded_file.size
                created += 1
            else:
                file_errors = form.errors.get('file')
                messages.error(request, _('Could not upload %(name)s: %(error)s') % {
                    'name': uploaded_file.name,
                    'error': ' '.join(file_errors) if file_errors else form.errors.as_text(),
                })

        if created:
            messages.success(request, _('Uploaded %(count)d file(s).') % {'count': created})

        return render_files_partial(request, status=200 if created else 400)


class FilesDeleteView(LoginRequiredMixin, View):
    def post(self, request, file_id):
        file = get_object_or_404(File, pk=file_id, user_id=request.user.id, deleted_at__isnull=True)
        file.deleted_at = timezone.now()
        file.save(update_fields=['deleted_at'])
        messages.success(request, _('Moved %(name)s to trash.') % {'name': file.old_file_name})
        return render_files_partial(request)


class FileRestoreView(LoginRequiredMixin, View):
    def post(self, request, file_id):
        file = get_object_or_404(File, pk=file_id, user_id=request.user.id, deleted_at__isnull=False)
        if file.folder_id and file.folder.deleted_at is not None:
            file.folder = None
        file.deleted_at = None
        file.save(update_fields=['folder', 'deleted_at'])
        messages.success(request, _('Restored %(name)s.') % {'name': file.old_file_name})
        return render_trash_partial(request)


class FilePermanentDeleteView(LoginRequiredMixin, View):
    def post(self, request, file_id):
        file = get_object_or_404(File, pk=file_id, user_id=request.user.id, deleted_at__isnull=False)
        name = file.old_file_name
        file.delete()
        messages.success(request, _('Permanently deleted %(name)s.') % {'name': name})
        return render_trash_partial(request)


class FileRenameView(LoginRequiredMixin, View):
    def get(self, request, file_id):
        file = get_object_or_404(File, pk=file_id, user_id=request.user.id, deleted_at__isnull=True)
        return render_item_modal(request, {
            'action': _('Rename file'),
            'icon': 'pencil',
            'item': file,
            'item_name': file.old_file_name,
            'form': ItemRenameForm(initial={'name': file.old_file_name}),
            'post_url': 'files-rename',
            'post_url_arg': file.id,
            'submit_label': _('Rename'),
            'current_folder': get_current_folder(request),
        })

    def post(self, request, file_id):
        current_folder = get_current_folder(request)
        file = get_object_or_404(File, pk=file_id, user_id=request.user.id, deleted_at__isnull=True)
        form = ItemRenameForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data['name'].strip()
            if name:
                old_name = file.old_file_name
                file.old_file_name = name
                file.save(update_fields=['old_file_name'])
                messages.success(request, _('Renamed %(old)s to %(new)s.') % {
                    'old': old_name,
                    'new': file.old_file_name,
                })
            else:
                messages.error(request, _('Enter a file name.'))
        else:
            messages.error(request, _('Enter a file name.'))
        return render_files_partial(request, current_folder=current_folder)


class FileMoveView(LoginRequiredMixin, View):
    def get(self, request, file_id):
        file = get_object_or_404(File, pk=file_id, user_id=request.user.id, deleted_at__isnull=True)
        return render_item_modal(request, {
            'action': _('Move file'),
            'icon': 'folder-input',
            'item': file,
            'item_name': file.old_file_name,
            'form': ItemMoveForm(user=request.user, initial={
                'destination': str(file.folder_id) if file.folder_id else '',
            }),
            'post_url': 'files-move',
            'post_url_arg': file.id,
            'submit_label': _('Move'),
            'current_folder': get_current_folder(request),
        })

    def post(self, request, file_id):
        current_folder = get_current_folder(request)
        file = get_object_or_404(File, pk=file_id, user_id=request.user.id, deleted_at__isnull=True)
        form = ItemMoveForm(request.POST, user=request.user)
        if form.is_valid():
            destination = get_destination_folder(request, form)
            file.folder = destination
            file.save(update_fields=['folder'])
            messages.success(request, _('Moved %(name)s.') % {'name': file.old_file_name})
        else:
            messages.error(request, _('Choose a destination folder.'))
        return render_files_partial(request, current_folder=current_folder)


class FolderCreateView(LoginRequiredMixin, View):
    def post(self, request):
        current_folder = get_current_folder(request)
        form = FolderCreateForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data['name'].strip()
            folder = Folder.objects.filter(
                user=request.user,
                parent=current_folder,
                name=name,
                deleted_at__isnull=True,
            ).first()
            created = folder is None
            if created:
                folder = Folder.objects.create(user=request.user, parent=current_folder, name=name)
            if created:
                messages.success(request, _('Created folder %(name)s.') % {'name': folder.name})
            else:
                messages.error(request, _('A folder named %(name)s already exists here.') % {'name': folder.name})
        else:
            messages.error(request, _('Enter a folder name.'))
        return render_files_partial(request)


class FolderDeleteView(LoginRequiredMixin, View):
    def post(self, request, folder_id):
        folder = get_object_or_404(Folder, pk=folder_id, user_id=request.user.id, deleted_at__isnull=True)
        parent = folder.parent
        folder_name = folder.name
        soft_delete_folder_tree(folder, timezone.now())
        messages.success(request, _('Moved folder %(name)s and its contents to trash.') % {'name': folder_name})
        return render_files_partial(request, current_folder=parent)


class FolderRestoreView(LoginRequiredMixin, View):
    def post(self, request, folder_id):
        folder = get_object_or_404(Folder, pk=folder_id, user_id=request.user.id, deleted_at__isnull=False)
        parent = folder.parent
        if parent is not None and parent.deleted_at is not None:
            parent = None
        if folder_name_exists(request.user, parent, folder.name, exclude_id=folder.id):
            messages.error(request, _('A folder named %(name)s already exists in the restore destination.') % {
                'name': folder.name,
            })
            return render_trash_partial(request, status=400)
        if folder.parent != parent:
            folder.parent = parent
            folder.save(update_fields=['parent'])
        restore_folder_tree(folder)
        messages.success(request, _('Restored folder %(name)s.') % {'name': folder.name})
        return render_trash_partial(request)


class FolderPermanentDeleteView(LoginRequiredMixin, View):
    def post(self, request, folder_id):
        folder = get_object_or_404(Folder, pk=folder_id, user_id=request.user.id, deleted_at__isnull=False)
        name = folder.name
        folder.delete()
        messages.success(request, _('Permanently deleted folder %(name)s and its contents.') % {'name': name})
        return render_trash_partial(request)


class FolderRenameView(LoginRequiredMixin, View):
    def get(self, request, folder_id):
        folder = get_object_or_404(Folder, pk=folder_id, user_id=request.user.id, deleted_at__isnull=True)
        return render_item_modal(request, {
            'action': _('Rename folder'),
            'icon': 'pencil',
            'item': folder,
            'item_name': folder.name,
            'form': ItemRenameForm(initial={'name': folder.name}),
            'post_url': 'folder-rename',
            'post_url_arg': folder.id,
            'submit_label': _('Rename'),
            'current_folder': get_current_folder(request),
        })

    def post(self, request, folder_id):
        current_folder = get_current_folder(request)
        folder = get_object_or_404(Folder, pk=folder_id, user_id=request.user.id, deleted_at__isnull=True)
        form = ItemRenameForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data['name'].strip()
            if not name:
                messages.error(request, _('Enter a folder name.'))
            elif folder_name_exists(request.user, folder.parent, name, exclude_id=folder.id):
                messages.error(request, _('A folder named %(name)s already exists here.') % {'name': name})
            else:
                old_name = folder.name
                folder.name = name
                folder.save(update_fields=['name'])
                messages.success(request, _('Renamed %(old)s to %(new)s.') % {
                    'old': old_name,
                    'new': folder.name,
                })
        else:
            messages.error(request, _('Enter a folder name.'))
        return render_files_partial(request, current_folder=current_folder)


class FolderMoveView(LoginRequiredMixin, View):
    def get(self, request, folder_id):
        folder = get_object_or_404(Folder, pk=folder_id, user_id=request.user.id, deleted_at__isnull=True)
        return render_item_modal(request, {
            'action': _('Move folder'),
            'icon': 'folder-input',
            'item': folder,
            'item_name': folder.name,
            'form': ItemMoveForm(
                user=request.user,
                excluded_folder=folder,
                initial={'destination': str(folder.parent_id) if folder.parent_id else ''},
            ),
            'post_url': 'folder-move',
            'post_url_arg': folder.id,
            'submit_label': _('Move'),
            'current_folder': get_current_folder(request),
        })

    def post(self, request, folder_id):
        current_folder = get_current_folder(request)
        folder = get_object_or_404(Folder, pk=folder_id, user_id=request.user.id, deleted_at__isnull=True)
        form = ItemMoveForm(request.POST, user=request.user, excluded_folder=folder)
        if form.is_valid():
            destination = get_destination_folder(request, form)
            if folder_name_exists(request.user, destination, folder.name, exclude_id=folder.id):
                messages.error(request, _('A folder named %(name)s already exists in that destination.') % {
                    'name': folder.name,
                })
            else:
                folder.parent = destination
                folder.save(update_fields=['parent'])
                messages.success(request, _('Moved folder %(name)s.') % {'name': folder.name})
        else:
            messages.error(request, _('Choose a destination folder.'))
        return render_files_partial(request, current_folder=current_folder)


class FilesShareView(LoginRequiredMixin, View):
    def post(self, request, file_id):
        current_folder = get_current_folder(request)
        file = get_object_or_404(File, pk=file_id, user_id=request.user.id, deleted_at__isnull=True)
        reissue = request.POST.get('reissue') == '1'
        share = None
        if not reissue:
            share = file.shares.filter(expires_at__gt=timezone.now()).order_by('-created_at').first()
        if share is None:
            expires_at = timezone.now() + timedelta(hours=settings.FILE_SHARE_EXPIRE_HOURS)
            share = FileShare.objects.create(
                file=file,
                created_by=request.user,
                expires_at=expires_at,
            )
        public_url = request.build_absolute_uri(share.get_absolute_url())
        download_url = request.build_absolute_uri(share.get_download_url())
        return render(request, 'files/partials/share_modal_content.html', {
            'share': share,
            'file': file,
            'public_url': public_url,
            'download_url': download_url,
            'share_expire_hours': settings.FILE_SHARE_EXPIRE_HOURS,
            'reissued': reissue,
            'file_list_oob': True,
            **get_files_context(request, current_folder),
        })


class FilesUnshareView(LoginRequiredMixin, View):
    def post(self, request, file_id):
        current_folder = get_current_folder(request)
        file = get_object_or_404(File, pk=file_id, user_id=request.user.id, deleted_at__isnull=True)
        deleted_count, delete_details = file.shares.filter(expires_at__gt=timezone.now()).delete()
        if deleted_count > 0:
            messages.success(request, _('Share link removed for %(name)s.') % {'name': file.old_file_name})
        else:
            messages.info(request, _('This file does not have an active share link.'))

        if request.POST.get('refresh_list') == '1':
            return render_files_partial(request)

        return render(request, 'files/partials/share_modal_content.html', {
            'file': file,
            'share': None,
            'unshared': deleted_count > 0,
            'share_expire_hours': settings.FILE_SHARE_EXPIRE_HOURS,
            'file_list_oob': True,
            **get_files_context(request, current_folder),
        })


class FilesListView(LoginRequiredMixin, View):
    def get(self, request):
        if request.headers.get('HX-Request'):
            return render_files_partial(request)
        return JsonResponse(get_user_files(request), encoder=FileQuerySetJSONEncoder, safe=False)


class FilesDownloadView(LoginRequiredMixin, View):
    def get(self, request, file_id):
        f = get_object_or_404(File, pk=file_id, user_id=request.user.id, deleted_at__isnull=True)
        return FileResponse(open(f.file.path, 'rb'), as_attachment=True, filename=f.old_file_name)


class PublicShareView(View):
    def get(self, request, token):
        share = get_object_or_404(FileShare.objects.select_related('file'), token=token, file__deleted_at__isnull=True)
        if share.is_expired:
            return render(request, 'files/share_expired.html', {'share': share}, status=410)
        public_url = request.build_absolute_uri(share.get_absolute_url())
        download_url = request.build_absolute_uri(share.get_download_url())
        return render(request, 'files/share_public.html', {
            'share': share,
            'file': share.file,
            'public_url': public_url,
            'download_url': download_url,
        })


class PublicShareDownloadView(View):
    def get(self, request, token):
        share = get_object_or_404(FileShare.objects.select_related('file'), token=token, file__deleted_at__isnull=True)
        if share.is_expired:
            return render(request, 'files/share_expired.html', {'share': share}, status=410)
        file = share.file
        return FileResponse(open(file.file.path, 'rb'), as_attachment=True, filename=file.old_file_name)
