# adsoft/middleware.py
from django.contrib.sessions.exceptions import SessionInterrupted
from django.shortcuts import redirect
import logging

logger = logging.getLogger(__name__)

class SessionErrorMiddleware:
    """
    Middleware to handle SessionInterrupted exceptions gracefully.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            response = self.get_response(request)
            return response
        except SessionInterrupted as e:
            logger.warning(f"Session interrupted: {e}")
            
            # Handle AJAX requests
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                from django.http import JsonResponse
                return JsonResponse({'error': 'Session expired', 'redirect': '/login/'}, status=401)
            else:
                # Redirect to login for regular requests
                return redirect('login')

class IgnoreSessionInterruptedMiddleware:
    """
    Alternative middleware that silently handles session errors.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            return self.get_response(request)
        except SessionInterrupted as e:
            logger.warning(f"Ignoring session interrupted error: {e}")
            # Return a generic response instead of crashing
            from django.http import HttpResponse
            return HttpResponse("Session expired - please refresh the page", status=401)