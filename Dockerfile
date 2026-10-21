FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --disable-pip-version-check -r requirements.txt \
    && useradd --system --uid 10001 --home /nonexistent --shell /usr/sbin/nologin app
COPY src /app/src
RUN chmod +x /app/src/host/entrypoint.sh
USER 10001:10001
EXPOSE 5000
HEALTHCHECK --interval=30s --timeout=4s --start-period=10s --retries=3 CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:5000/api/v1/health_check/ready', timeout=3)" || exit 1
ENTRYPOINT ["/app/src/host/entrypoint.sh"]
