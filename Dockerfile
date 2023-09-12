FROM python:3.11-slim

RUN apt-get -y update && apt-get -y install git
RUN git clone https://github.com/junwha0511/hexa-delivery-backend
COPY requirements.txt .
RUN pip3 install -r requirements.txt
RUN pip3 install gevent gunicorn
# COPY .env ./
EXPOSE 7777

WORKDIR /hexa-delivery-backend
ENTRYPOINT ["gunicorn", "main:app", "--access-logfile", "access.log", "--error-logfile", "error.log", "-b", "0.0.0.0:7777", "-w", "4", "--timeout=10", "-k", "gevent"]


