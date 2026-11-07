FROM python:3.12-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    DJANGO_SETTINGS_MODULE=evitrack.settings.production

RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      libpango-1.0-0 \
      libpangoft2-1.0-0 \
      libharfbuzz0b \
      libharfbuzz-subset0 \
      libfontconfig1 \
      libffi8 \
      shared-mime-info \
      fonts-dejavu-core \
      libpq5 \
 && rm -rf /var/lib/apt/lists/*

RUN useradd --create-home --uid 10001 evitrack

WORKDIR /app

COPY requirements/ requirements/
RUN pip install -r requirements/prod.txt

COPY . .

RUN EVITRACK_SECRET_KEY=build-only-not-used-at-runtime python manage.py collectstatic --noinput \
 && mkdir -p /srv/evidence \
 && chown -R evitrack:evitrack /srv/evidence /app/staticfiles

USER evitrack

EXPOSE 8000

CMD ["gunicorn", "evitrack.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--access-logfile", "-"]
