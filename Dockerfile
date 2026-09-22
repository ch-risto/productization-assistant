# syntax=docker/dockerfile:1
FROM node:24-bookworm-slim AS frontend
WORKDIR /build
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.12-slim-bookworm AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY backend/requirements.lock.txt /app/backend/requirements.lock.txt
RUN pip install --no-cache-dir -r backend/requirements.lock.txt     && groupadd --gid 10001 app     && useradd --uid 10001 --gid app --no-create-home app
COPY backend/app/ /app/backend/app/
COPY scripts/ /app/scripts/
COPY demo-data/ /app/demo-data/
COPY --from=frontend /build/dist/ /app/frontend/dist/
RUN mkdir -p /app/data && chown app:app /app/data
USER app
EXPOSE 8000
HEALTHCHECK --interval=15s --timeout=5s --start-period=20s --retries=5   CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/health', timeout=3)"
CMD ["python", "-m", "uvicorn", "app.main:app", "--app-dir", "backend", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
