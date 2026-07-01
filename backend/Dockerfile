FROM python:3.12-slim

WORKDIR /usr/src/app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN pip install --upgrade pip
COPY ./requirements.txt .
RUN pip install -r requirements.txt

COPY . .
CMD ["gunicorn", "app.wsgi", "--access-logfile", "-", \
    "--workers", "2", "--bind", "0.0.0.0:8000"]