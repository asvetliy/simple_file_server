from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin
from files.formaters import HumanBytes

from .models import User


@admin.register(User)
class UserAdmin(ModelAdmin, BaseUserAdmin):
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'username', 'password1', 'password2', 'is_staff', 'is_superuser',
                'storage_quote',
            )
        }
         ),
    )
    fieldsets = (
        (None, {'fields': ('username', 'password', 'storage_quote')}),
        (_('Storage'), {
            'fields': (
                'storage_used_display',
                'storage_remaining_display',
                'storage_usage_display',
            ),
        }),
        (_('Permissions'), {
            'fields': (
                'is_superuser', 'groups', 'user_permissions',
            ),
        }),
        (_('Important dates'), {'fields': ('last_login', 'date_joined',)}),
    )
    readonly_fields = ('storage_used_display', 'storage_remaining_display', 'storage_usage_display',)
    list_display = ('username', 'storage_quote', 'storage_used_display', 'storage_usage_badge', 'is_staff', 'date_joined',)
    list_filter = ('storage_quote', 'is_staff', 'is_superuser', 'is_active',)
    list_per_page = 20
    ordering = ('-date_joined',)

    def storage_used_display(self, obj):
        return HumanBytes.format(obj.storage_used_bytes, True, 2)

    storage_used_display.short_description = _('Storage used')

    def storage_remaining_display(self, obj):
        return HumanBytes.format(obj.storage_remaining_bytes, True, 2)

    storage_remaining_display.short_description = _('Storage remaining')

    def storage_usage_display(self, obj):
        return _('%(used)s of %(quota)s (%(percent)s%%)') % {
            'used': HumanBytes.format(obj.storage_used_bytes, True, 2),
            'quota': HumanBytes.format(obj.storage_quota_bytes, True, 2),
            'percent': obj.storage_usage_percent,
        }

    storage_usage_display.short_description = _('Storage usage')

    def storage_usage_badge(self, obj):
        percent = obj.storage_usage_percent
        color = '#16a34a'
        if percent >= 95:
            color = '#dc2626'
        elif percent >= 80:
            color = '#d97706'
        return format_html(
            '<strong style="color: {};">{}%</strong>',
            color,
            percent,
        )

    storage_usage_badge.short_description = _('Usage')
