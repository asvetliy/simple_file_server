from django.urls import path

from . import views

urlpatterns = [
    path('dashboard', views.FilesDashboardView.as_view(), name='files-dashboard'),
    path('files', views.FilesIndexView.as_view(), name='files-index'),
    path('trash', views.FilesTrashView.as_view(), name='files-trash'),
    path('trash/empty', views.EmptyTrashView.as_view(), name='files-empty-trash'),
    path('folders/create', views.FolderCreateView.as_view(), name='folder-create'),
    path('folders/rename/<folder_id>', views.FolderRenameView.as_view(), name='folder-rename'),
    path('folders/move/<folder_id>', views.FolderMoveView.as_view(), name='folder-move'),
    path('folders/delete/<folder_id>', views.FolderDeleteView.as_view(), name='folder-delete'),
    path('folders/restore/<folder_id>', views.FolderRestoreView.as_view(), name='folder-restore'),
    path('folders/permanent-delete/<folder_id>', views.FolderPermanentDeleteView.as_view(), name='folder-permanent-delete'),
    path('upload', views.FilesUploadView.as_view(), name='files-upload'),
    path('rename/<file_id>', views.FileRenameView.as_view(), name='files-rename'),
    path('move/<file_id>', views.FileMoveView.as_view(), name='files-move'),
    path('delete/<file_id>', views.FilesDeleteView.as_view(), name='files-delete'),
    path('restore/<file_id>', views.FileRestoreView.as_view(), name='files-restore'),
    path('permanent-delete/<file_id>', views.FilePermanentDeleteView.as_view(), name='files-permanent-delete'),
    path('share/<file_id>', views.FilesShareView.as_view(), name='files-share'),
    path('unshare/<file_id>', views.FilesUnshareView.as_view(), name='files-unshare'),
    path('s/<token>', views.PublicShareView.as_view(), name='public-share'),
    path('s/<token>/download', views.PublicShareDownloadView.as_view(), name='public-share-download'),
    path('list', views.FilesListView.as_view(), name='files-list'),
    path('download/<file_id>', views.FilesDownloadView.as_view(), name='files-download'),
]
