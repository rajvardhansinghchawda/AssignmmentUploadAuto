"""
Core Celery task: run_assignment_pipeline
Orchestrates the full assignment automation pipeline for one student.
"""
import os
import shutil
import logging
from datetime import datetime, date

from celery import shared_task
from django.utils import timezone
from django.conf import settings

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=0, name="assignments.run_pipeline")
def run_assignment_pipeline(self, student_id: int, triggered_by: str = "schedule", run_id: int = None):
    """
    Full pipeline for one student:
      1. Create AssignmentRun record
      2. Decrypt credentials
      3. Selenium: login → navigate → scan subjects
      4. For each subject: download → extract → AI answer → build doc → Drive upload → portal upload
      5. Finalise run status
      6. Cleanup temp files
    """
    from apps.users.models import StudentProfile
    from apps.assignments.models import AssignmentRun, GeneratedDoc
    from services.crypto import decrypt
    from services import piemr_selenium as selenium_svc
    from services import extractor, ai_service, gdocs_builder, drive_service

    # ── Step 1: Resolve run record ───────────────────────────────────────────
    try:
        student = StudentProfile.objects.get(id=student_id)
    except StudentProfile.DoesNotExist:
        logger.error(f"[pipeline] StudentProfile {student_id} not found")
        return

    if run_id:
        try:
            run = AssignmentRun.objects.get(id=run_id)
            run.status = "running"
            if not run.started_at:
                run.started_at = timezone.now()
            # Update task ID if not set or different
            if self.request.id:
                run.celery_task_id = self.request.id
            run.save(update_fields=["status", "started_at", "celery_task_id"])
        except AssignmentRun.DoesNotExist:
            logger.error(f"[pipeline] AssignmentRun {run_id} not found, creating new.")
            run = AssignmentRun.objects.create(
                student=student,
                triggered_by=triggered_by,
                status="running",
                started_at=timezone.now(),
                celery_task_id=self.request.id or "",
            )
    else:
        run = AssignmentRun.objects.create(
            student=student,
            triggered_by=triggered_by,
            status="running",
            started_at=timezone.now(),
            celery_task_id=self.request.id or "",
        )

    run.append_log(f"Pipeline started (triggered_by={triggered_by})")
    logger.info(f"[pipeline] Run #{run.id} started for student {student_id}")

    # ── Per-run temp directories ───────────────────────────────────────────────
    run_download_dir = os.path.join(settings.DOWNLOADS_DIR, str(student_id), str(run.id))
    run_generated_dir = os.path.join(settings.GENERATED_DIR, str(student_id), str(run.id))
    os.makedirs(run_download_dir, exist_ok=True)
    os.makedirs(run_generated_dir, exist_ok=True)

    driver = None
    uploaded_count = 0
    failed_subjects = []

    try:
        # ── Step 2: Decrypt credentials ───────────────────────────────────────
        run.append_log("Decrypting PIEMR credentials...")
        enrollment_no = student.enrollment_no
        piemr_password = decrypt(student.piemr_password)

        # Decrypt Google tokens for Drive upload
        access_token = decrypt(student.google_access_token) if student.google_access_token else ""
        refresh_token = decrypt(student.google_refresh_token) if student.google_refresh_token else ""

        student_info = {
            "name": student.full_name or student.user.get_full_name() or student.user.email,
            "enrollment": enrollment_no,
            "full_name": student.full_name,
        }

        # ── Step 3: Selenium login & navigation ───────────────────────────────
        mode_str = "headless" if settings.SELENIUM_HEADLESS else "visible"
        run.append_log(f"Launching Chrome browser ({mode_str} mode)...")
        # Ensure headless is ALWAYS True on server environments
        driver = selenium_svc.build_driver(download_dir=run_download_dir, headless=settings.SELENIUM_HEADLESS)

        selenium_svc.login(driver, enrollment_no, piemr_password, log_callback=run.append_log)

        selenium_svc.open_assignments_page(driver, log_callback=run.append_log)

        # ── Step 4: Scan subjects ─────────────────────────────────────────────
        run.append_log("Scanning subjects for open assignments...")
        subjects = selenium_svc.scan_subjects(driver, log_callback=run.append_log)

        if not subjects:
            run.append_log("No open assignments found. Pipeline complete.")
            run.status = "success"
            run.finished_at = timezone.now()
            run.save(update_fields=["status", "finished_at"])
            return

        run.append_log(f"Found {len(subjects)} subject(s) with open assignments.")

        # ── Step 5: Process each subject ──────────────────────────────────────
        for subject_info in subjects:
            subject_name = subject_info.get("name", "Unknown Subject")
            new_count = max(1, subject_info.get("new_count", 1))
            run.append_log(f"\n── Processing: {subject_name} ({new_count} pending) ──")

            for a_idx in range(new_count):
                if new_count > 1:
                    run.append_log(f"  > Assignment {a_idx+1}/{new_count}")

                doc_record = GeneratedDoc.objects.create(
                    run=run,
                    subject_name=subject_name,
                )

                try:
                    # 5a. Download question paper
                    run.append_log(f"  [Action] Opening subject: {subject_name}")
                    run.append_log(f"  [Action] Locating question paper attachment...")
                    qp_path = selenium_svc.download_question_paper(
                        driver, subject_info, run_download_dir, 
                        assignment_index=a_idx, 
                        log_callback=run.append_log
                    )
                    run.append_log(f"  Downloaded: {os.path.basename(qp_path)}")

                    # 5b. Extract questions
                    run.append_log("  Extracting questions from document...")
                    questions = extractor.extract_questions(qp_path)
                    if not questions:
                        raise ValueError("No questions could be extracted from the question paper.")
                    run.append_log(f"  Extracted {len(questions)} question(s).")

                    # 5c. Generate AI answers
                    run.append_log("  Generating answers via Groq AI (LLaMA 3.3 70B)...")
                    qa_dict = ai_service.generate_answers(subject_name, questions)
                    run.append_log(f"  Generated answers for {len(qa_dict)} question(s).")

                    # 5d. Build answer document via Google Docs API
                    run.append_log("  Creating and formatting Google Doc...")
                    doc_id = gdocs_builder.build_google_doc(
                        subject_name=subject_name,
                        student_info=student_info,
                        qa_pairs=qa_dict,
                        access_token=access_token,
                        refresh_token=refresh_token,
                    )
                    
                    # Store web link in doc_record (fetch from drive if needed, or just build it)
                    doc_record.drive_url = f"https://docs.google.com/document/d/{doc_id}/edit"
                    
                    # 5e. Export as local .docx for PIEMR portal upload
                    run.append_log("  Exporting to local .docx for portal upload...")
                    safe_subject = subject_name.replace(" ", "_").replace("/", "-").replace("\\", "-")
                    filename = f"{safe_subject}_{date.today().isoformat()}.docx"
                    doc_path = os.path.join(run_generated_dir, filename)
                    
                    gdocs_builder.export_to_local_docx(
                        doc_id=doc_id,
                        output_path=doc_path,
                        access_token=access_token,
                        refresh_token=refresh_token,
                    )
                    
                    doc_record.local_path = doc_path
                    doc_record.save(update_fields=["local_path", "drive_url"])
                    run.append_log(f"  Google Doc ready: {doc_record.drive_url}")

                    # 5f. Upload to PIEMR portal
                    run.append_log("  Uploading answer document to PIEMR portal...")
                    selenium_svc.upload_file(driver, subject_info, doc_path, log_callback=run.append_log)
                    doc_record.uploaded_to_portal = True
                    doc_record.save(update_fields=["uploaded_to_portal"])
                    run.append_log(f"  ✓ Upload successful for {subject_name}.")
                    uploaded_count += 1

                except Exception as exc:
                    err_msg = f"  ✗ Error processing {subject_name} (Assignment {a_idx+1}): {exc}"
                    logger.exception(f"[pipeline] Run #{run.id} — {err_msg}")
                    run.append_log(err_msg)
                    if subject_name not in failed_subjects:
                        failed_subjects.append(subject_name)

    except Exception as exc:
        # Fatal error (login failed, etc.)
        err_msg = f"Fatal pipeline error: {exc}"
        logger.exception(f"[pipeline] Run #{run.id} — {err_msg}")
        run.append_log(err_msg)
        run.status = "failed"
        run.finished_at = timezone.now()
        run.total_uploaded = uploaded_count
        run.save(update_fields=["status", "finished_at", "total_uploaded"])
        return

    finally:
        # ── Always quit browser ────────────────────────────────────────────────
        if driver:
            try:
                driver.quit()
                logger.info(f"[pipeline] Run #{run.id} — browser closed")
            except Exception:
                pass

        # ── Cleanup temp files ─────────────────────────────────────────────────
        for temp_dir in [run_download_dir, run_generated_dir]:
            try:
                if os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir)
            except Exception as e:
                logger.warning(f"[pipeline] Could not clean up {temp_dir}: {e}")

    # ── Step 6: Finalise run ───────────────────────────────────────────────────
    total_subjects = len(subjects) if 'subjects' in dir() else 0
    if failed_subjects and uploaded_count == 0:
        run.status = "failed"
    elif failed_subjects:
        run.status = "partial"
    else:
        run.status = "success"

    run.total_uploaded = uploaded_count
    run.finished_at = timezone.now()

    summary = (
        f"\nPipeline complete — "
        f"{uploaded_count}/{total_subjects} assignment(s) uploaded successfully."
    )
    if failed_subjects:
        summary += f"\nFailed subjects: {', '.join(failed_subjects)}"

    run.append_log(summary)
    run.save(update_fields=["status", "total_uploaded", "finished_at"])
    logger.info(f"[pipeline] Run #{run.id} finished — status={run.status}")
