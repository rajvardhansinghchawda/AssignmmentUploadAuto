# ── Stage 1: Build React frontend ─────────────────────────────────────────────
FROM node:20-slim AS frontend-builder

WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ ./
RUN npm run build


# ── Stage 2: Python backend + Chrome + supervisord ────────────────────────────
FROM python:3.11-slim AS final

# Install supervisord + Chrome system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    supervisor \
    wget \
    gnupg \
    curl \
    unzip \
    fonts-liberation \
    libasound2t64 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libcups2 \
    libdbus-1-3 \
    libgdk-pixbuf-xlib-2.0-0 \
    libnspr4 \
    libnss3 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    xdg-utils \
    libgbm1 \
    libvulkan1 \
    libu2f-udev \
    ca-certificates \
    && wget -q -O /tmp/chrome.deb https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb \
    && apt-get install -y /tmp/chrome.deb \
    && rm /tmp/chrome.deb \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user (HuggingFace Spaces requirement)
RUN useradd -m -u 1000 appuser

WORKDIR /app

# Install Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy Django backend source
COPY backend/ .

# Copy built React app into a temporary directory for Django collectstatic
COPY --from=frontend-builder /app/frontend/dist ./frontend_dist/

# Copy supervisord config
COPY backend/supervisord.conf /etc/supervisor/conf.d/app.conf

# Create required runtime directories and fix permissions
RUN mkdir -p downloads generated \
    && chown -R appuser:appuser /app \
    && chmod -R 755 /app

# Switch to non-root user
USER appuser

# HuggingFace Spaces uses port 7860
EXPOSE 7860

# Run migrations + collectstatic, then launch all processes via supervisord
CMD ["sh", "-c", "\
    python manage.py migrate --noinput && \
    python manage.py collectstatic --noinput && \
    supervisord -c /etc/supervisor/conf.d/app.conf"]
