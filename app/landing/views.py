from django.shortcuts import render
from django.utils.translation import gettext_lazy as _
from django.views import View


class HomeView(View):
    def get(self, request):
        return render(request, 'landing/home.html', {
            'title_category': _('Home'),
        })
