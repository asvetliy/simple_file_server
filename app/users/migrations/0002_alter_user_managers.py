# Generated by Django 3.2.11 on 2022-01-13 13:51

from django.db import migrations
import users.models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelManagers(
            name='user',
            managers=[
                ('objects', users.models.CustomUserManager()),
            ],
        ),
    ]
