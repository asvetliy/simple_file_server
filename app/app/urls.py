from django.contrib import admin
from django.urls import path, include, re_path
from django.conf.urls.i18n import i18n_patterns
from django.contrib.admin.views.decorators import staff_member_required
from django.views.static import serve
from django.conf import settings


@staff_member_required(login_url=settings.LOGIN_URL)
def protected_serve(request, file_path, document_root=None, show_indexes=False):
    return serve(request, file_path, document_root, show_indexes)


urlpatterns = [
    path('OBzwyYM/', admin.site.urls),
    re_path(r'^%s(?P<file_path>.*)$' % settings.MEDIA_URL[1:], protected_serve, {'document_root': settings.MEDIA_ROOT}),
]
urlpatterns += i18n_patterns(
    path('', include('landing.urls')),
    prefix_default_language=False
)
urlpatterns += i18n_patterns(
    path('', include('files.urls')),
    prefix_default_language=False
)
urlpatterns += i18n_patterns(
    path('', include('users.urls')),
    prefix_default_language=False
)
urlpatterns += i18n_patterns(
    path('i18n/', include('django.conf.urls.i18n')),
    prefix_default_language=False
)
# urlpatterns += i18n_patterns(
#     path('', include('torrents.urls')),
#     prefix_default_language=False
# )
