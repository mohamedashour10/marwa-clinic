FROM python:3.11-slim

WORKDIR /app

# system deps
RUN apt-get update && apt-get install -y build-essential libpq-dev && rm -rf /var/lib/apt/lists/*

# dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# copy app
COPY . .

# environment defaults
ENV FLASK_APP=app.py
ENV FLASK_ENV=production
ENV PORT=8000

# Expose port
EXPOSE 8000

# Run with gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "app:create_app()"]
