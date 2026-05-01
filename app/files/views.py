from datetime import timedelta

from django.contrib import messages
from django.shortcuts import get_object_or_404, render
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.translation import gettext_lazy as _
from django.http import HttpResponse, JsonResponse, FileResponse
from django.conf import settings
from django.utils import timezone

from .models import File, FileShare, Folder
from .forms import FileUploadForm, FolderCreateForm
from .json_serializers import FileQuerySetJSONEncoder


def get_folder_id(request):
    return request.POST.get('folder') or request.GET.get('folder')


def get_current_folder(request):
    folder_id = get_folder_id(request)
    if not folder_id:
        return None
    return get_object_or_404(Folder, pk=folder_id, user_id=request.user.id)


def get_breadcrumbs(folder):
    breadcrumbs = []
    while folder is not None:
        breadcrumbs.append(folder)
        folder = folder.parent
    return list(reversed(breadcrumbs))


def get_user_files(request, current_folder=None):
    if current_folder is None:
        current_folder = get_current_folder(request)
    files = File.objects.filter(user_id=request.user.id, folder=current_folder).order_by('-created_at')
    query = request.GET.get('q', '').strip()
    if query:
        files = files.filter(old_file_name__icontains=query)
    return files


def get_user_folders(request, current_folder=None):
    if current_folder is None:
        current_folder = get_current_folder(request)
    folders = Folder.objects.filter(user_id=request.user.id, parent=current_folder).order_by('name')
    query = request.GET.get('q', '').strip()
    if query:
        folders = folders.filter(name__icontains=query)
    return folders


def get_drive_stats(user):
    files = File.objects.filter(user=user).order_by('-created_at')
    folders = Folder.objects.filter(user=user).order_by('-created_at')
    total_size = sum(file.file.size for file in files if file.file)
    return {
        'file_count': files.count(),
        'folder_count': folders.count(),
        'total_size': total_size,
        'recent_files': files[:5],
        'recent_folders': folders[:5],
        'largest_files': sorted(files, key=lambda item: item.file.size if item.file else 0, reverse=True)[:5],
    }


def render_files_partial(request, status=200, current_folder=None):
    if current_folder is None:
        current_folder = get_current_folder(request)
    context = {
        'files': get_user_files(request, current_folder),
        'folders': get_user_folders(request, current_folder),
        'current_folder': current_folder,
        'breadcrumbs': get_breadcrumbs(current_folder),
        'query': request.GET.get('q', '').strip(),
    }
    return render(request, 'files/partials/file_list_response.html', context=context, status=status)


class FilesDashboardView(LoginRequiredMixin, View):
    def get(self, request):
        context = {
            'title_category': _('Dashboard'),
            **get_drive_stats(request.user),
        }
        return render(request, 'files/dashboard.html', context=context)


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
        for uploaded_file in uploaded_files:
            form = FileUploadForm(files={'file': uploaded_file})
            if form.is_valid():
                File.objects.create(
                    user=request.user,
                    folder=current_folder,
                    old_file_name=uploaded_file.name,
                    file=form.cleaned_data['file'],
                )
                created += 1
            else:
                messages.error(request, _('Could not upload %(name)s: %(error)s') % {
                    'name': uploaded_file.name,
                    'error': form.errors.as_text(),
                })

        if created:
            messages.success(request, _('Uploaded %(count)d file(s).') % {'count': created})

        return render_files_partial(request, status=200 if created else 400)


class FilesDeleteView(LoginRequiredMixin, View):
    def post(self, request, file_id):
        file = get_object_or_404(File, pk=file_id, user_id=request.user.id)
        file.delete()
        messages.success(request, _('Deleted %(name)s.') % {'name': file.old_file_name})
        return render_files_partial(request)


class FolderCreateView(LoginRequiredMixin, View):
    def post(self, request):
        current_folder = get_current_folder(request)
        form = FolderCreateForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data['name'].strip()
            folder, created = Folder.objects.get_or_create(
                user=request.user,
                parent=current_folder,
                name=name,
            )
            if created:
                messages.success(request, _('Created folder %(name)s.') % {'name': folder.name})
            else:
                messages.error(request, _('A folder named %(name)s already exists here.') % {'name': folder.name})
        else:
            messages.error(request, _('Enter a folder name.'))
        return render_files_partial(request)


class FolderDeleteView(LoginRequiredMixin, View):
    def post(self, request, folder_id):
        folder = get_object_or_404(Folder, pk=folder_id, user_id=request.user.id)
        parent = folder.parent
        folder_name = folder.name
        folder.delete()
        messages.success(request, _('Deleted folder %(name)s and its contents.') % {'name': folder_name})
        return render_files_partial(request, current_folder=parent)


class FilesShareView(LoginRequiredMixin, View):
    def post(self, request, file_id):
        file = get_object_or_404(File, pk=file_id, user_id=request.user.id)
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
        })


class FilesUnshareView(LoginRequiredMixin, View):
    def post(self, request, file_id):
        file = get_object_or_404(File, pk=file_id, user_id=request.user.id)
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
        })


class FilesListView(LoginRequiredMixin, View):
    def get(self, request):
        if request.headers.get('HX-Request'):
            return render_files_partial(request)
        return JsonResponse(get_user_files(request), encoder=FileQuerySetJSONEncoder, safe=False)


class FilesDownloadView(LoginRequiredMixin, View):
    def get(self, request, file_id):
        f = get_object_or_404(File, pk=file_id, user_id=request.user.id)
        return FileResponse(open(f.file.path, 'rb'), as_attachment=True, filename=f.old_file_name)


class PublicShareView(View):
    def get(self, request, token):
        share = get_object_or_404(FileShare.objects.select_related('file'), token=token)
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
        share = get_object_or_404(FileShare.objects.select_related('file'), token=token)
        if share.is_expired:
            return render(request, 'files/share_expired.html', {'share': share}, status=410)
        file = share.file
        return FileResponse(open(file.file.path, 'rb'), as_attachment=True, filename=file.old_file_name)
