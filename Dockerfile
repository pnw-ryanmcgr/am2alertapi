FROM gcr.io/google-appengine/python

RUN virtualenv -p python3.7 /env

ENV VIRTUAL_ENV /env
ENV PATH /env/bin:$PATH

ADD requirements.txt /app/requirements.txt
RUN pip install -r /app/requirements.txt

ADD gunicorn.conf  /app/gunicorn.conf
ADD am2alertapi.py /app/am2alertapi.py
ENV FLASK_APP=/app/am2alertapi.py

CMD gunicorn --config /app/gunicorn.conf am2alertapi:server
