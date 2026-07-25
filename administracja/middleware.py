from django.conf import settings
from django.shortcuts import redirect


class LoginRequiredMiddleware:
    """Wymusza zalogowanie na wszystkich stronach poza logowaniem, adminem i plikami statycznymi."""

    EXEMPT_PREFIXES = ('/login/', '/admin/', '/static/')

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not request.user.is_authenticated and not request.path.startswith(self.EXEMPT_PREFIXES):
            return redirect(f"{settings.LOGIN_URL}?next={request.path}")
        return self.get_response(request)
