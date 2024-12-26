from django.conf import settings
from django.shortcuts import redirect
from datetime import datetime, timedelta
from django.urls import reverse
from django.contrib import messages
from django.contrib.sessions.models import Session


class SessionTimeoutMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Check if the user is authenticated
        if request.user.is_authenticated:
            # Get the last activity time
            last_activity = request.session.get('last_activity')
            
            if last_activity:
                # Check for inactivity timeout
                elapsed_time = (now() - last_activity).total_seconds()
                if elapsed_time > 600:  # Timeout in seconds (e.g., 10 minutes)
                    request.session.flush()  # Clear the session
                    if request.resolver_match:
                        # Ensure `kwargs` is checked to avoid AttributeError
                        kwargs = request.resolver_match.kwargs or {}
                        return redirect('login-page', **kwargs)
                    return redirect('login-page')  # Fallback redirect
                
            # Update last activity time
            request.session['last_activity'] = now()

        response = self.get_response(request)
        return response



class NotifyOnSessionTerminationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if '_session_terminated' in request.session:
            del request.session['_session_terminated']
            messages.info(request, "One of your sessions has been terminated.")
        return self.get_response(request)
