"""
DocumentScanner — Einlesen und Analysieren von Verwaltungsdokumenten.
Unterstützt PDF (PyPDF2) und DOCX (python-docx).
"""

import json
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)


class DocumentScanner:
    """Scanner für PDF- und DOCX-Dokumente zur Fristenerkennung."""

    def __init__(self, config: Optional[dict] = None):
        """
        Initialisiert den DocumentScanner.

        Args:
            config: Konfigurationsdictionary mit KI-Einstellungen
        """
        self.config = config or {}

    def scan_document(self, dateipfad: str) -> Dict[str, Any]:
        """
        Scannt ein Dokument und erkennt enthaltene Fristen.

        Args:
            dateipfad: Pfad zum Dokument (PDF oder DOCX)

        Returns:
            Dictionary mit erkannten Fristen und Metadaten
        """
        datei = Path(dateipfad)
        if not datei.exists():
            logger.error(f"Datei nicht gefunden: {dateipfad}")
            return {"fehler": "Datei nicht gefunden", "fristen": []}

        # Text basierend auf Dateityp extrahieren
        suffix = datei.suffix.lower()
        if suffix == ".pdf":
            rohtext = self._lese_pdf(dateipfad)
        elif suffix == ".docx":
            rohtext = self._lese_docx(dateipfad)
        else:
            logger.error(f"Nicht unterstütztes Format: {suffix}")
            return {"fehler": f"Format {suffix} nicht unterstützt", "fristen": []}

        if not rohtext or len(rohtext.strip()) < 20:
            return {"rohtext": rohtext, "fristen": [], "warnung": "Dokument enthält kaum Text"}

        # Fristen extrahieren
        fristen = self.extract_fristen(rohtext)

        return {
            "dateiname": datei.name,
            "dateityp": suffix,
            "rohtext": rohtext,
            "fristen": fristen,
            "anzahl_fristen": len(fristen),
        }

    def _lese_pdf(self, dateipfad: str) -> str:
        """Liest Text aus einer PDF-Datei mit PyPDF2."""
        try:
            from PyPDF2 import PdfReader
            leser = PdfReader(dateipfad)
            seiten_text = []
            for seite in leser.pages:
                text = seite.extract_text()
                if text:
                    seiten_text.append(text)
            return "\n\n".join(seiten_text)
        except ImportError:
            logger.error("PyPDF2 nicht installiert. Bitte: pip install PyPDF2")
            return ""
        except Exception as e:
            logger.error(f"Fehler beim PDF-Lesen: {e}")
            return ""

    def _lese_docx(self, dateipfad: str) -> str:
        """Liest Text aus einer DOCX-Datei mit python-docx."""
        try:
            from docx import Document
            doc = Document(dateipfad)
            absaetze = [absatz.text for absatz in doc.paragraphs if absatz.text.strip()]
            return "\n\n".join(absaetze)
        except ImportError:
            logger.error("python-docx nicht installiert. Bitte: pip install python-docx")
            return ""
        except Exception as e:
            logger.error(f"Fehler beim DOCX-Lesen: {e}")
            return ""

    def extract_fristen(self, text: str) -> List[Dict[str, Any]]:
        """
        Extrahiert Fristen aus einem Text mittels KI-Analyse.

        Args:
            text: Der zu analysierende Text

        Returns:
            Liste der erkannten Fristen als Dictionaries
        """
        try:
            from processor.ki_analyzer import FristenAnalyzer
            analyzer = FristenAnalyzer(self.config)
            return analyzer.detect_fristen(text)
        except Exception as e:
            logger.error(f"Fehler bei der Fristenextraktion: {e}")
            return []

    def validate_fristen(self, fristen: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Validiert erkannte Fristen auf Plausibilität.

        Args:
            fristen: Liste der zu validierenden Fristen

        Returns:
            Validierte Fristen mit zusätzlichem 'valid' Feld
        """
        from datetime import datetime

        validierte = []
        for frist in fristen:
            valid = True
            warnungen = []

            # Prüfe ob Datum vorhanden
            datum_str = frist.get("frist_datum")
            if not datum_str:
                valid = False
                warnungen.append("Kein Datum erkannt")
            else:
                # Versuche Datum zu parsen
                try:
                    if isinstance(datum_str, str):
                        datetime.fromisoformat(datum_str.replace("Z", "+00:00"))
                except ValueError:
                    valid = False
                    warnungen.append(f"Ungültiges Datum: {datum_str}")

            # Prüfe Beschreibung
            if not frist.get("beschreibung"):
                warnungen.append("Keine Beschreibung vorhanden")

            frist_copy = dict(frist)
            frist_copy["valid"] = valid
            frist_copy["warnungen"] = warnungen
            validierte.append(frist_copy)

        return validierte
