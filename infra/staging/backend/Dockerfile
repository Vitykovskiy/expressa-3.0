FROM python:3.12-alpine

WORKDIR /app

COPY apps /app/apps
COPY infra/staging/backend/app.py /app/app.py

RUN mkdir -p /data

EXPOSE 8081

CMD ["python", "/app/app.py"]
