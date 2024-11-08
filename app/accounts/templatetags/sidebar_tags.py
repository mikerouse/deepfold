# accounts/templatetags/sidebar_tags.py
from django import template
from accounts.models import Task

register = template.Library()

@register.inclusion_tag('includes/task_list.html')
def render_tasks(user):
    tasks = Task.objects.filter(user=user, completed=False)
    return {
        'tasks': tasks,
        'awesomeness': user.userprofile.awesomeness_score
    }