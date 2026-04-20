"""
Assignment API views:
  POST /api/assignments/run/            — Trigger pipeline
  GET  /api/assignments/runs/           — List runs
  GET  /api/assignments/runs/<id>/      — Run detail
  GET  /api/assignments/runs/<id>/stream/ — SSE live log stream
  GET  /api/assignments/docs/           — List generated docs
"""
import json
import time
import logging

from django.db import models
from django.http import StreamingHttpResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from .models import AssignmentRun, GeneratedDoc
from .serializers import (
    AssignmentRunListSerializer,
    AssignmentRunDetailSerializer,
    GeneratedDocSerializer,
)
from .tasks import run_assignment_pipeline
from config.celery import app as celery_app

logger = logging.getLogger(__name__)


class TriggerRunView(APIView):
    """POST /api/assignments/run/ — Manually trigger the pipeline."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            profile = request.user.profile
        except Exception:
            return Response({"error": "Student profile not found."}, status=404)

        if not profile.has_piemr_credentials:
            return Response(
                {"error": "PIEMR credentials not configured. Please complete setup first."},
                status=400,
            )

        # ── Step 1: Cleanup stale runs ──
        # Mark runs that have been 'running' or 'pending' for > 30 mins as failed
        from django.utils import timezone
        from datetime import timedelta
        stale_threshold = timezone.now() - timedelta(minutes=30)
        
        stale_runs = AssignmentRun.objects.filter(
            student=profile,
            status__in=["pending", "running"],
            created_at__lt=stale_threshold
        )
        if stale_runs.exists():
            count = stale_runs.count()
            stale_runs.update(
                status="failed",
                log_output=models.F('log_output') + f"\n[{timezone.now().strftime('%H:%M:%S')}] Marked as stale/failed by system.\n",
                finished_at=timezone.now()
            )
            logger.info(f"[api] Cleaned up {count} stale runs for student {profile.id}")

        # ── Step 2: Check if a run is already active ──
        active_run = AssignmentRun.objects.filter(
            student=profile, status__in=["pending", "running"]
        ).first()
        if active_run:
            return Response(
                {"error": "A pipeline run is already in progress.", "run_id": active_run.id},
                status=409,
            )

        # ── Step 3: Create run record immediately ──
        run = AssignmentRun.objects.create(
            student=profile,
            triggered_by="manual",
            status="pending",
            started_at=timezone.now(),
        )

        # ── Step 4: Dispatch Celery task with run_id ──
        task = run_assignment_pipeline.delay(profile.id, triggered_by="manual", run_id=run.id)
        
        # Update run with task ID
        run.celery_task_id = task.id
        run.save(update_fields=["celery_task_id"])
        
        logger.info(f"[api] Manual run triggered: run={run.id}, task={task.id}")

        return Response(
            {
                "detail": "Pipeline started.", 
                "run_id": run.id,
                "task_id": task.id
            },
            status=status.HTTP_201_CREATED,
        )


class RunListView(APIView):
    """GET /api/assignments/runs/ — Paginated run history for the current student."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            profile = request.user.profile
        except Exception:
            return Response({"error": "Profile not found"}, status=404)

        runs = AssignmentRun.objects.filter(student=profile).order_by("-created_at")[:50]
        return Response(AssignmentRunListSerializer(runs, many=True).data)


class RunDetailView(APIView):
    """GET /api/assignments/runs/<id>/ — Full detail + log for one run."""
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            run = AssignmentRun.objects.get(id=pk, student=request.user.profile)
        except AssignmentRun.DoesNotExist:
            return Response({"error": "Run not found."}, status=404)
        except Exception:
            return Response({"error": "Profile not found."}, status=404)

        return Response(AssignmentRunDetailSerializer(run).data)


class RunLogStreamView(APIView):
    """
    GET /api/assignments/runs/<id>/stream/
    Server-Sent Events — streams live log output while the run is active.
    For completed runs, sends the full log as a single event and closes.
    Auth via ?token= query param (EventSource doesn't support custom headers).
    """
    permission_classes = []  # Auth handled manually below

    def get(self, request, pk):
        # Manual JWT auth (EventSource can't send Authorization headers)
        from apps.users.authentication import decode_token
        from django.contrib.auth.models import User

        token = request.query_params.get("token", "")
        try:
            payload = decode_token(token)
            user = User.objects.get(id=payload["user_id"])
        except Exception:
            return Response({"error": "Unauthorized"}, status=401)

        try:
            run = AssignmentRun.objects.get(id=pk, student=user.profile)
        except AssignmentRun.DoesNotExist:
            return Response({"error": "Run not found"}, status=404)

        def event_stream():
            sent_chars = 0
            poll_interval = 1.0  # seconds between DB polls

            while True:
                # Re-fetch from DB to get latest log
                try:
                    run.refresh_from_db(fields=["log_output", "status"])
                except Exception:
                    break

                log = run.log_output or ""
                new_content = log[sent_chars:]

                if new_content:
                    for line in new_content.splitlines():
                        if line:
                            yield f"data: {line}\n\n"
                    sent_chars = len(log)

                if run.status not in ("pending", "running"):
                    # Run is done — send final status event and close
                    yield f"event: done\ndata: {json.dumps({'status': run.status})}\n\n"
                    break

                time.sleep(poll_interval)

        response = StreamingHttpResponse(
            event_stream(),
            content_type="text/event-stream",
        )
        response["Cache-Control"] = "no-cache"
        response["X-Accel-Buffering"] = "no"  # Disable nginx buffering
        return response


class DocListView(APIView):
    """GET /api/assignments/docs/ — All generated docs for the current student."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            profile = request.user.profile
        except Exception:
            return Response({"error": "Profile not found"}, status=404)

        docs = GeneratedDoc.objects.filter(run__student=profile).select_related("run")
        
        # Filter by run_id if provided (used by RunDetail page)
        run_id = request.query_params.get('run_id')
        if run_id:
            docs = docs.filter(run_id=run_id)
            
        return Response(GeneratedDocSerializer(docs, many=True).data)


class StopRunView(APIView):
    """POST /api/assignments/runs/<id>/stop/ — Manually terminal a running task."""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            run = AssignmentRun.objects.get(id=pk, student=request.user.profile)
        except AssignmentRun.DoesNotExist:
            return Response({"error": "Run not found."}, status=404)

        if run.status not in ["pending", "running"]:
            return Response({"error": "Run is not active."}, status=400)

        # 1. Revoke the Celery task
        if run.celery_task_id:
            logger.info(f"[api] Stopping task {run.celery_task_id} for run {run.id}")
            # terminate=True sends SIGTERM to the worker child process
            celery_app.control.revoke(run.celery_task_id, terminate=True, signal='SIGTERM')

        # 2. Update DB status immediately
        run.status = "failed"
        run.finished_at = timezone.now()
        run.append_log("Run manually stopped by user.")
        run.save(update_fields=["status", "finished_at"])

        return Response({"detail": "Stop signal sent to pipeline."})
