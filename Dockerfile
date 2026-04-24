FROM python:3.11-slim

WORKDIR /app

# System-Abhängigkeiten
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Python-Abhängigkeiten
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# App-Dateien kopieren
COPY app.py .
COPY processor/ processor/
COPY database/ database/
COPY prompts/ prompts/
COPY email_templates/ email_templates/

# Uploads-Verzeichnis
RUN mkdir -p /app/uploads

# Healthcheck-Port
EXPOSE 8501

# Streamlit starten
CMD ["streamlit", "run", "app.py", \
     "--server.port=8501", \
     "--server.address=0.0.0.0", \
     "--server.headless=true", \
     "--server.enableCORS=false", \
     "--server.enableXsrfProtection=false"]
