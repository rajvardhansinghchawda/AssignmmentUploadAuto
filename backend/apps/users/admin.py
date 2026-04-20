from django.contrib import admin
from .models import StudentProfile


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ["user", "enrollment_no", "is_setup_complete", "created_at"]
    list_filter = ["is_setup_complete"]
    search_fields = ["user__email", "enrollment_no"]
    readonly_fields = ["created_at", "updated_at", "google_access_token", "google_refresh_token"]
