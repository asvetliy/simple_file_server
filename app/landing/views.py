from django.shortcuts import render
from django.utils.translation import gettext_lazy as _
from django.views import View

from files.models import StorageQuote


class HomeView(View):
    def get(self, request):
        return render(request, 'landing/home.html', {
            'title_category': _('Home'),
            'storage_quotes': StorageQuote.objects.order_by('quota_bytes', 'name'),
        })
