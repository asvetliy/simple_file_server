from django.db import migrations, models
import django.db.models.deletion


def migrate_storage_quote(apps, schema_editor):
    StoragePlan = apps.get_model('users', 'StoragePlan')
    StorageQuote = apps.get_model('files', 'StorageQuote')
    User = apps.get_model('users', 'User')
    default_quote = StorageQuote.objects.filter(is_default=True).order_by('quota_bytes', 'name').first()

    quotes_by_name = {
        quote.name.lower(): quote
        for quote in StorageQuote.objects.all()
    }
    plans_by_id = {
        plan.id: plan
        for plan in StoragePlan.objects.all()
    }

    for user in User.objects.all():
        quote = default_quote
        plan = plans_by_id.get(user.storage_plan_id)
        if plan is not None:
            quote = quotes_by_name.get(plan.name.lower(), default_quote)
        user.storage_quote = quote
        user.save(update_fields=['storage_quote'])


class Migration(migrations.Migration):

    dependencies = [
        ('files', '0005_storagequote'),
        ('users', '0003_storageplan_user_storage_plan'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='storage_quote',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='users', to='files.storagequote'),
        ),
        migrations.RunPython(migrate_storage_quote, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name='user',
            name='storage_plan',
        ),
        migrations.DeleteModel(
            name='StoragePlan',
        ),
    ]
