FROM python:3.7-slim

ENV PATH="/venv/bin:$PATH"
RUN python3 -m venv /venv

COPY requirements.txt /app/requirements.txt
RUN pip install -r /app/requirements.txt
COPY am2alertapi.py /app/am2alertapi.py

ENTRYPOINT ["gunicorn", "app.am2alertapi:server", "-b", ":3080"]
CMD ["--worker-class=eventlet", "--log-level", "INFO"]

# With Apache style request logging
#CMD ["--worker-class=eventlet", "--access-logfile", "-", "--log-level", "INFO"]

