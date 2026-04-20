# PIEMR Assignment AI Agent — Backend

Django 4 + DRF + Celery + Redis + PostgreSQL + Selenium + Groq + Google Drive

---

## Project Structure

```
backend/
├── config/
│   ├── __init__.py         ← Imports Celery app
│   ├── settings.py         ← All Django configuration
│   ├── urls.py             ← Root URL router
│   ├── wsgi.py
│   └── celery.py           ← Celery app init
│
├── apps/
│   ├── users/              ← Auth, Google OAuth, student profiles, config
│   │   ├── models.py           StudentProfile
│   │   ├── views.py            Google OAuth, JWT, /api/config/
│   │   ├── serializers.py
│   │   ├── authentication.py   JWTAuthentication (DRF backend)
│   │   ├── urls.py             /api/auth/
│   │   ├── config_urls.py      /api/config/
│   │   └── admin.py
│   │
│   ├── assignments/        ← Pipeline orchestration, run logging
│   │   ├── models.py           AssignmentRun, GeneratedDoc
│   │   ├── views.py            REST + SSE stream
│   │   ├── serializers.py
│   │   ├── tasks.py            ← THE CORE PIPELINE (Celery task)
│   │   ├── urls.py
│   │   └── admin.py
│   │
│   └── scheduler/          ← Per-student Celery Beat schedule
│       ├── models.py           StudentSchedule
│       ├── views.py
│       ├── urls.py
│       └── admin.py
│
├── services/               ← Business logic (no Django dependencies)
│   ├── crypto.py           ← Fernet encrypt/decrypt
│   ├── extractor.py        ← PDF + DOCX question extraction
│   ├── ai_service.py       ← Groq API (LLaMA 3.3 70B)
│   ├── doc_builder.py      ← python-docx answer doc generator
│   ├── drive_service.py    ← Google Drive API v3 upload
│   └── piemr_selenium.py   ← Selenium browser automation
│
├── downloads/              ← Temp: downloaded question papers (gitignored)
├── generated/              ← Temp: generated answer docs (gitignored)
├── manage.py
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── .env.example
```

---

## API Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/api/auth/google/` | Public | Returns Google OAuth redirect URL |
| GET | `/api/auth/google/callback/` | Public | OAuth callback → issues JWT |
| POST | `/api/auth/logout/` | JWT | Logout |
| GET | `/api/auth/me/` | JWT | Current user profile |
| GET | `/api/config/` | JWT | Get PIEMR config (no password) |
| POST | `/api/config/` | JWT | Save PIEMR enrollment + password |
| POST | `/api/assignments/run/` | JWT | Manually trigger pipeline |
| GET | `/api/assignments/runs/` | JWT | List run history |
| GET | `/api/assignments/runs/<id>/` | JWT | Run detail + full log |
| GET | `/api/assignments/runs/<id>/stream/?token=<jwt>` | Token param | SSE live log |
| GET | `/api/assignments/docs/` | JWT | List generated documents |
| GET | `/api/scheduler/` | JWT | Get current schedule |
| POST | `/api/scheduler/` | JWT | Create/update schedule |
| DELETE | `/api/scheduler/` | JWT | Disable schedule |

---

## Local Development Setup

### Prerequisites
- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- Google Chrome (for Selenium)
- A Google Cloud project with OAuth 2.0 credentials
- A Groq API key (free at console.groq.com)

### 1. Clone and install

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env with your actual values
```

Generate a Fernet key:
```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Generate a Django secret key:
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### 3. Database setup

```bash
python manage.py migrate
python manage.py createsuperuser
```

### 4. Run all services (separate terminals)

**Django dev server:**
```bash
python manage.py runserver
```

**Celery worker:**
```bash
celery -A config worker --loglevel=info
```

**Celery Beat scheduler:**
```bash
celery -A config beat --loglevel=info --scheduler django_celery_beat.schedulers:DatabaseScheduler
```

---

## Docker (Recommended)

```bash
# Copy and fill in your .env
cp backend/.env.example backend/.env

# Build and start everything
docker-compose up --build

# Run migrations inside the container
docker-compose exec backend python manage.py migrate
docker-compose exec backend python manage.py createsuperuser
```

Services started:
- `db` — PostgreSQL on port 5432
- `redis` — Redis on port 6379
- `backend` — Django/Gunicorn on port 8000
- `celery_worker` — Celery worker (2 concurrent)
- `celery_beat` — Celery Beat scheduler

---

## Google Cloud Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a project → Enable **Google Drive API**
3. OAuth consent screen → External → Add scopes:
   - `openid`, `email`, `profile`
   - `https://www.googleapis.com/auth/drive.file`
4. Credentials → Create OAuth 2.0 Client ID (Web application)
5. Add Authorized redirect URI: `http://localhost:8000/api/auth/google/callback/`
6. Copy Client ID and Secret to `.env`

---

## Pipeline Flow

```
POST /api/assignments/run/
        │
        ▼
  Celery task dispatched
        │
        ▼
  [1] AssignmentRun created (status=running)
        │
        ▼
  [2] Decrypt PIEMR credentials (Fernet)
        │
        ▼
  [3] Selenium: Chrome headless login → PIEMR portal
        │
        ▼
  [4] Selenium: Navigate to Assignments page
        │
        ▼
  [5] Selenium: Scan subjects for open assignments
        │
        ▼
  For each open subject:
    ├─ [5a] Download question paper (PDF/DOCX)
    ├─ [5b] Extract questions (PyMuPDF / python-docx)
    ├─ [5c] AI generate answers (Groq LLaMA 3.3 70B)
    ├─ [5d] Build formatted Word doc (python-docx)
    ├─ [5e] Upload to Google Drive → store URL
    ├─ [5f] Upload doc to PIEMR portal via Selenium
    └─ [5g] Update GeneratedDoc record
        │
        ▼
  [6] AssignmentRun finalised (success/partial/failed)
        │
        ▼
  [7] Temp files cleaned up
```

Live log is streamed to frontend via SSE at `/api/assignments/runs/<id>/stream/`.

---

## Security Notes

- **Never** commit `.env` — it's in `.gitignore`
- PIEMR passwords are Fernet-encrypted before DB storage
- Google tokens are Fernet-encrypted before DB storage
- JWT tokens expire after 72 hours (configurable)
- The SSE endpoint accepts `?token=` query param because `EventSource` doesn't support custom headers
- Temp files in `downloads/` and `generated/` are deleted after each run
