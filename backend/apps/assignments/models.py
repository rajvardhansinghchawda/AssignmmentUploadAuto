from django.db import models
from apps.users.models import StudentProfile


class AssignmentRun(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("running", "Running"),
        ("success", "Success"),
        ("partial", "Partial"),
        ("failed", "Failed"),
    ]

    student = models.ForeignKey(
        StudentProfile, on_delete=models.CASCADE, related_name="runs"
    )
    triggered_by = models.CharField(
        max_length=20, default="schedule"
    )  # 'manual' or 'schedule'
    status = models.CharField(
        max_length=10, choices=STATUS_CHOICES, default="pending"
    )
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    log_output = models.TextField(blank=True)
    total_uploaded = models.IntegerField(default=0)
    celery_task_id = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Assignment Run"
        verbose_name_plural = "Assignment Runs"

    def __str__(self):
        return f"Run #{self.id} — {self.student} — {self.status}"

    def append_log(self, line: str):
        """Append a timestamped line to log_output and save."""
        from django.utils import timezone
        ts = timezone.now().strftime("%H:%M:%S")
        self.log_output += f"[{ts}] {line}\n"
        self.save(update_fields=["log_output"])

    @property
    def duration_seconds(self) -> int | None:
        if self.started_at and self.finished_at:
            return int((self.finished_at - self.started_at).total_seconds())
        return None


class GeneratedDoc(models.Model):
    run = models.ForeignKey(
        AssignmentRun, on_delete=models.CASCADE, related_name="docs"
    )
    subject_name = models.CharField(max_length=100)
    assignment_no = models.CharField(max_length=20, blank=True)
    local_path = models.CharField(max_length=500, blank=True)
    drive_url = models.URLField(blank=True)
    uploaded_to_portal = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Generated Document"
        verbose_name_plural = "Generated Documents"

    def __str__(self):
        status = "✓" if self.uploaded_to_portal else "⏳"
        return f"{status} {self.subject_name} — Run #{self.run_id}"
