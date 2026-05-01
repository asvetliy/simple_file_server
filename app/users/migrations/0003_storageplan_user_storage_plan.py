from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def create_default_plan(apps, schema_editor):
    StoragePlan = apps.get_model('users', 'StoragePlan')
    User = apps.get_model('users', 'User')
    default_plan, _ = StoragePlan.objects.get_or_create(
        name='Free',
        defaults={
            'quota_bytes': settings.DEFAULT_STORAGE_QUOTA_BYTES,
            'is_default': True,
        },
    )
    StoragePlan.objects.exclude(id=default_plan.id).update(is_default=False)
    User.objects.filter(storage_plan__isnull=True).update(storage_plan=default_plan)


def remove_default_plan(apps, schema_editor):
    StoragePlan = apps.get_model('users', 'StoragePlan')
    StoragePlan.objects.filter(name='Free').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_alter_user_managers'),
    ]

    operations = [
        migrations.CreateModel(
            name='StoragePlan',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=80, unique=True)),
                ('quota_bytes', models.PositiveBigIntegerField(default=settings.DEFAULT_STORAGE_QUOTA_BYTES)),
                ('is_default', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'db_table': 'storage_plans',
                'ordering': ('quota_bytes', 'name'),
            },
        ),
        migrations.AddField(
            model_name='user',
            name='storage_plan',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='users', to='users.storageplan'),
        ),
        migrations.RunPython(create_default_plan, remove_default_plan),
    ]
