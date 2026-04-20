from django.contrib import admin
from .models import StudentSchedule


@admin.register(StudentSchedule)
class StudentScheduleAdmin(admin.ModelAdmin):
    list_display = ["student", "is_active", "run_time", "periodic_task_name", "updated_at"]
    list_filter = ["is_active"]
    search_fields = ["student__enrollment_no", "student__user__email"]
    readonly_fields = ["periodic_task_name", "updated_at"]
