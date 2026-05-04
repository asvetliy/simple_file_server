from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from django.utils import timezone


class BrowserTimezoneMiddleware:
    cookie_name = 'simple_drive_timezone'

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        timezone_name = request.COOKIES.get(self.cookie_name)
        if timezone_name:
            try:
                timezone.activate(ZoneInfo(timezone_name))
            except ZoneInfoNotFoundError:
                timezone.deactivate()
        else:
            timezone.deactivate()

        try:
            return self.get_response(request)
        finally:
            timezone.deactivate()
