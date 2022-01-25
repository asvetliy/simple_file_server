from django.urls import path
from django.views.decorators.csrf import csrf_exempt

from . import views

urlpatterns = [
    path('', views.FilesIndexView.as_view(), name='files-index'),
    path('upload', views.FilesUploadView.as_view(), name='files-upload'),
    path('delete/<file_id>', csrf_exempt(views.FilesDeleteView.as_view()), name='files-delete'),
    path('list', views.FilesListView.as_view(), name='files-list'),
    path('download/<file_id>', views.FilesDownloadView.as_view(), name='files-download'),
]
