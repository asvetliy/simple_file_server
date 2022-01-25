from django.shortcuts import render, redirect
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.translation import gettext_lazy as _
from django.http import HttpResponse, HttpResponseBadRequest, JsonResponse, FileResponse
from django.conf import settings
from django.views.defaults import page_not_found

from .models import File
from .forms import FileUploadForm
from .json_serializers import FileQuerySetJSONEncoder


class FilesIndexView(LoginRequiredMixin, View):
    def get(self, request):
        if request.GET.get('next'):
            return redirect(request.GET.get('next'))
        context = {
            'title': _('FILES_VIEW_TITLE'),
            'max_file_size': settings.MAX_FILESIZE,
        }
        return render(request, 'files/index.html', context=context)


class FilesUploadView(LoginRequiredMixin, View):
    def post(self, request):
        if len(request.FILES) > 1:
            return HttpResponseBadRequest()
        file = request.FILES['file[]']
        if file is not None:
            form = FileUploadForm(
                data={
                    'old_file_name': file.name,
                    'user': request.user,
                },
                files=request.FILES,
            )
            if form.is_valid():
                f = File.objects.create(
                    user=form.cleaned_data.get('user'),
                    old_file_name=form.cleaned_data.get('old_file_name'),
                    file=form.cleaned_data.get('file'),
                )
                return JsonResponse({
                    'name': form.cleaned_data.get('old_file_name'),
                    'id': f.id,
                })
        return HttpResponse('')


class FilesDeleteView(LoginRequiredMixin, View):
    def post(self, request, file_id):
        try:
            file = File.objects.get(pk=file_id, user_id=request.user.id)
            file.delete()
            return HttpResponse('')
        except File.DoesNotExist:
            return page_not_found(request, None)


class FilesListView(LoginRequiredMixin, View):
    def get(self, request):
        return JsonResponse(File.objects.filter(user_id=request.user.id), encoder=FileQuerySetJSONEncoder, safe=False)


class FilesDownloadView(LoginRequiredMixin, View):
    def get(self, request, file_id):
        try:
            f = File.objects.get(pk=file_id, user_id=request.user.id)
            return FileResponse(open(f.file.path, 'rb'), as_attachment=True, filename=f.old_file_name)
        except File.DoesNotExist:
            return page_not_found(request, None)
