FROM python:3.11-slim

RUN apt-get -y update && apt-get -y install git
RUN git clone https://github.com/junwha0511/hexa-delivery-backend
COPY requirements.txt .
RUN pip3 install -r requirements.txt
# COPY .env ./

WORKDIR /hexa-delivery-backend
ENTRYPOINT ["gunicorn", "main:app", "--access-logfile", "/server/access.log", "--error-logfile", "/server/error.log", "-b", "0.0.0.0:7777", "-w", "4", "--timeout=10", "-k", "gevent"]
