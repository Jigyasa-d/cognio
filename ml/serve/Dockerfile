FROM python:3.11-slim

WORKDIR /app

COPY ml/requirements-ml.txt /app/requirements-ml.txt
RUN pip install --no-cache-dir -r /app/requirements-ml.txt && \
    pip install --no-cache-dir flask

COPY ml /app/ml

WORKDIR /app/ml/serve

EXPOSE 8001

CMD ["python", "app.py"]