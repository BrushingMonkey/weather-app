FROM python:3.12-slim

WORKDIR /weather_app

COPY requirements.txt .
COPY ./weather_project .

RUN pip install --upgrade pip setuptools wheel
RUN pip install --no-cache-dir --upgrade -r requirements.txt

CMD gunicorn --bind 0.0.0.0:5000 wsgi:app
