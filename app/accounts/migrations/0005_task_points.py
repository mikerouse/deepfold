# Generated by Django 5.1.3 on 2024-11-09 00:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0004_addressconfiguration_remove_organisation_address_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='task',
            name='points',
            field=models.IntegerField(default=0),
        ),
    ]
