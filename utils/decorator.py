from functools import wraps
from django.urls import reverse
from django.shortcuts import redirect


# Custom decorator
def login_required_with_short_code(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            short_code = kwargs.get('short_code', 'default')  # Ensure default value is handled
            login_url = reverse('login-page', kwargs={'short_code': short_code})
            return redirect(f'{login_url}?next={request.path}')
        return view_func(request, *args, **kwargs)
    return _wrapped_view
