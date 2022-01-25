from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import QuerySet


class FileQuerySetJSONEncoder(DjangoJSONEncoder):
    def default(self, obj):
        if isinstance(obj, QuerySet):
            return [f.to_dict() for f in list(obj)]
        return super().default(obj)
