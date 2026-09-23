# --- frontend build -------------------------------------------------------
FROM node:20-slim AS frontend
WORKDIR /build
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# --- backend --------------------------------------------------------------
FROM python:3.11-slim

# libgomp is XGBoost's OpenMP runtime; without it the import fails.
RUN apt-get update \
    && apt-get install -y --no-install-recommends libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ ./backend/
COPY ml/ ./ml/
COPY migrations/ ./migrations/
COPY --from=frontend /build/dist ./frontend/dist

RUN mkdir -p data/uploads models

# Train on synthetic data at build time so the image is demoable as-is.
# Mount a volume over /app/models to supply your own artifacts instead.
RUN python -m ml.train --rows 24000

# Run as an unprivileged user. Root in a container is root on the host if the
# runtime is ever escaped, and nothing here needs those privileges.
# UID 1000 specifically: Hugging Face Spaces runs the container as that user
# and does not remap it, so anything owned by another uid is unwritable there.
# Any host can run this; only HF is fussy about the number.
RUN useradd --create-home --uid 1000 appuser \
    && chown -R appuser:appuser /app
USER appuser

# 7860 is what Hugging Face Spaces routes to by default (and what `app_port`
# in README.md declares); it injects no PORT variable, so the image has to
# default to it. A platform that does inject one -- Render, Fly, Cloud Run --
# overrides this at runtime, because runtime environment beats image ENV.
ENV PORT=7860
EXPOSE 7860

# Lets the orchestrator restart a container whose model failed to load rather
# than leaving it serving 503s.
HEALTHCHECK --interval=30s --timeout=5s --start-period=40s --retries=3 \
    CMD python -c "import os,urllib.request,sys; p=os.getenv('PORT','2800'); sys.exit(0 if urllib.request.urlopen(f'http://localhost:{p}/api/health', timeout=4).status == 200 else 1)"

# Migrations run once, before the workers start. Doing it here rather than in
# the app factory keeps two workers from racing to apply the same revision.
# One worker, not two. Each worker holds its own copy of the model and the
# SHAP explainer -- measured at ~473 MB resident after a first explained
# prediction -- so a second worker does not fit in a 512 MB instance.
CMD ["sh", "-c", "flask --app 'backend.app:create_app' db upgrade && exec gunicorn --bind 0.0.0.0:${PORT:-2800} --workers 1 --timeout 120 'backend.app:create_app()'"]
