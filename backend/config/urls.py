from django.contrib import admin
from django.urls import path, include, re_path
from django.views.generic import TemplateView
from django.conf import settings
from django.conf.urls.static import static
import os

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/", include("apps.users.urls")),
    path("api/assignments/", include("apps.assignments.urls")),
    path("api/scheduler/", include("apps.scheduler.urls")),
    path("api/config/", include("apps.users.config_urls")),

    # Serve React frontend for all non-API routes
    re_path(r"^(?!api/|admin/|static/|assets/|manifest\.json|robots\.txt|favicon\.ico).*$", TemplateView.as_view(
        template_name="index.html"
    )),
]

# Serve static files in development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
