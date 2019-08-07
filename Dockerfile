FROM gcr.io/google-appengine/python

RUN virtualenv -p python3 /env

ENV VIRTUAL_ENV /env
ENV PATH /env/bin:$PATH

ADD requirements.txt /app/requirements.txt
RUN pip install -r /app/requirements.txt

ADD am2alertapi.py /app/am2alertapi.py
ENV FLASK_APP=/app/am2alertapi.py

CMD gunicorn --worker-class eventlet --bind :3080 am2alertapi:app
