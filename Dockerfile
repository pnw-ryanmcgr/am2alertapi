FROM gcr.io/google-appengine/python

RUN virtualenv /env

ENV VIRTUAL_ENV /env
ENV PATH /env/bin:$PATH

ADD requirements.txt /app/requirements.txt
RUN pip install -r /app/requirements.txt

ADD am2alertapi /app/am2alertapi

CMD [ "python", "/app/am2alertapi" ]
