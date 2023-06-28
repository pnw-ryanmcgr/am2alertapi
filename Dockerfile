FROM python:3.10-slim

ENV PROMETHEUS_MULTIPROC_DIR=/tmp/metric-multi
RUN mkdir -p /tmp/metric-multi

ENV PATH="/venv/bin:$PATH"
RUN python3 -m venv /venv

COPY requirements.txt /app/requirements.txt
RUN pip install -r /app/requirements.txt
COPY am2alertapi.py /app/am2alertapi.py

# Without Apache style request logging (for production use)
# In production its noisy to log all the health check requests
ENTRYPOINT ["hypercorn", "asgi:app.am2alertapi:server", "-b", ":3080", \
            "--worker-class=asyncio", "--workers=2", "--log-level", "INFO"]

# With Apache style request logging (for debugging)
# ENTRYPOINT ["hypercorn", "asgi:app.am2alertapi:server", "-b", ":3080", \
#             "--worker-class=asyncio", "--workers=2", "--access-logfile", "-", "--log-level", "INFO"]

