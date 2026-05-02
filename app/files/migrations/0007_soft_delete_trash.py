from django.db import migrations, models
from django.db.models import Q


class Migration(migrations.Migration):

    dependencies = [
        ('files', '0006_update_storage_quote_plan_sizes'),
    ]

    operations = [
        migrations.AddField(
            model_name='file',
            name='deleted_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='folder',
            name='deleted_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.RemoveConstraint(
            model_name='folder',
            name='unique_folder_name_per_parent',
        ),
        migrations.AddConstraint(
            model_name='folder',
            constraint=models.UniqueConstraint(
                condition=Q(deleted_at__isnull=True),
                fields=('user', 'parent', 'name'),
                name='unique_folder_name_per_parent',
            ),
        ),
    ]
