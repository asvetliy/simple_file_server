from django.shortcuts import render


class ErrorView404(object):
    def get(self, request):
        return render(request, '404.html')


class ErrorView500(object):
    def get(self, request):
        return render(request, '500.html')
