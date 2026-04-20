from django.db import models
from apps.users.models import StudentProfile


class StudentSchedule(models.Model):
    student = models.OneToOneField(
        StudentProfile, on_delete=models.CASCADE, related_name="schedule"
    )
    is_active = models.BooleanField(default=True)
    run_time = models.TimeField(default="08:00")  # Local IST time
    # django-celery-beat PeriodicTask name for this student
    periodic_task_name = models.CharField(max_length=200, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Student Schedule"
        verbose_name_plural = "Student Schedules"

    def __str__(self):
        status = "Active" if self.is_active else "Paused"
        return f"{self.student} — {status} @ {self.run_time}"
