# PIEMR Assignment AI Agent — Project Description

## Vision

The **PIEMR Assignment AI Agent** is a fully autonomous, AI-powered academic assistant built for students of PIEMR (Prestige Institute of Engineering Management and Research). It eliminates 100% of the manual effort involved in completing and submitting assignments — from reading the question paper to generating answers to uploading the final document — all without the student lifting a finger.

The project evolves from a simple file uploader into a complete AI-driven academic pipeline.

---

## The Problem It Solves

Previously, students had to:
1. Manually check the portal for new assignments.
2. Download the question paper themselves.
3. Write or find answers.
4. Format a Word document.
5. Log back into the portal and upload it.

The new system automates every single one of these steps. The student only needs to be registered once. After that, the system runs on a daily schedule and handles everything end-to-end.

---

## What the System Does — The Full Pipeline

### Stage 1 — Login & Discovery
- Selenium logs into the PIEMR portal using the student's encrypted credentials.
- Navigates directly to the Assignments page.
- Scans all subjects for open/new assignments with pending uploads.

### Stage 2 — Question Paper Download
- For each open assignment, Selenium finds and downloads the attached question paper (PDF or Word doc) from the portal.
- The file is saved temporarily to the server's `downloads/` directory.

### Stage 3 — Question Extraction
- The downloaded file is parsed using Python:
  - `PyMuPDF (fitz)` for PDF files.
  - `python-docx` for `.docx` files.
- All questions are extracted as clean text.

### Stage 4 — AI Answer Generation (Groq)
- The extracted questions are sent to the **Groq API** with a structured academic prompt.
- Model used: `llama-3.3-70b-versatile` or `mixtral-8x7b-32768`.
- The AI generates well-structured, subject-appropriate answers for each question.

### Stage 5 — Answer Document Creation
- `python-docx` formats the AI-generated answers into a clean, properly formatted Word document.
- Document includes: Assignment title, subject name, student enrollment, date, and all Q&A pairs with headings.
- The file is saved to `generated/` on the server and simultaneously pushed to the student's **Google Drive**.

### Stage 6 — Upload
- Selenium picks up the generated `.docx` file.
- Uploads it to the correct assignment row on the portal.
- Confirms the upload alert and logs the result.

### Stage 7 — Logging & Notification
- The full run (success/failure per assignment) is recorded in the PostgreSQL database.
- Run history is visible on the student's dashboard.
- Optional: Email/WhatsApp notification on completion.

---

## Target Users

- B.Tech students at PIEMR (any semester).
- Multi-user: Each student has their own account, credentials, and Google Drive connection.

---

## Core Constraints

- Answers are AI-generated for academic assistance purposes. Students are responsible for reviewing them.
- Portal structure is specific to `accsoft.piemr.edu.in` — the Selenium logic is tightly coupled to it.
- Google Drive storage is per-student, using their own OAuth-authorized Drive folder.
- The system runs as a scheduled background job; no manual trigger needed after initial setup.

---

## Deployment Target

- **Docker** containerized application.
- Deployable on **Render**, **Hugging Face Spaces**, or any VPS.
- Chrome runs headless inside the container.

---

## Technology Summary

| Layer | Technology |
|---|---|
| Backend Framework | Django 4.x + Django REST Framework |
| Task Scheduling | Celery + Redis |
| Browser Automation | Selenium 4 + ChromeDriver |
| AI Answer Generation | Groq API (LLaMA 3 / Mixtral) |
| PDF Parsing | PyMuPDF (fitz) |
| Word Doc Generation | python-docx |
| Authentication | Google OAuth 2.0 |
| Cloud Storage | Google Drive API v3 |
| Database | PostgreSQL |
| Password Security | Fernet symmetric encryption |
| Frontend | React 18 + Vite + Tailwind CSS |
| Containerization | Docker (multi-stage build) |
