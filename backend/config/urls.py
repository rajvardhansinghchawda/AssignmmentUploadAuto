from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/", include("apps.users.urls")),
    path("api/assignments/", include("apps.assignments.urls")),
    path("api/scheduler/", include("apps.scheduler.urls")),
    path("api/config/", include("apps.users.config_urls")),
]
