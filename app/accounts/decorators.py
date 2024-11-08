# accounts/decorators.py
from functools import wraps
from django.shortcuts import redirect
from django.urls import reverse

def profile_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not hasattr(request.user, 'organization'):
            return redirect('complete_profile')
        return view_func(request, *args, **kwargs)
    return _wrapped_view