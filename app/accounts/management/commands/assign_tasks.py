# app/accounts/management/commands/assign_tasks.py

from django.core.management.base import BaseCommand
from accounts.models import User, Task

class Command(BaseCommand):
    help = 'Assign "Complete Your Profile" task to users without one.'

    def handle(self, *args, **kwargs):
        users = User.objects.exclude(tasks__task_type='PROFILE')
        for user in users:
            Task.objects.create(
                user=user,
                task_type='PROFILE',
                title='Complete Your Profile',
                description='Add your organisation details to unlock more features',
                points=10
            )
        self.stdout.write(self.style.SUCCESS('Tasks assigned successfully'))