from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse

from .models import File


@admin.register(File)
class UserAccountsAdmin(admin.ModelAdmin):
    list_display = ('id', 'user_username', 'old_file_name', 'file', 'created_at', )
    autocomplete_fields = ('user', )
    search_fields = ('user__username', 'id', )
    list_per_page = 20

    def user_username(self, obj: File):
        url = reverse('admin:users_user_change', args=(obj.user_id, ))
        return format_html(f'<a href="{url}">{obj.user.username}</a>')

    user_username.admin_order_field = 'user'
    user_username.short_description = 'user'