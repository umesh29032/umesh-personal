# Kapil Enterprises ERP — production app image (deploy direction C, 2026-06-11).
# Exact-pinned base (owner rule: no floating tags). All Python deps ship wheels
# (psycopg2-binary, Pillow, argon2-cffi, reportlab) → no compiler, single stage.
FROM python:3.10.16-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    DJANGO_SETTINGS_MODULE=config.settings.production

# Layer-cache deps separately from app code.
COPY requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt

# Non-root runtime user. Apps are importable top-level from config/ (the repo's
# documented working dir — see .importlinter header), so that's the WORKDIR.
RUN useradd --create-home --uid 1000 app
COPY --chown=app:app config /srv/app/config
WORKDIR /srv/app/config

# Writable dirs the app touches at import/runtime: logs/ (base.py mkdir),
# staticfiles/ (collectstatic at entrypoint), media/ (named volume mounts here).
RUN mkdir -p logs staticfiles media && chown -R app:app logs staticfiles media

COPY --chown=app:app deploy/entrypoint.sh /srv/app/entrypoint.sh
RUN chmod +x /srv/app/entrypoint.sh

USER app
EXPOSE 8000
ENTRYPOINT ["/srv/app/entrypoint.sh"]
# 3 sync workers fits a 2-4GB box; access/error logs → stdout (PD logging rule).
CMD ["gunicorn", "config.wsgi:application", \
     "--bind", "0.0.0.0:8000", "--workers", "3", \
     "--access-logfile", "-", "--error-logfile", "-"]
