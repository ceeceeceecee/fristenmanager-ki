#!/bin/bash
# ============================================================
# Fristenmanager-KI — Setup-Script
# Initialisiert Datenbank, erstellt Demo-Daten, startet Services
# ============================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "============================================================"
echo "  Fristenmanager-KI — Setup"
echo "============================================================"
echo ""

# Prüfe ob Docker verfügbar ist
if ! command -v docker &> /dev/null; then
    echo "❌ Docker ist nicht installiert. Bitte installieren Sie Docker zuerst."
    exit 1
fi

if ! command -v docker compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose ist nicht verfügbar."
    exit 1
fi

echo "✅ Docker und Docker Compose gefunden."
echo ""

# Konfiguration prüfen
if [ ! -f "$PROJECT_DIR/config/settings.yaml" ]; then
    echo "📋 Konfiguration erstellen..."
    cp "$PROJECT_DIR/config/settings.example.yaml" "$PROJECT_DIR/config/settings.yaml"
    echo "✅ config/settings.yaml erstellt. Bitte anpassen!"
else
    echo "✅ Konfiguration vorhanden."
fi

# Uploads-Verzeichnis
mkdir -p "$PROJECT_DIR/uploads"
echo "✅ Uploads-Verzeichnis erstellt."

echo ""
echo "============================================================"
echo "  Services starten"
echo "============================================================"
echo ""

# Services starten
cd "$PROJECT_DIR"
docker compose up -d

echo ""
echo "Warte auf Datenbank..."
sleep 10

# Demo-Daten einfügen (optional)
read -p "Demo-Daten einfügen? (j/N) " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Jj]$ ]]; then
    echo "📊 Demo-Daten werden eingefügt..."
    docker compose exec -T postgres psql -U fristen -d fristenmanager <<'SQL'
    -- Demo-Sachbearbeiter
    INSERT INTO sachbearbeiter (name, email, abteilung, telefon) VALUES
        ('Müller, Anna', 'anna.mueller@behoerde.de', 'Bauordnung', '+49 123 456'),
        ('Schmidt, Klaus', 'klaus.schmidt@behoerde.de', 'Allgemeine Verwaltung', '+49 123 457'),
        ('Weber, Petra', 'petra.weber@behoerde.de', 'Bauordnung', '+49 123 458')
    ON CONFLICT (email) DO NOTHING;

    -- Demo-Fristen
    INSERT INTO fristen (aktenzeichen, beschreibung, frist_datum, frist_typ, gesetzliche_grundlage, sachbearbeiter, prioritaet, status) VALUES
        ('AZ 2024/1234', 'Stellungnahme zum Bebauungsplan B-4711', CURRENT_DATE + INTERVAL '21 days', 'Stellungnahme', '§ 3 BauGB', 'Müller, Anna', 'hoch', 'offen'),
        ('AZ 2024/5678', 'Widerspruchsfrist Bescheid vom 15.03.2024', CURRENT_DATE + INTERVAL '5 days', 'Widerspruch', '§ 70 VwGO', 'Schmidt, Klaus', 'hoch', 'offen'),
        ('AZ 2024/9012', 'Genehmigungsfrist Gewerbeanmeldung Fa. Meyer GmbH', CURRENT_DATE + INTERVAL '2 days', 'Genehmigung', '§ 14 GewO', 'Weber, Petra', 'kritisch', 'offen'),
        ('AZ 2024/3456', 'Auskunftserteilung nach UIG-Anfrage', CURRENT_DATE + INTERVAL '10 days', 'Auskunft', '§ 5 UIG', 'Müller, Anna', 'mittel', 'in_bearbeitung'),
        ('AZ 2024/7890', 'Entschädigungsangebot nach Enteignungsverfahren', CURRENT_DATE - INTERVAL '1 day', 'Entschädigung', '§ 95 BauGB', 'Schmidt, Klaus', 'kritisch', 'abgelaufen'),
        ('AZ 2024/6789', 'Anhörung im Planfeststellungsverfahren A7', CURRENT_DATE + INTERVAL '7 days', 'Anhörung', '§ 73 VwVfG', 'Müller, Anna', 'hoch', 'offen')
    ON CONFLICT DO NOTHING;

    -- Audit-Log
    INSERT INTO audit_log (aktion, details, benutzer) VALUES
        ('setup', '{"nachricht": "Demo-Daten eingefügt", "fristen": 6, "sachbearbeiter": 3}', 'system')
    ON CONFLICT DO NOTHING;

SQL
    echo "✅ Demo-Daten eingefügt!"
fi

echo ""
echo "============================================================"
echo "  ✅ Setup abgeschlossen!"
echo "============================================================"
echo ""
echo "  📱 App:        http://localhost:8501"
echo "  🐘 Datenbank:  localhost:5432"
echo "  🔴 Redis:      localhost:6379"
echo "  🧠 Ollama:     http://localhost:11434"
echo ""
echo "  ⚠️  Konfiguration anpassen: config/settings.yaml"
echo "  📖 Dokumentation:            docs/setup-guide.md"
echo ""
