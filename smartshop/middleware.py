from __future__ import annotations

from django.http import HttpResponse


class AzureHealthProbeMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Azure App Service health probes may send unusual Host headers.
        # Short-circuit this probe path before any middleware calls request.get_host().
        if request.path == "/robots933456.txt":
            return HttpResponse("ok", content_type="text/plain")

        return self.get_response(request)
