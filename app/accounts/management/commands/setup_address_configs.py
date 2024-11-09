# accounts/management/commands/setup_address_configs.py
from django.core.management.base import BaseCommand
from accounts.models import AddressConfiguration, AddressFieldConfiguration

class Command(BaseCommand):
    help = 'Set up initial address configurations'

    def handle(self, *args, **options):
        # UK Configuration
        uk_config, created = AddressConfiguration.objects.get_or_create(
            name='UK',
            defaults={'is_default': True}
        )
        
        if created:
            uk_fields = [
                ('line1', 'Address Line 1', True, 1),
                ('line2', 'Address Line 2', False, 2),
                ('line3', 'Address Line 3', False, 3),
                ('city', 'Town/City', True, 4),
                ('region', 'County', False, 5),
                ('postal_code', 'Post Code', True, 6),
                ('country', 'Country', True, 7),
            ]
            
            for name, label, required, order in uk_fields:
                AddressFieldConfiguration.objects.get_or_create(
                    configuration=uk_config,
                    name=name,
                    defaults={
                        'label': label,
                        'required': required,
                        'enabled': True,
                        'order': order
                    }
                )

        # US Configuration
        us_config, created = AddressConfiguration.objects.get_or_create(
            name='US'
        )
        
        if created:
            us_fields = [
                ('line1', 'Street Address', True, 1),
                ('line2', 'Apt/Suite', False, 2),
                ('city', 'City', True, 3),
                ('region', 'State', True, 4),
                ('postal_code', 'ZIP Code', True, 5),
                ('country', 'Country', True, 6),
            ]
            
            for name, label, required, order in us_fields:
                AddressFieldConfiguration.objects.get_or_create(
                    configuration=us_config,
                    name=name,
                    defaults={
                        'label': label,
                        'required': required,
                        'enabled': True,
                        'order': order
                    }
                )

        self.stdout.write(self.style.SUCCESS('Address configurations created successfully'))