# PIEMR Assignment AI Agent — Frontend Description

**Stack:** React 18 + Vite + Tailwind CSS + Axios  
**Auth:** Google OAuth (handled by backend redirect flow)  
**API Base:** `http://localhost:8000/api/` (dev) / `/api/` (prod)

---

## 1. Application Structure

```
frontend/
├── package.json
├── vite.config.js
├── tailwind.config.js
├── index.html
└── src/
    ├── main.jsx
    ├── App.jsx
    ├── api.js                  (Axios instance + interceptors)
    ├── hooks/
    │   ├── useAuth.js          (Google auth state)
    │   └── useSSE.js           (Server-Sent Events hook for live logs)
    ├── pages/
    │   ├── Login.jsx           (Route: /)
    │   ├── Setup.jsx           (Route: /setup)
    │   ├── Dashboard.jsx       (Route: /dashboard)
    │   └── RunDetail.jsx       (Route: /runs/:id)
    └── components/
        ├── Navbar.jsx
        ├── LiveLog.jsx
        ├── RunCard.jsx
        ├── DocCard.jsx
        └── ScheduleToggle.jsx
```

---

## 2. Routing Table

| Route | Page | Access |
|---|---|---|
| `/` | Login.jsx | Public only (redirect to /dashboard if logged in) |
| `/setup` | Setup.jsx | Auth required |
| `/dashboard` | Dashboard.jsx | Auth required |
| `/runs/:id` | RunDetail.jsx | Auth required |

Use `react-router-dom v6` for routing. Wrap protected routes in an `<AuthGuard>` component that checks localStorage for JWT and redirects to `/` if not found.

---

## 3. Page Specifications

---

### Page 1 — `Login.jsx` (Route: `/`)

**Purpose:** Entry point. Student authenticates with Google.

**Layout:** Centered card on a dark/gradient background.

**Elements:**
- App logo / name: "PIEMR Assignment AI Agent"
- Tagline: "Your assignments. Done automatically."
- Single CTA button: **"Continue with Google"** — clicking this calls `GET /api/auth/google/` which redirects to Google OAuth consent screen.
- After OAuth callback, the backend returns a JWT. Store it in `localStorage` as `piemr_token` and redirect to `/setup` if first login, or `/dashboard` if returning user.

**States:**
- Default: Show the Google button.
- Loading: Show spinner after button click (while redirect happens).

---

### Page 2 — `Setup.jsx` (Route: `/setup`)

**Purpose:** One-time setup. Student enters PIEMR portal credentials.

**Layout:** Centered form card with two sections.

**Section A — PIEMR Credentials**

Fields:
- **Enrollment Number** (text input) — pre-filled if already saved (GET `/api/config/`).
- **Portal Password** (password input with show/hide toggle) — never pre-filled.

Submit button: **"Save Credentials"** → `POST /api/config/` with `{ enrollment_no, piemr_password }`.

On success: Show green toast "Credentials saved securely".

**Section B — Schedule**

- Toggle switch: **"Enable Daily Auto-Run"** (default: ON).
- Time picker: **"Run at"** with default value `08:00 AM`.
- On toggle/time change: `POST /api/scheduler/` with `{ is_active, run_time }`.

**Footer CTA:** "Go to Dashboard →" button — navigates to `/dashboard`.

**Note:** This page is also reachable from the dashboard via a Settings icon for updating credentials.

---

### Page 3 — `Dashboard.jsx` (Route: `/dashboard`)

**Purpose:** Main control center. Shows run history, generated docs, and manual trigger.

**Layout:** Full-width with a top navbar and two-column grid below.

**Navbar (`Navbar.jsx`):**
- Left: App name.
- Center: Navigation links — Dashboard, History.
- Right: Student name + Google avatar + Settings icon (links to `/setup`) + Logout button.

**Top Action Bar:**
- Status badge: "Schedule Active — Runs at 08:00 AM" OR "Schedule Paused".
- Primary button: **"Run Now"** → `POST /api/assignments/run/` → on success, navigate to `/runs/<new_run_id>`.

**Left Column — Recent Runs**

List of `<RunCard />` components, most recent first.

`RunCard` displays:
- Status badge (colored): Pending / Running / Success / Partial / Failed.
- Triggered by: "Manual" or "Scheduled".
- Start time and duration.
- Number uploaded (e.g., "3 assignments uploaded").
- Clicking a card navigates to `/runs/:id`.

Fetch from: `GET /api/assignments/runs/`

**Right Column — Generated Documents**

List of `<DocCard />` components.

`DocCard` displays:
- Subject name.
- Assignment number.
- Date generated.
- "Open in Drive" button — links to `drive_url`.
- Status: "Uploaded to Portal ✓" or "Upload Pending".

