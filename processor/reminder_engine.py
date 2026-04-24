"""
ReminderEngine — Erinnerungen und Eskalationsmanagement.
Versendet E-Mail-Erinnerungen und eskaliert bei drohenden Fristverletzungen.
"""

import json
import logging
import smtplib
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)


class ReminderEngine:
    """Verwaltet Erinnerungen und Eskalationen für Fristen."""

    def __init__(self, config: dict, db_manager=None):
        """
        Initialisiert die ReminderEngine.

        Args:
            config: Konfigurationsdictionary mit SMTP- und Eskalations-Einstellungen
            db_manager: Optionaler DatabaseManager für Persistenz
        """
        self.config = config
        self.db = db_manager
        self.email_config = config.get("email", {})
        self.escalation_config = config.get("eskalation", {})
        self.reminder_config = config.get("erinnerung", {})

    def check_all_fristen(self) -> Dict[str, Any]:
        """
        Prüft alle offenen Fristen und löst Erinnerungen/Eskalationen aus.

        Returns:
            Dictionary mit Ergebnis-Zusammenfassung
        """
        ergebnis = {
            "geprueft": 0,
            "erinnerungen": 0,
            "eskalationen": 0,
            "abgelaufen": 0,
            "zeitstempel": datetime.now().isoformat(),
        }

        if not self.db:
            logger.warning("Kein DatabaseManager — kann keine Fristen prüfen.")
            return ergebnis

        try:
            # Alle offenen Fristen laden
            fristen = self.db.lade_offene_fristen()
            ergebnis["geprueft"] = len(fristen)

            for frist in fristen:
                frist = dict(frist)
                frist_datum = datetime.fromisoformat(frist["frist_datum"])
                heute = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
                tage = (frist_datum - heute).days

                # Abgelaufen
                if tage < 0:
                    ergebnis["abgelaufen"] += 1
                    self.escalate(frist, f"ABGELAUFEN seit {abs(tage)} Tagen")
                    continue

                # Eskalation (kritisch: < 3 Tage)
                if tage <= 3:
                    ergebnis["eskalationen"] += 1
                    self.escalate(frist, f"KRITISCH — Nur noch {tage} Tage")
                    continue

                # Reguläre Erinnerungen
                erinnerung_tage = self.reminder_config.get("vorab_tage", [14, 7, 3, 1])
                if tage in erinnerung_tage:
                    ergebnis["erinnerungen"] += 1
                    self.send_reminder(frist, tage)

            self.log_action("batch_pruefung", ergebnis)
            logger.info(f"Fristenprüfung abgeschlossen: {ergebnis}")
            return ergebnis

        except Exception as e:
            logger.error(f"Fehler bei der Fristenprüfung: {e}")
            self.log_action("fehler", {"nachricht": str(e)})
            return ergebnis

    def send_reminder(self, frist: Dict[str, Any], tage_verbleibend: int) -> bool:
        """
        Sendet eine Erinnerungs-E-Mail für eine Frist.

        Args:
            frist: Fristen-Dictionary
            tage_verbleibend: Verbleibende Tage bis zur Frist

        Returns:
            True bei Erfolg, False bei Fehler
        """
        sachbearbeiter = frist.get("sachbearbeiter", "Unbekannt")
        email = self._finde_email(sachbearbeiter)

        if not email:
            logger.warning(f"Keine E-Mail für {sachbearbeiter} gefunden")
            return False

        # Ampelfarbe bestimmen
        if tage_verbleibend > 14:
            ampel = "gruen"
        elif tage_verbleibend > 3:
            ampel = "gelb"
        else:
            ampel = "rot"

        # Template laden
        template = self._lade_template("email_templates/erinnerung.html")
        inhalt = template.replace("{{NAME}}", sachbearbeiter)
        inhalt = inhalt.replace("{{FRIST}}", frist.get("beschreibung", ""))
        inhalt = inhalt.replace("{{AKTENZEICHEN}}", frist.get("aktenzeichen", ""))
        inhalt = inhalt.replace("{{TAGE_VERBLEIBEND}}", str(tage_verbleibend))
        inhalt = inhalt.replace("{{DATUM}}", datetime.fromisoformat(frist["frist_datum"]).strftime("%d.%m.%Y"))
        inhalt = inhalt.replace("{{AMPEL}}", ampel)

        betreff = f"[Fristenmanager] Erinnerung: {frist.get('aktenzeichen', '')} — {tage_verbleibend} Tage verbleibend"

        erfolgreich = self._sende_email(email, betreff, inhalt)
        self.log_action("erinnerung", {
            "frist_id": frist.get("id"),
            "empfaenger": email,
            "tage_verbleibend": tage_verbleibend,
            "erfolgreich": erfolgreich,
        })
        return erfolgreich

    def escalate(self, frist: Dict[str, Any], grund: str) -> bool:
        """
        Eskaliert eine kritische Frist an den Vorgesetzten.

        Args:
            frist: Fristen-Dictionary
            grund: Grund für die Eskalation

        Returns:
            True bei Erfolg, False bei Fehler
        """
        vorgesetzter = self.escalation_config.get("vorgesetzter_email", "")
        if not vorgesetzter:
            logger.warning("Kein Vorgesetzter für Eskalation konfiguriert")
            return False

        template = self._lade_template("email_templates/eskalation.html")
        inhalt = template.replace("{{VORGESETZTER}}", self.escalation_config.get("vorgesetzter_name", "Vorgesetzter"))
        inhalt = inhalt.replace("{{SACHBEARBEITER}}", frist.get("sachbearbeiter", "Unbekannt"))
        inhalt = inhalt.replace("{{FRIST}}", frist.get("beschreibung", ""))
        inhalt = inhalt.replace("{{AKTENZEICHEN}}", frist.get("aktenzeichen", ""))
        inhalt = inhalt.replace("{{GRUND}}", grund)
        inhalt = inhalt.replace("{{DATUM}}", datetime.fromisoformat(frist["frist_datum"]).strftime("%d.%m.%Y"))

        betreff = f"⚠️ ESKALATION: {frist.get('aktenzeichen', '')} — {grund}"

        erfolgreich = self._sende_email(vorgesetzter, betreff, inhalt)

        # Auch an Sachbearbeiter
        sb_email = self._finde_email(frist.get("sachbearbeiter", ""))
        if sb_email and sb_email != vorgesetzter:
            self._sende_email(sb_email, f"[KOPIE] {betreff}", inhalt)

        self.log_action("eskalation", {
            "frist_id": frist.get("id"),
            "grund": grund,
            "vorgesetzter": vorgesetzter,
            "erfolgreich": erfolgreich,
        })

        # In DB speichern
        if self.db:
            try:
                self.db.erstelle_eskalation({
                    "frist_id": frist.get("id"),
                    "grund": grund,
                    "empfaenger": vorgesetzter,
                    "erstellt_am": datetime.now().isoformat(),
                })
            except Exception as e:
                logger.error(f"Fehler beim Speichern der Eskalation: {e}")

        return erfolgreich

    def log_action(self, aktion: str, details: Dict[str, Any]) -> None:
        """
        Protokolliert eine Aktion im Audit-Log.

        Args:
            aktion: Art der Aktion
            details: Detail-Dictionary
        """
        eintrag = {
            "aktion": aktion,
            "details": json.dumps(details, ensure_ascii=False, default=str),
            "zeitstempel": datetime.now().isoformat(),
        }

        logger.info(f"[Audit] {aktion}: {details}")

        if self.db:
            try:
                self.db.erstelle_audit_log(eintrag)
            except Exception as e:
                logger.error(f"Fehler beim Audit-Log: {e}")

    # ──────────────────────────────────────────────
    # Hilfsmethoden
    # ──────────────────────────────────────────────

    def _sende_email(self, empfaenger: str, betreff: str, inhalt_html: str) -> bool:
        """Sendet eine HTML-E-Mail via SMTP."""
        if not self.email_config.get("smtp_host"):
            logger.warning("SMTP nicht konfiguriert — E-Mail wird nicht gesendet")
            return False

        try:
            nachricht = MIMEMultipart("alternative")
            nachricht["Subject"] = betreff
            nachricht["From"] = self.email_config.get("absender", "fristenmanager@behoerde.de")
            nachricht["To"] = empfaenger

            # Nur HTML-Part
            html_part = MIMEText(inhalt_html, "html", "utf-8")
            nachricht.attach(html_part)

            # SMTP-Verbindung
            smtp = smtplib.SMTP(
                self.email_config.get("smtp_host", "localhost"),
                self.email_config.get("smtp_port", 587),
            )
            smtp.starttls()

            benutzer = self.email_config.get("smtp_user")
            passwort = self.email_config.get("smtp_pass")
            if benutzer and passwort:
                smtp.login(benutzer, passwort)

            smtp.sendmail(nachricht["From"], empfaenger, nachricht.as_string())
            smtp.quit()
            return True

        except Exception as e:
            logger.error(f"E-Mail-Versand fehlgeschlagen: {e}")
            return False

    def _lade_template(self, dateipfad: str) -> str:
        """Lädt ein E-Mail-Template aus einer Datei."""
        pfad = Path(dateipfad)
        if pfad.exists():
            return pfad.read_text(encoding="utf-8")
        return "<html><body><p>Template nicht gefunden.</p></body></html>"

    def _finde_email(self, sachbearbeiter: str) -> Optional[str]:
        """Findet die E-Mail-Adresse eines Sachbearbeiters."""
        if not self.db:
            return None
        try:
            daten = self.db.suche_sachbearbeiter(sachbearbeiter)
            if daten:
                return daten.get("email")
        except Exception:
            pass
        return None
