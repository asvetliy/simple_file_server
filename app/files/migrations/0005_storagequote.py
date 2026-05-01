from django.conf import settings
from django.db import migrations, models


def create_storage_quotes(apps, schema_editor):
    StorageQuote = apps.get_model('files', 'StorageQuote')
    plans = [
        ('Free', settings.DEFAULT_STORAGE_QUOTA_BYTES, True),
        ('Standard', 10 * 1024 * 1024 * 1024, False),
        ('Premium', 100 * 1024 * 1024 * 1024, False),
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


def remove_storage_quotes(apps, schema_editor):
    StorageQuote = apps.get_model('files', 'StorageQuote')
    StorageQuote.objects.filter(name__in=['Free', 'Standard', 'Premium']).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('files', '0004_fileshare'),
    ]

    operations = [
        migrations.CreateModel(
            name='StorageQuote',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=80, unique=True)),
                ('quota_bytes', models.PositiveBigIntegerField(default=settings.DEFAULT_STORAGE_QUOTA_BYTES)),
                ('is_default', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'db_table': 'storage_quotes',
                'ordering': ('quota_bytes', 'name'),
            },
        ),
        migrations.RunPython(create_storage_quotes, remove_storage_quotes),
    ]
