# Installationsanleitung — Schritt für Schritt

## Voraussetzungen

| Software | Version | Link |
|---|---|---|
| Docker | 20.10+ | https://docs.docker.com/get-docker/ |
| Docker Compose | 2.0+ | In Docker Desktop enthalten |
| Ollama | neueste | https://ollama.ai |
| Git | beliebig | https://git-scm.com/ |

## Schritt 1: Repo klonen

```bash
git clone https://github.com/ceeceeceecee/fristenmanager-ki.git
cd fristenmanager-ki
```

## Schritt 2: Ollama installieren

```bash
# Linux / macOS
curl -fsSL https://ollama.ai/install.sh | sh

# Empfohlenes Modell herunterladen
ollama pull llama3

# Ollama starten
ollama serve
```

**Windows:** Ollama von https://ollama.ai/download herunterladen und installieren.

## Schritt 3: Konfiguration anpassen

```bash
cp config/settings.example.yaml config/settings.yaml
```

Bearbeiten Sie `config/settings.yaml`:
1. **SMTP**: Tragen Sie Ihre Mailserver-Daten ein
2. **Vorgesetzter**: E-Mail für Eskalationen
3. **Ollama**: URL und Modellname (Standard: `http://localhost:11434`, `llama3`)

### Passwörter (.env Datei)

Erstellen Sie eine `.env` Datei im Projektverzeichnis:

```env
DB_PASSWORD=ihr_sicheres_passwort
```

## Schritt 4: Setup-Script ausführen

```bash
chmod +x scripts/setup.sh
./scripts/setup.sh
```

Das Script:
1. Prüft Docker-Verfügbarkeit
2. Erstellt die Konfiguration
3. Startet alle Services (PostgreSQL, Redis, App)
4. Fragt nach Demo-Daten

## Schritt 5: App öffnen

Öffnen Sie im Browser: **http://localhost:8501**

### Demo-Modus
Wenn keine Datenbank verbunden ist, startet die App automatisch im Demo-Modus mit Beispieldaten.

## Alternative: Manuelle Installation

Ohne Docker:

```bash
# Python 3.11+ erforderlich
python -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate   # Windows

pip install -r requirements.txt

# Datenbank einrichten (PostgreSQL muss laufen)
psql -U postgres -c "CREATE DATABASE fristenmanager;"
psql -U postgres -d fristenmanager -f database/schema.sql

# App starten
streamlit run app.py
```

## Fehlersuche

### Ollama nicht erreichbar
```bash
# Prüfen ob Ollama läuft
curl http://localhost:11434/api/tags

# Ollama neu starten
ollama serve
```

### Datenbank-Verbindung fehlgeschlagen
```bash
# Prüfen ob PostgreSQL läuft
docker compose ps postgres

# Logs anzeigen
docker compose logs postgres
```

### App startet nicht
```bash
# Logs anzeigen
docker compose logs app

# Neustart
docker compose restart app
```

## Updates

```bash
git pull origin main
docker compose up -d --build
```

## Deinstallation

```bash
docker compose down -v  # Stoppt und löscht alle Daten
rm -rf uploads/         # Hochgeladene Dokumente
```
