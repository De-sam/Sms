from django.conf import settings
from datetime import datetime, timedelta
from django.contrib.auth import logout
from django.contrib import messages


class SessionTimeoutMiddleware:
    """
    Middleware to log out users after a period of inactivity without redirecting.
    A session expiry message is displayed on the next request.
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
                    logout(request)
                    # Flag the session as terminated for notification on the next request
                    request.session['_session_terminated'] = True

            # Update the last activity timestamp in the session
            request.session['last_activity'] = str(datetime.now())

        response = self.get_response(request)

        # Check if a session termination occurred
        if request.session.pop('_session_terminated', False):
            messages.warning(request, "Your session has expired due to inactivity. Please log in again.")

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
