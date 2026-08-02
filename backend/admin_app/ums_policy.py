from django.http import JsonResponse

from admin_app.settings_registry import all_settings, features_enabled_for_path


EXEMPT_PATHS = (
    "/super_admin",
    "/admin/database-backup",
    "/admin/settings",
    "/admin/audit-log",
    "/auth",
    "/applicant/auth/login",
    "/settings/public",
)


class UmsPolicyMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path.rstrip("/") or "/"
        if any(path.startswith(prefix) for prefix in EXEMPT_PATHS):
            return self.get_response(request)

        settings = all_settings()["security"]
        if settings["maintenance_mode"]:
            return JsonResponse(
                {"detail": "The UMS is currently in maintenance mode."},
                status=503,
            )
        if settings["read_only_mode"] and request.method not in {"GET", "HEAD", "OPTIONS"}:
            return JsonResponse(
                {"detail": "The UMS is currently in read-only mode."},
                status=503,
            )

        if not features_enabled_for_path(path):
            return JsonResponse(
                {"detail": "This UMS feature is currently unavailable."},
                status=404,
            )
        return self.get_response(request)
