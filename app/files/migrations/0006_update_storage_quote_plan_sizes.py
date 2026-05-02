from django.conf import settings
from django.db import migrations


def update_storage_quote_sizes(apps, schema_editor):
    StorageQuote = apps.get_model('files', 'StorageQuote')
    plans = [
        ('Free', settings.DEFAULT_STORAGE_QUOTA_BYTES, True),
        ('Standard', 10 * 1024 * 1024 * 1024, False),
        ('Premium', 1024 * 1024 * 1024 * 1024, False),
    ]
    for name, quota_bytes, is_default in plans:
        StorageQuote.objects.update_or_create(
            name=name,
            defaults={
                'quota_bytes': quota_bytes,
                'is_default': is_default,
            },
        )
    default_quote = StorageQuote.objects.get(name='Free')
    StorageQuote.objects.exclude(id=default_quote.id).update(is_default=False)


class Migration(migrations.Migration):

    dependencies = [
        ('files', '0005_storagequote'),
    ]

    operations = [
        migrations.RunPython(update_storage_quote_sizes, migrations.RunPython.noop),
    ]
