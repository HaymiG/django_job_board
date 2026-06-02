from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect

from .models import UserRole


def role_required(*roles):
    """Require login and one of the given user roles."""

    def decorator(view_func):
        @login_required
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            if request.user.role not in roles:
                messages.error(
                    request,
                    "You do not have permission to access that page.",
                )
                return redirect("accounts:profile")
            return view_func(request, *args, **kwargs)

        return _wrapped

    return decorator


employer_required = role_required(UserRole.EMPLOYER)
job_seeker_required = role_required(UserRole.JOB_SEEKER)
