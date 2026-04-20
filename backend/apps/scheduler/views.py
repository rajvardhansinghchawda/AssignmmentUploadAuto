"""
Scheduler views: GET/POST/DELETE /api/scheduler/
Manages per-student Celery Beat periodic tasks.
"""
import json
import logging

from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import StudentSchedule

logger = logging.getLogger(__name__)


def _sync_celery_beat(schedule: StudentSchedule):
    """
    Create or update the django-celery-beat PeriodicTask for this student.
    Task fires daily at schedule.run_time (IST).
    """
    try:
        from django_celery_beat.models import PeriodicTask, CrontabSchedule

        run_time = schedule.run_time
        crontab, _ = CrontabSchedule.objects.get_or_create(
            minute=str(run_time.minute),
            hour=str(run_time.hour),
            day_of_week="*",
            day_of_month="*",
            month_of_year="*",
            timezone="Asia/Kolkata",
        )

        task_name = f"piemr-daily-run-student-{schedule.student_id}"
        schedule.periodic_task_name = task_name
        schedule.save(update_fields=["periodic_task_name"])

        task, created = PeriodicTask.objects.update_or_create(
            name=task_name,
            defaults={
                "task": "assignments.run_pipeline",
                "crontab": crontab,
                "args": json.dumps([schedule.student_id, "schedule"]),
                "enabled": schedule.is_active,
                "description": f"Daily assignment run for student {schedule.student.enrollment_no}",
            },
        )
        action = "Created" if created else "Updated"
        logger.info(f"[scheduler] {action} Celery Beat task '{task_name}' (enabled={schedule.is_active})")
    except Exception as exc:
        logger.exception(f"[scheduler] Failed to sync Celery Beat: {exc}")


def _disable_celery_beat(schedule: StudentSchedule):
    """Disable the PeriodicTask in Celery Beat without deleting it."""
    try:
        from django_celery_beat.models import PeriodicTask
        if schedule.periodic_task_name:
            PeriodicTask.objects.filter(name=schedule.periodic_task_name).update(enabled=False)
            logger.info(f"[scheduler] Disabled task '{schedule.periodic_task_name}'")
    except Exception as exc:
        logger.warning(f"[scheduler] Could not disable Celery Beat task: {exc}")


class SchedulerView(APIView):
    """
    GET    /api/scheduler/ — Return current schedule
    POST   /api/scheduler/ — Create or update schedule
    DELETE /api/scheduler/ — Disable schedule
    """
    permission_classes = [IsAuthenticated]

    def _get_profile(self, request):
        try:
            return request.user.profile
        except Exception:
            return None

    def get(self, request):
        profile = self._get_profile(request)
        if not profile:
            return Response({"error": "Profile not found"}, status=404)

        try:
            schedule = profile.schedule
            return Response({
                "is_active": schedule.is_active,
                "run_time": schedule.run_time.strftime("%H:%M"),
                "updated_at": schedule.updated_at,
            })
        except StudentSchedule.DoesNotExist:
            return Response({"is_active": False, "run_time": "08:00"})

    def post(self, request):
        profile = self._get_profile(request)
        if not profile:
            return Response({"error": "Profile not found"}, status=404)

        is_active = request.data.get("is_active", True)
        run_time_str = request.data.get("run_time", "08:00")

        # Validate time format
        try:
            from datetime import datetime
            run_time = datetime.strptime(run_time_str, "%H:%M").time()
        except (ValueError, TypeError):
            return Response({"error": "Invalid time format. Use HH:MM."}, status=400)

        schedule, _ = StudentSchedule.objects.get_or_create(student=profile)
        schedule.is_active = is_active
        schedule.run_time = run_time
        schedule.save()

        # Sync with Celery Beat
        _sync_celery_beat(schedule)

        logger.info(
            f"[scheduler] Schedule updated for student {profile.id}: "
            f"active={is_active}, time={run_time_str}"
        )

        return Response({
            "is_active": schedule.is_active,
            "run_time": schedule.run_time.strftime("%H:%M"),
            "detail": "Schedule updated successfully.",
        })

    def delete(self, request):
        profile = self._get_profile(request)
        if not profile:
            return Response({"error": "Profile not found"}, status=404)

        try:
            schedule = profile.schedule
            schedule.is_active = False
            schedule.save(update_fields=["is_active"])
            _disable_celery_beat(schedule)
            return Response({"detail": "Schedule disabled."})
        except StudentSchedule.DoesNotExist:
            return Response({"detail": "No schedule found."})
