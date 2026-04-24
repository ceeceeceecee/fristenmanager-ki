# Datenschutzerklärung & DSGVO-Konformität

## Übersicht

Der Fristenmanager-KI wurde unter Berücksichtigung der Datenschutz-Grundverordnung (DSGVO) entwickelt. Alle personenbezogenen Daten werden ausschließlich lokal verarbeitet.

## Grundprinzipien

### 1. Datenminimierung (Art. 5 Abs. 1 lit. c DSGVO)
Es werden nur Daten verarbeitet, die zur Erfüllung der Aufgabe (Fristüberwachung) zwingend erforderlich sind:
- Name des Sachbearbeiters
- Aktenzeichen
- Fristdatum und -beschreibung
- Name betroffener Personen (falls im Dokument erwähnt)

### 2. Lokale Verarbeitung (Art. 44 DSGVO)
- **Kein Cloud-Export**: Alle Daten verbleiben auf dem eigenen Server
- **Lokale KI**: Ollama läuft vollständig auf dem eigenen Server — keine Datenabgabe an externe KI-Dienste
- **Optional**: Claude API als Cloud-Fallback — erfordert separate DSV und Auftragsverarbeitungsvertrag

### 3. Speicherbegrenzung (Art. 5 Abs. 1 lit. e DSGVO)
Siehe Löschkonzept unten.

## Löschkonzept

Automatische Löschung nach folgenden Aufbewahrungsfristen:

| Datenkategorie | Aufbewahrung | Löschmethode |
|---|---|---|
| Offene Fristen | Bis Erledigung | — |
| Erledigte Fristen | 365 Tage | Automatische Löschung |
| Abgelaufene Fristen | 365 Tage | Automatische Löschung |
| Dokumente (Uploads) | 180 Tage | Automatische Löschung |
| Audit-Log | 90 Tage | Automatische Löschung |
| Erinnerungen | 365 Tage | Automatische Löschung |
| Eskalationen | 365 Tage | Automatische Löschung |

### Umsetzung
- Cron-Job prüft täglich auf zu löschende Datensätze
- Konfigurierbar in `config/settings.yaml` unter `aufbewahrung`
- Manuelle Löschung jederzeit über die Benutzeroberfläche möglich

## Sicherheit

### Transportverschlüsselung
- HTTPS für die Web-Anwendung empfohlen
- STARTTLS für E-Mail-Versand

### Zugriffskontrolle
- Datenbankzugriff nur über den Application-Layer
- Kein direkter DB-Zugriff von außen
- Audit-Log protokolliert alle Zugriffe

### Passwörter
- SMTP-Passwörter in `.env` Datei (nicht im Repository)
- Datenbank-Passwörter über Docker-Environment-Variablen

## Betroffenenrechte

| Recht | Umsetzung |
|---|---|
| Auskunft (Art. 15) | Export-Funktion in der App |
| Berichtigung (Art. 16) | Bearbeitungsfunktion in der App |
| Löschung (Art. 17) | Löschfunktion in der App + automatisches Löschkonzept |
| Einschränkung (Art. 18) | Status-Änderung auf "archiviert" |
| Datenübertragbarkeit (Art. 20) | JSON/CSV-Export |

## Claude API (Optional)

Wenn die Claude API als Fallback aktiviert wird:
- **Zustimmung erforderlich**: Vor Aktivierung ist eine Datenschutz-Folgenabschätzung durchzuführen
- **Auftragsverarbeitungsvertrag**: Mit Anthropic abzuschließen
- **Datenminimierung**: Nur der Textinhalt des Dokuments wird an die API gesendet
- **Keine Metadaten**: Keine Namen, E-Mail-Adressen oder Aktenzeichen an die API
- **Deaktivierbar**: Claude kann jederzeit deaktiviert werden, Ollama bleibt Standard

## Kontakt

Bei Datenschutz-Anfragen wenden Sie sich an die Datenschutzbeauftragte Ihrer Behörde.
