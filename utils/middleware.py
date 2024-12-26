from django.conf import settings
from django.shortcuts import redirect
from datetime import datetime, timedelta
from django.urls import reverse
from django.contrib import messages


class SessionTimeoutMiddleware:
    """
    Middleware to log out users after a period of inactivity.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            # Get the last activity timestamp from the session
            last_activity = request.session.get('last_activity')

            if last_activity:
                last_activity = datetime.strptime(last_activity, "%Y-%m-%d %H:%M:%S.%f")
                inactivity_period = datetime.now() - last_activity

                # Check if the inactivity period exceeds the allowed limit
                max_inactivity = timedelta(seconds=getattr(settings, 'INACTIVITY_TIMEOUT', 300))  # Default: 5 minutes
                if inactivity_period > max_inactivity:
                    from django.contrib.auth import logout
                    logout(request)
                    
                    # Get the `short_code` from the request path
                    short_code = request.resolver_match.kwargs.get('short_code', None)
                    
                    if short_code:
                        # Redirect with the short_code
                        return redirect(reverse('login-page', kwargs={'short_code': short_code}))
                    else:
                        # Handle cases where short_code is missing
                        return redirect('home')  # Or another fallback URL

            # Update the last activity timestamp in the session
            request.session['last_activity'] = str(datetime.now())

        response = self.get_response(request)
        return response


from django.contrib.sessions.models import Session

class NotifyOnSessionTerminationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if '_session_terminated' in request.session:
            del request.session['_session_terminated']
            messages.info(request, "One of your sessions has been terminated.")
        return self.get_response(request)
