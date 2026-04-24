-- ============================================================
-- Fristenmanager-KI — Datenbankschema (PostgreSQL)
-- ============================================================
-- Alle Tabellen und Felder für den KI-gestützten Fristenmanager
-- Kommentare auf Deutsch für bessere Wartbarkeit
-- ============================================================

-- Sachbearbeiter-Verwaltung
CREATE TABLE IF NOT EXISTS sachbearbeiter (
    id              SERIAL PRIMARY KEY,                    -- Eindeutige ID
    name            VARCHAR(200) NOT NULL,                 -- Name (Nachname, Vorname)
    email           VARCHAR(300) UNIQUE,                   -- E-Mail-Adresse
    abteilung       VARCHAR(200),                          -- Zugehörige Abteilung
    telefon         VARCHAR(50),                           -- Telefonnummer
    aktiv           BOOLEAN DEFAULT TRUE,                  -- Aktiver Mitarbeiter
    erstellt_am     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,   -- Erstellungsdatum
    aktualisiert_am TIMESTAMP DEFAULT CURRENT_TIMESTAMP    -- Letzte Änderung
);

-- Dokumente (hochgeladene Dateien)
CREATE TABLE IF NOT EXISTS dokumente (
    id              SERIAL PRIMARY KEY,                    -- Eindeutige ID
    dateiname       VARCHAR(500) NOT NULL,                 -- Original-Dateiname
    dateityp        VARCHAR(10),                           -- Dateiendung (pdf, docx)
    dateipfad       VARCHAR(1000),                         -- Pfad auf dem Server
    rohtext         TEXT,                                  -- Extrahierter Textinhalt
    groesse_bytes   INTEGER,                               -- Dateigröße in Bytes
    hochgeladen_von VARCHAR(200),                          -- Hochladender Sachbearbeiter
    erstellt_am     TIMESTAMP DEFAULT CURRENT_TIMESTAMP    -- Upload-Zeitpunkt
);

-- Fristen (Haupttabelle)
CREATE TABLE IF NOT EXISTS fristen (
    id                      SERIAL PRIMARY KEY,            -- Eindeutige ID
    aktenzeichen            VARCHAR(200) NOT NULL,         -- Aktenzeichen (z.B. AZ 2024/1234)
    beschreibung            TEXT NOT NULL,                  -- Kurzbeschreibung der Frist
    frist_datum             DATE NOT NULL,                  -- Fälligkeitsdatum
    frist_typ               VARCHAR(100),                   -- Art der Frist (Widerspruch, Stellungnahme, etc.)
    gesetzliche_grundlage   VARCHAR(500),                   -- Rechtsgrundlage (z.B. § 70 VwGO)
    sachbearbeiter          VARCHAR(200),                   -- Zuständiger Sachbearbeiter
    prioritaet              VARCHAR(20) DEFAULT 'mittel',   -- Dringlichkeit (niedrig, mittel, hoch, kritisch)
    status                  VARCHAR(30) DEFAULT 'offen',    -- Status (offen, in_bearbeitung, erledigt, abgelaufen)
    betroffene_person       VARCHAR(300),                   -- Name der betroffenen Person
    dokument_id             INTEGER REFERENCES dokumente(id), -- Zugehöriges Dokument
    handlungstipp           TEXT,                           -- KI-generierter Handlungstipp
    notizen                 TEXT,                           -- Interne Notizen
    ki_vertrauen            DECIMAL(3,2),                   -- KI-Konfidenz (0.00-1.00)
    erstellt_am             TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- Erstellungsdatum
    aktualisiert_am         TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- Letzte Änderung
    erledigt_am             TIMESTAMP                       -- Datum der Erledigung
);

-- Erinnerungen (versendete E-Mail-Erinnerungen)
CREATE TABLE IF NOT EXISTS erinnerungen (
    id              SERIAL PRIMARY KEY,                    -- Eindeutige ID
    frist_id        INTEGER NOT NULL REFERENCES fristen(id) ON DELETE CASCADE, -- Zugehörige Frist
    empfaenger      VARCHAR(300) NOT NULL,                 -- E-Mail-Empfänger
    betreff         VARCHAR(500),                          -- E-Mail-Betreff
    tage_verbleibend INTEGER,                              -- Verbleibende Tage zum Versandzeitpunkt
    versand_am      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,   -- Versandzeitpunkt
    erfolgreich     BOOLEAN DEFAULT TRUE                   -- Versand erfolgreich
);

-- Eskalationen (kritische Fristen an Vorgesetzte)
CREATE TABLE IF NOT EXISTS eskalationen (
    id              SERIAL PRIMARY KEY,                    -- Eindeutige ID
    frist_id        INTEGER NOT NULL REFERENCES fristen(id) ON DELETE CASCADE, -- Zugehörige Frist
    stufe           INTEGER DEFAULT 1,                     -- Eskalationsstufe (1, 2, 3)
    grund           TEXT NOT NULL,                         -- Grund der Eskalation
    empfaenger      VARCHAR(300) NOT NULL,                 -- Vorgesetzter-E-Mail
    status          VARCHAR(30) DEFAULT 'offen',           -- Status (offen, bestaetigt, erledigt)
    bestaetigt_am   TIMESTAMP,                             -- Bestätigungszeitpunkt
    erstellt_am     TIMESTAMP DEFAULT CURRENT_TIMESTAMP    -- Erstellungsdatum
);

-- Audit-Log (vollständige Protokollierung)
CREATE TABLE IF NOT EXISTS audit_log (
    id              SERIAL PRIMARY KEY,                    -- Eindeutige ID
    aktion          VARCHAR(200) NOT NULL,                 -- Art der Aktion
    details         TEXT,                                  -- JSON-Details der Aktion
    benutzer        VARCHAR(200),                          -- Ausführender Benutzer
    ip_adresse      VARCHAR(50),                           -- IP-Adresse (bei Web-Zugriff)
    zeitstempel     TIMESTAMP DEFAULT CURRENT_TIMESTAMP    -- Zeitstempel
);

-- ============================================================
-- Indizes für Performance
-- ============================================================

CREATE INDEX IF NOT EXISTS idx_fristen_datum ON fristen(frist_datum);
CREATE INDEX IF NOT EXISTS idx_fristen_status ON fristen(status);
CREATE INDEX IF NOT EXISTS idx_fristen_sachbearbeiter ON fristen(sachbearbeiter);
CREATE INDEX IF NOT EXISTS idx_fristen_prioritaet ON fristen(prioritaet);
CREATE INDEX IF NOT EXISTS idx_fristen_aktenzeichen ON fristen(aktenzeichen);
CREATE INDEX IF NOT EXISTS idx_erinnerungen_frist ON erinnerungen(frist_id);
CREATE INDEX IF NOT EXISTS idx_eskalationen_frist ON eskalationen(frist_id);
CREATE INDEX IF NOT EXISTS idx_audit_zeitstempel ON audit_log(zeitstempel);
CREATE INDEX IF NOT EXISTS idx_dokumente_datum ON dokumente(erstellt_am);
