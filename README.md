# 🏛️ Fristenmanager-KI – Automatische Fristenerkennung für Behörden

![DSGVO-konform](https://img.shields.io/badge/DSGVO-konform-brightgreen)
![Self-Hosted](https://img.shields.io/badge/Deployment-Self_Hosted-blue)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED)
![Python](https://img.shields.io/badge/Python-3.11+-3776AB)
![Ollama](https://img.shields.io/badge/KI-Backend-Ollama-white)

## 🚨 Das Problem

Verpasste Fristen in Behörden bedeuten **rechtliches Risiko**, Verzögerungen in Verwaltungsverfahren und potenzielle Regressforderungen. Sachbearbeiter müssen Hunderte von Dokumenten überwachen — bei sinkenden Personalressourcen eine wachsende Herausforderung.

**Fristenmanager-KI** erkennt automatisch Fristen aus Eingangspost, Bescheiden und Verwaltungsdokumenten und überwacht diese mit einem intuitiven Ampel-Dashboard.

## ✅ Features

- **🔍 Automatische Fristenerkennung** — KI analysiert PDF- und DOCX-Dokumente und extrahiert Fristen
- **🚦 Ampel-Dashboard** — Grüne (>14 Tage), gelbe (3–14 Tage), rote (<3 Tage) Visualisierung
- **📧 Intelligente Erinnerungen** — Automatische E-Mail-Erinnerungen an Sachbearbeiter
- **⚡ Eskalationsmanagement** — Automatische Eskalation bei drohenden Fristverletzungen
- **🧠 Lokale KI (Ollama)** — DSGVO-konform, keine Datenabgabe an Cloud-Dienste
- **📊 Statistiken & Berichte** — Übersicht über Fristenlast, Bearbeitungszeiten, Team-Performance
- **🔐 Audit-Log** — Vollständige Nachverfolgung aller Aktionen
- **🐳 Ein-Kommando-Install** — `docker compose up -d` und loslegen



## 📸 Screenshots

### Dashboard — Ampelübersicht aller Fristen
![Dashboard](screenshots/dashboard.png)

### Dokument-Analyse — KI erkennt Fristen automatisch
![Dokument-Analyse](screenshots/dokument-analyse.png)

### Neue Frist erfassen
![Neue Frist](screenshots/neue-frist.png)

### Statistiken
![Statistiken](screenshots/statistiken.png)

### Einstellungen
![Einstellungen](screenshots/einstellungen.png)

## 🚀 Schnellstart

```bash
# Repo klonen
git clone https://github.com/ceeceeceecee/fristenmanager-ki.git
cd fristenmanager-ki

# Konfiguration anpassen
cp config/settings.example.yaml config/settings.yaml

# Starten
docker compose up -d

# App öffnen
open http://localhost:8501
```

## 📋 Voraussetzungen

| Komponente | Version | Zweck |
|---|---|---|
| Docker | 20.10+ | Container-Deployment |
| Docker Compose | 2.0+ | Service-Orchestrierung |
| Ollama | neueste | Lokale KI-Verarbeitung |

### Ollama einrichten

```bash
# Ollama installieren (https://ollama.ai)
curl -fsSL https://ollama.ai/install.sh | sh

# Empfohlenes Modell herunterladen
ollama pull llama3
```

## ⚙️ Konfiguration

Alle Einstellungen in `config/settings.yaml`:

- **SMTP** — E-Mail-Versand für Erinnerungen
- **Erinnerungsregeln** — Wann und wie oft erinnert wird
- **Eskalation** — Stufen und Empfänger bei Fristverletzungsgefahr
- **Fristentypen** — Wiedervorlage, Stellungnahme, Genehmigung, etc.

## 📁 Projektstruktur

```
fristenmanager-ki/
├── app.py                    # Streamlit Web-App
├── processor/                # KI-Verarbeitung
│   ├── document_scanner.py   # Dokument-Einlesung
│   ├── ki_analyzer.py        # Ollama/Claude Integration
│   └── reminder_engine.py    # Erinnerungen & Eskalation
├── database/                 # Datenbank
│   ├── schema.sql            # PostgreSQL Schema
│   └── db_manager.py         # CRUD-Operationen
├── prompts/                  # KI-Prompts
├── email_templates/          # E-Mail-Vorlagen
├── config/                   # Konfiguration
├── scripts/                  # Setup & Wartung
├── docs/                     # Dokumentation
└── docker-compose.yml        # Container-Setup
```

## 📸 Screenshots

*(Screenshots folgen nach erster Installation)*

## 📄 Dokumentation

- [Installationsanleitung](docs/setup-guide.md)
- [Datenschutzerklärung & DSGVO](docs/datenschutz.md)

## 🛡️ DSGVO-Konformität

- **100% Self-Hosted** — Keine Daten verlassen den Server
- **Lokale KI** — Ollama läuft vollständig auf dem eigenen Server
- **Löschkonzept** — Automatische Datenlöschung nach Aufbewahrungsfristen
- **Audit-Log** — Vollständige Protokollierung aller Zugriffe

## 📜 Lizenz

MIT License — siehe [LICENSE](LICENSE)

---

**Entwickelt für die öffentliche Verwaltung. DSGVO-konform. Open Source.**
