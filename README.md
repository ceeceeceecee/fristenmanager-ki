# Fristenmanager Ki

<p align="center">
</p>

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python) ![DSGVO](https://img.shields.io/badge/DSGVO-Konform-brightgreen) ![Self-Hosted](https://img.shields.io/badge/Self-Hosted-blue) ![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker) ![Ollama](https://img.shields.io/badge/Ollama-KI-333?logo=ollama)

> Automatische Fristenerkennung und -überwachung für Behörden

## Overview

KI-gestützte Fristenüberwachung für Behörden. Erkennt automatisch Fristen aus Dokumenten, sendet Erinnerungen und verwaltet Wiedervorlagen. Self-hosted mit Ollama.

## Features

- Automatische Fristenerkennung aus Dokumenten
- KI-gestützte Dokumentenanalyse
- Erinnerungs-System mit E-Mail
- Wiedervorlagen-Verwaltung
- Statistik-Dashboard
- DSGVO-konforme Speicherung

## Tech Stack

| Tech | Zweck |
|------|-------|
| Python 3.11+ | Backend |
| Streamlit | Web-Interface |
| Ollama | Lokale KI |
| PostgreSQL | Datenbank |
| Docker | Deployment |

## Quick Start

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Screenshots

**Dashboard mit Fristenübersicht**

<img src="screenshots/dashboard.png" alt="Dashboard mit Fristenübersicht" width="800">

**Neue Frist erstellen**

<img src="screenshots/neue-frist.png" alt="Neue Frist erstellen" width="800">

**Dokumentenanalyse zur Fristenerkennung**

<img src="screenshots/dokument-analyse.png" alt="Dokumentenanalyse zur Fristenerkennung" width="800">

**Konfiguration**

<img src="screenshots/einstellungen.png" alt="Konfiguration" width="800">

**Statistiken und Reports**

<img src="screenshots/statistiken.png" alt="Statistiken und Reports" width="800">

---

## Contributing

Beiträge sind willkommen! Bitte erstelle einen Issue oder Pull Request.

## License

MIT License — siehe [LICENSE](LICENSE).

<p align="center">
</p>