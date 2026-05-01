from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse

from .models import File, FileShare, Folder


@admin.register(Folder)
class FolderAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'user_username', 'parent', 'created_at',)
    autocomplete_fields = ('user', 'parent',)
    search_fields = ('name', 'user__username',)
    list_per_page = 20

    def user_username(self, obj: Folder):
        url = reverse('admin:users_user_change', args=(obj.user_id, ))
        return format_html('<a href="{}">{}</a>', url, obj.user.username)

    user_username.admin_order_field = 'user'
    user_username.short_description = 'user'


@admin.register(File)
class UserAccountsAdmin(admin.ModelAdmin):
    list_display = ('id', 'user_username', 'folder', 'old_file_name', 'file', 'created_at', )
    autocomplete_fields = ('user', 'folder', )
    search_fields = ('user__username', 'old_file_name', 'id', )
    list_per_page = 20

    def user_username(self, obj: File):
        url = reverse('admin:users_user_change', args=(obj.user_id, ))
        return format_html('<a href="{}">{}</a>', url, obj.user.username)

    user_username.admin_order_field = 'user'
    user_username.short_description = 'user'


@admin.register(FileShare)
class FileShareAdmin(admin.ModelAdmin):
    list_display = ('id', 'file', 'created_by', 'created_at', 'expires_at', 'is_expired',)
    autocomplete_fields = ('file', 'created_by',)
    search_fields = ('token', 'file__old_file_name', 'created_by__username',)
    list_per_page = 20
