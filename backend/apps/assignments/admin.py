from django.contrib import admin
from .models import AssignmentRun, GeneratedDoc


class GeneratedDocInline(admin.TabularInline):
    model = GeneratedDoc
    extra = 0
    readonly_fields = ["subject_name", "drive_url", "uploaded_to_portal", "created_at"]


@admin.register(AssignmentRun)
class AssignmentRunAdmin(admin.ModelAdmin):
    list_display = ["id", "student", "status", "triggered_by", "total_uploaded", "started_at", "finished_at"]
    list_filter = ["status", "triggered_by"]
    search_fields = ["student__enrollment_no", "student__user__email"]
    readonly_fields = ["started_at", "finished_at", "celery_task_id", "created_at", "log_output"]
    inlines = [GeneratedDocInline]


@admin.register(GeneratedDoc)
class GeneratedDocAdmin(admin.ModelAdmin):
    list_display = ["id", "subject_name", "run", "uploaded_to_portal", "created_at"]
    list_filter = ["uploaded_to_portal"]
    search_fields = ["subject_name", "run__student__enrollment_no"]
