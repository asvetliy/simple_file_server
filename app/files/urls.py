from django.urls import path

from . import views

urlpatterns = [
    path('dashboard', views.FilesDashboardView.as_view(), name='files-dashboard'),
    path('files', views.FilesIndexView.as_view(), name='files-index'),
    path('folders/create', views.FolderCreateView.as_view(), name='folder-create'),
    path('folders/delete/<folder_id>', views.FolderDeleteView.as_view(), name='folder-delete'),
    path('upload', views.FilesUploadView.as_view(), name='files-upload'),
    path('delete/<file_id>', views.FilesDeleteView.as_view(), name='files-delete'),
    path('share/<file_id>', views.FilesShareView.as_view(), name='files-share'),
    path('unshare/<file_id>', views.FilesUnshareView.as_view(), name='files-unshare'),
    path('s/<token>', views.PublicShareView.as_view(), name='public-share'),
    path('s/<token>/download', views.PublicShareDownloadView.as_view(), name='public-share-download'),
    path('list', views.FilesListView.as_view(), name='files-list'),
    path('download/<file_id>', views.FilesDownloadView.as_view(), name='files-download'),
]
