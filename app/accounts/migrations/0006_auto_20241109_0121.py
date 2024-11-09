# Generated by Django 5.1.3 on 2024-11-09 01:21

from django.db import migrations


def assign_default_configuration(apps, schema_editor):
    Address = apps.get_model('accounts', 'Address')
    AddressConfiguration = apps.get_model('accounts', 'AddressConfiguration')
    default_config = AddressConfiguration.objects.filter(is_default=True).first()
    if not default_config:
        default_config = AddressConfiguration.objects.first()
    Address.objects.filter(configuration__isnull=True).update(configuration=default_config)

class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0004_addressconfiguration_remove_organisation_address_and_more'),
    ]

    operations = [
        migrations.RunPython(assign_default_configuration),
    ]