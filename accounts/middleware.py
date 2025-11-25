from urllib.parse import urlencode

from django.conf import settings
from django.shortcuts import redirect
from django.urls import reverse


class EnsurePoliciesAcceptedMiddleware:
    """
    Redirige a la pantalla de Términos y Política a los usuarios autenticados
    que aún no han registrado su aceptación.
    """

    EXEMPT_PREFIXES = (
        "/admin",
        "/static",
        "/media",
        "/health-check",
        "/i18n",
        "/jsi18n",
    )
    EXEMPT_SUBSTRINGS = (
        "/accounts/login",
        "/accounts/logout",
        "/accounts/password",
        "/accounts/register",
        "/accounts/reset",
        "/accounts/accept-terms",
    )

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if self._should_redirect(request):
            accept_url = reverse("accept_policies")
            next_url = request.get_full_path()
            query = urlencode({"next": next_url})
            return redirect(f"{accept_url}?{query}")
        return self.get_response(request)

    def _should_redirect(self, request):
        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            return False
        if user.has_accepted_terms and user.has_accepted_privacy:
            return False

        path = request.path
        if any(path.startswith(prefix) for prefix in self.EXEMPT_PREFIXES):
            return False
        if any(substr in path for substr in self.EXEMPT_SUBSTRINGS):
            return False

        # Evitar redirecciones para vistas públicas (ej. validación)
        public_prefixes = getattr(
            settings,
            "POLICY_PUBLIC_PREFIXES",
            ("/quiz/external-courses/validation/",),
        )
        if any(path.startswith(prefix) for prefix in public_prefixes):
            return False

        return True

