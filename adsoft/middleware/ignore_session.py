from django.shortcuts import redirect
from django.contrib.sessions.exceptions import SessionInterrupted

class IgnoreSessionInterruptedMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            return self.get_response(request)
        except SessionInterrupted:
            # Gracefully ignore or redirect
            return redirect('login')  # or HttpResponse(status=204)
