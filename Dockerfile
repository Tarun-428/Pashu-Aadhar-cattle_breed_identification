FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies needed for some Python packages (Pillow, etc.)
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       build-essential \
       libpq-dev \
       libjpeg-dev \
       zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps
COPY requirements.txt /app/
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir gunicorn

# Copy application code
# Copy model explicitly so it's present in the image and can be cached separately
COPY resnet50_model.h5 /app/resnet50_model.h5
COPY . /app

# Configure model path environment variable
ENV MODEL_PATH=/app/resnet50_model.h5

# Ensure upload dir exists
RUN mkdir -p /app/static/uploads

EXPOSE 5000

# Use gunicorn to serve the Flask app. The Flask app object is in app.py (`app:app`).
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
