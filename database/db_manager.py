"""
DatabaseManager — Datenbankzugriff für den Fristenmanager.
CRUD-Operationen für alle Tabellen mit Connection-Pooling.
"""

import json
import logging
from datetime import datetime, date
from typing import Optional, List, Dict, Any, Tuple

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Verwaltet alle Datenbankoperationen für den Fristenmanager."""

    def __init__(self, host: str = "localhost", port: int = 5432,
                 datenbank: str = "fristenmanager", benutzer: str = "fristen",
                 passwort: str = ""):
        """
        Initialisiert den DatabaseManager.

        Args:
            host: PostgreSQL Host
            port: PostgreSQL Port
            datenbank: Datenbankname
            benutzer: Datenbankbenutzer
            passwort: Datenbankpasswort
        """
        self.conn_params = {
            "host": host,
            "port": port,
            "dbname": datenbank,
            "user": benutzer,
            "password": passwort,
        }
        self._pool = None

    def verbinde(self) -> bool:
        """Stellt eine Verbindung zur Datenbank her."""
        try:
            import psycopg2
            self._pool = psycopg2.connect(**self.conn_params)
            self._pool.autocommit = False
            logger.info("Datenbankverbindung hergestellt")
            return True
        except ImportError:
            logger.error("psycopg2 nicht installiert. Bitte: pip install psycopg2-binary")
            return False
        except Exception as e:
            logger.error(f"Datenbankverbindung fehlgeschlagen: {e}")
            return False

    def _get_connection(self):
        """Gibt die aktuelle Verbindung zurück."""
        if not self._pool:
            self.verbinde()
        return self._pool

    def close(self):
        """Schließt die Datenbankverbindung."""
        if self._pool:
            self._pool.close()
            self._pool = None
            logger.info("Datenbankverbindung geschlossen")

    def _execute(self, query: str, params: tuple = None, fetch: bool = False) -> Any:
        """Führt eine SQL-Abfrage aus."""
        conn = self._get_connection()
        if not conn:
            raise RuntimeError("Keine Datenbankverbindung")

        with conn.cursor() as cur:
            cur.execute(query, params or ())
            if fetch:
                ergebnis = cur.fetchall()
                conn.commit()
                return ergebnis
            conn.commit()
            return cur.rowcount

    def _row_to_dict(self, row: tuple, spalten: list) -> Dict[str, Any]:
        """Konvertiert eine Datenbankzeile in ein Dictionary."""
        ergebnis = {}
        for i, spalte in enumerate(spalten):
            wert = row[i]
            # Datetime/Date in ISO-String konvertieren
            if isinstance(wert, (datetime, date)):
                wert = wert.isoformat()
            ergebnis[spalte] = wert
        return ergebnis

    # ──────────────────────────────────────────────
    # CRUD: Fristen
    # ──────────────────────────────────────────────

    def erstelle_frist(self, daten: Dict[str, Any]) -> int:
        """Erstellt eine neue Frist und gibt die ID zurück."""
        query = """
            INSERT INTO fristen (aktenzeichen, beschreibung, frist_datum, frist_typ,
                                 gesetzliche_grundlage, sachbearbeiter, prioritaet,
                                 status, betroffene_person, dokument_id,
                                 handlungstipp, notizen, ki_vertrauen, erstellt_am)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """
        params = (
            daten.get("aktenzeichen"),
            daten.get("beschreibung"),
            daten.get("frist_datum"),
            daten.get("frist_typ"),
            daten.get("gesetzliche_grundlage"),
            daten.get("sachbearbeiter"),
            daten.get("prioritaet", "mittel"),
            daten.get("status", "offen"),
            daten.get("betroffene_person"),
            daten.get("dokument_id"),
            daten.get("handlungstipp"),
            daten.get("notizen"),
            daten.get("ki_vertrauen"),
            daten.get("erstellt_am", datetime.now().isoformat()),
        )
        ergebnis = self._execute(query, params, fetch=True)
        return ergebnis[0][0] if ergebnis else 0

    def lade_frist(self, frist_id: int) -> Optional[Dict[str, Any]]:
        """Lädt eine einzelne Frist anhand ihrer ID."""
        spalten = ["id", "aktenzeichen", "beschreibung", "frist_datum", "frist_typ",
                    "gesetzliche_grundlage", "sachbearbeiter", "prioritaet", "status",
                    "betroffene_person", "dokument_id", "handlungstipp", "notizen",
                    "ki_vertrauen", "erstellt_am", "aktualisiert_am", "erledigt_am"]
        query = f"SELECT {', '.join(spalten)} FROM fristen WHERE id = %s"
        ergebnis = self._execute(query, (frist_id,), fetch=True)
        if ergebnis:
            return self._row_to_dict(ergebnis[0], spalten)
        return None

    def lade_alle_fristen(self) -> List[Dict[str, Any]]:
        """Lädt alle Fristen sortiert nach Fristdatum."""
        spalten = ["id", "aktenzeichen", "beschreibung", "frist_datum", "frist_typ",
                    "gesetzliche_grundlage", "sachbearbeiter", "prioritaet", "status",
                    "betroffene_person", "dokument_id", "handlungstipp", "notizen",
                    "ki_vertrauen", "erstellt_am", "aktualisiert_am", "erledigt_am"]
        query = f"SELECT {', '.join(spalten)} FROM fristen ORDER BY frist_datum ASC"
        ergebnis = self._execute(query, fetch=True)
        return [self._row_to_dict(row, spalten) for row in ergebnis]

    def lade_offene_fristen(self) -> List[Dict[str, Any]]:
        """Lädt alle offenen Fristen."""
        spalten = ["id", "aktenzeichen", "beschreibung", "frist_datum", "frist_typ",
                    "gesetzliche_grundlage", "sachbearbeiter", "prioritaet", "status",
                    "betroffene_person", "dokument_id", "handlungstipp", "notizen",
                    "ki_vertrauen", "erstellt_am", "aktualisiert_am", "erledigt_am"]
        query = f"""
            SELECT {', '.join(spalten)} FROM fristen
            WHERE status IN ('offen', 'in_bearbeitung')
            ORDER BY frist_datum ASC
        """
        ergebnis = self._execute(query, fetch=True)
        return [self._row_to_dict(row, spalten) for row in ergebnis]

    def aktualisiere_frist(self, frist_id: int, daten: Dict[str, Any]) -> bool:
        """Aktualisiert eine bestehende Frist."""
        felder = []
        werte = []
        for schluessel in ["beschreibung", "frist_datum", "frist_typ", "gesetzliche_grundlage",
                           "sachbearbeiter", "prioritaet", "status", "betroffene_person",
                           "handlungstipp", "notizen", "ki_vertrauen"]:
            if schluessel in daten:
                felder.append(f"{schluessel} = %s")
                werte.append(daten[schluessel])

        if not felder:
            return False

        felder.append("aktualisiert_am = %s")
        werte.append(datetime.now().isoformat())
        werte.append(frist_id)

        query = f"UPDATE fristen SET {', '.join(felder)} WHERE id = %s"
        zeilen = self._execute(query, tuple(werte))
        return zeilen > 0

    def loesche_frist(self, frist_id: int) -> bool:
        """Löscht eine Frist."""
        query = "DELETE FROM fristen WHERE id = %s"
        zeilen = self._execute(query, (frist_id,))
        return zeilen > 0

    # ──────────────────────────────────────────────
    # CRUD: Sachbearbeiter
    # ──────────────────────────────────────────────

    def erstelle_sachbearbeiter(self, daten: Dict[str, Any]) -> int:
        """Erstellt einen neuen Sachbearbeiter."""
        query = """
            INSERT INTO sachbearbeiter (name, email, abteilung, telefon, aktiv)
            VALUES (%s, %s, %s, %s, %s) RETURNING id
        """
        params = (
            daten.get("name"), daten.get("email"), daten.get("abteilung"),
            daten.get("telefon"), daten.get("aktiv", True),
        )
        ergebnis = self._execute(query, params, fetch=True)
        return ergebnis[0][0] if ergebnis else 0

    def suche_sachbearbeiter(self, name: str) -> Optional[Dict[str, Any]]:
        """Sucht einen Sachbearbeiter nach Name."""
        query = "SELECT id, name, email, abteilung, telefon FROM sachbearbeiter WHERE name ILIKE %s AND aktiv = TRUE"
        ergebnis = self._execute(query, (f"%{name}%",), fetch=True)
        if ergebnis:
            return self._row_to_dict(ergebnis[0], ["id", "name", "email", "abteilung", "telefon"])
        return None

    # ──────────────────────────────────────────────
    # CRUD: Dokumente
    # ──────────────────────────────────────────────

    def erstelle_dokument(self, daten: Dict[str, Any]) -> int:
        """Erstellt einen neuen Dokument-Eintrag."""
        query = """
            INSERT INTO dokumente (dateiname, dateityp, dateipfad, rohtext, groesse_bytes, hochgeladen_von)
            VALUES (%s, %s, %s, %s, %s, %s) RETURNING id
        """
        params = (
            daten.get("dateiname"), daten.get("dateityp"), daten.get("dateipfad"),
            daten.get("rohtext"), daten.get("groesse_bytes"), daten.get("hochgeladen_von"),
        )
        ergebnis = self._execute(query, params, fetch=True)
        return ergebnis[0][0] if ergebnis else 0

    # ──────────────────────────────────────────────
    # CRUD: Audit-Log & Eskalationen
    # ──────────────────────────────────────────────

    def erstelle_audit_log(self, daten: Dict[str, Any]) -> int:
        """Erstellt einen Audit-Log-Eintrag."""
        query = """
            INSERT INTO audit_log (aktion, details, benutzer, ip_adresse)
            VALUES (%s, %s, %s, %s) RETURNING id
        """
        params = (daten.get("aktion"), daten.get("details"), daten.get("benutzer"), daten.get("ip_adresse"))
        ergebnis = self._execute(query, params, fetch=True)
        return ergebnis[0][0] if ergebnis else 0

    def erstelle_eskalation(self, daten: Dict[str, Any]) -> int:
        """Erstellt eine Eskalation."""
        query = """
            INSERT INTO eskalationen (frist_id, stufe, grund, empfaenger, erstellt_am)
            VALUES (%s, %s, %s, %s, %s) RETURNING id
        """
        params = (
            daten.get("frist_id"), daten.get("stufe", 1), daten.get("grund"),
            daten.get("empfaenger"), daten.get("erstellt_am", datetime.now().isoformat()),
        )
        ergebnis = self._execute(query, params, fetch=True)
        return ergebnis[0][0] if ergebnis else 0

    def erstelle_erinnerung(self, daten: Dict[str, Any]) -> int:
        """Erstellt einen Erinnerungs-Eintrag."""
        query = """
            INSERT INTO erinnerungen (frist_id, empfaenger, betreff, tage_verbleibend, erfolgreich)
            VALUES (%s, %s, %s, %s, %s) RETURNING id
        """
        params = (
            daten.get("frist_id"), daten.get("empfaenger"), daten.get("betreff"),
            daten.get("tage_verbleibend"), daten.get("erfolgreich", True),
        )
        ergebnis = self._execute(query, params, fetch=True)
        return ergebnis[0][0] if ergebnis else 0

    # ──────────────────────────────────────────────
    # Statistiken
    # ──────────────────────────────────────────────

    def statistiken(self) -> Dict[str, Any]:
        """Liefert aggregierte Statistiken."""
        from datetime import datetime
        heute = datetime.now().date()

        query = """
            SELECT
                COUNT(*) FILTER (WHERE status IN ('offen', 'in_bearbeitung')) AS offen,
                COUNT(*) FILTER (WHERE status = 'erledigt') AS erledigt,
                COUNT(*) FILTER (WHERE status = 'abgelaufen' OR frist_datum < %s) AS abgelaufen,
                COUNT(*) FILTER (WHERE frist_datum BETWEEN %s AND %s + INTERVAL '7 days'
                                 AND status IN ('offen', 'in_bearbeitung')) AS diese_woche,
                COUNT(*) FILTER (WHERE frist_datum BETWEEN %s AND %s + INTERVAL '30 days'
                                 AND status IN ('offen', 'in_bearbeitung')) AS dieser_monat
            FROM fristen
        """
        ergebnis = self._execute(query, (heute, heute, heute, heute, heute), fetch=True)
        if ergebnis:
            row = ergebnis[0]
            return {
                "offen": row[0], "erledigt": row[1], "abgelaufen": row[2],
                "diese_woche": row[3], "dieser_monat": row[4],
            }
        return {}
