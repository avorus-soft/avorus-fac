FROM python:3.7.17-slim

COPY ./requirements.txt .
RUN pip install -r requirements.txt --no-cache-dir


