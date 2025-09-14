from django.http import HttpResponseNotFound
from django.urls import resolve

class AdminAccessRestrictionMiddleware:
    """
    Middleware to restrict access to /admin/ for non-admin users.
    - If user is authenticated and not admin, return 404.
    - If user is not authenticated, block access to admin login page by returning 404.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Check if the request path is under /admin/
        if request.path.startswith('/admin/'):
            user = request.user
            # If user is authenticated and is staff or superuser, allow access
            if user.is_authenticated:
                if not (user.is_staff or user.is_superuser):
                    return HttpResponseNotFound('<h1>Page not found</h1>')
            else:
                # User not authenticated, block access to admin login page
                # Allow access only if the resolved url is not admin login page
                # But safer to block all /admin/ for anonymous users except static files
                # So return 404 for all anonymous users accessing /admin/
                return HttpResponseNotFound('<h1>Page not found</h1>')

        response = self.get_response(request)
        return response