Fetch from: `GET /api/assignments/docs/`

---

### Page 4 — `RunDetail.jsx` (Route: `/runs/:id`)

**Purpose:** Full detail view of one pipeline run with live log streaming.

**Layout:** Single column, full width.

**Top Section:**
- Run ID, status badge, triggered by, start time, end time.
- If status is 'running': Show animated "Running..." indicator.

**Live Log Terminal (`LiveLog.jsx`):**
- Dark background terminal-style box.
- Streams live output while run is active via `GET /api/assignments/runs/:id/stream/` (SSE).
- If run is already complete, displays the full stored `log_output` statically.
- Auto-scrolls to the bottom as new lines arrive.
- Monospace font, green text on dark background.

**Documents Generated in this Run:**
- List of `<DocCard />` components filtered to this run's `run_id`.

**Back button:** "← Back to Dashboard"

---

## 4. Component Specifications

---

### `LiveLog.jsx`

```
Props:
  runId: string
  isActive: boolean  (true if run status is 'running')

Behavior:
  - If isActive is true: open EventSource to /api/assignments/runs/:id/stream/
  - On each SSE message: append new line to local state array
  - useEffect cleanup: close EventSource on unmount
  - If isActive is false: fetch full log from /api/assignments/runs/:id/ and display statically
  - Auto-scroll: useRef on the log container, scroll to bottom on each update

Rendering:
  <div class="bg-gray-900 text-green-400 font-mono text-sm p-4 rounded overflow-y-auto h-96">
    {lines.map(line => <div>{line}</div>)}
    <div ref={bottomRef} />
  </div>
```

---

### `RunCard.jsx`

```
Props:
  run: { id, status, triggered_by, started_at, finished_at, total_uploaded }

Status badge colors:
  pending  → gray
  running  → blue (with pulse animation)
  success  → green
  partial  → yellow
  failed   → red

Behavior:
  - Entire card is clickable → navigate('/runs/' + run.id)
```

---

### `DocCard.jsx`

```
Props:
  doc: { id, subject_name, assignment_no, drive_url, uploaded_to_portal, created_at }

Rendering:
  - Subject name as title
  - Assignment number as subtitle
  - Date formatted as DD MMM YYYY
  - "Open in Drive" button (external link, opens in new tab)
  - Upload status chip: green "Uploaded ✓" or amber "Pending"
```

---

### `ScheduleToggle.jsx`

```
Props:
  isActive: boolean
  runTime: string  (HH:MM)
  onUpdate: (isActive, runTime) => void

Rendering:
  - Toggle switch for enable/disable
  - Time input (type="time")
  - Auto-saves on change (debounced 800ms) by calling onUpdate
```

---

## 5. `api.js` — Axios Setup

```javascript
import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE || '/api/',
  headers: { 'Content-Type': 'application/json' },
});

// Attach JWT to every request
api.interceptors.request.use(config => {
  const token = localStorage.getItem('piemr_token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// Handle 401 — clear token and redirect to login
api.interceptors.response.use(
  res => res,
  err => {
    if (err.response?.status === 401) {
      localStorage.removeItem('piemr_token');
      window.location.href = '/';
    }
    return Promise.reject(err);
  }
);

export default api;
```

---

## 6. `useSSE.js` Hook

```javascript
import { useEffect, useRef, useState } from 'react';

export function useSSE(url, isActive) {
  const [lines, setLines] = useState([]);
  const esRef = useRef(null);

  useEffect(() => {
    if (!isActive || !url) return;

    const token = localStorage.getItem('piemr_token');
    esRef.current = new EventSource(`${url}?token=${token}`);

    esRef.current.onmessage = (e) => {
      setLines(prev => [...prev, e.data]);
    };

    esRef.current.onerror = () => {
      esRef.current.close();
    };

    return () => esRef.current?.close();
  }, [url, isActive]);

  return lines;
}
```

---

## 7. Key UX Rules

- The app must feel fast and minimal. No heavy animations or complex layouts.
- Mobile-responsive: All pages must work cleanly on a phone screen (students check portal on mobile).
- No manual file uploads anywhere in the UI — the entire value proposition is zero student effort.
- Show meaningful errors: If a run fails, the RunCard should say why (from log output), not just "Failed".
- Toast notifications (top-right) for: credential saved, run triggered, schedule updated.
- Use `react-hot-toast` or a simple custom toast for notifications.

---

## 8. Environment Variables (Frontend)

```env
VITE_API_BASE=http://localhost:8000/api/
```

In production this becomes `/api/` since Django serves the React build and the API is on the same origin.
