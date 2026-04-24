"""
FristenAnalyzer — KI-gestützte Analyse von Verwaltungstexten.
Primär: Ollama (lokal, DSGVO-konform)
Optional: Claude API (Cloud-Fallback)
"""

import json
import logging
import urllib.request
import urllib.error
from pathlib import Path
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)

# Standard-Modell und URL
OLLAMA_STANDARD_URL = "http://localhost:11434"
OLLAMA_STANDARD_MODELL = "llama3"


class FristenAnalyzer:
    """KI-Analyse von Verwaltungstexten zur Fristenerkennung."""

    def __init__(self, config: Optional[dict] = None):
        """
        Initialisiert den FristenAnalyzer.

        Args:
            config: Konfigurationsdictionary
        """
        self.config = config or {}
        ki_config = self.config.get("ki", {})

        # Ollama-Einstellungen (Standard)
        self.ollama_url = ki_config.get("ollama_url", OLLAMA_STANDARD_URL)
        self.ollama_modell = ki_config.get("ollama_modell", OLLAMA_STANDARD_MODELL)
        self.ollama_verfuegbar = self._pruefe_ollama()

        # Claude-Einstellungen (optionaler Fallback)
        self.claude_api_key = ki_config.get("claude_api_key", "")
        self.claude_modell = ki_config.get("claude_modell", "claude-3-haiku-20240307")

        # Prompts laden
        self.prompt_fristenerkennung = self._lade_prompt("prompts/fristenerkennung.txt")
        self.prompt_handlungstipp = self._lade_prompt("prompts/handlungstipp.txt")

    def _pruefe_ollama(self) -> bool:
        """Prüft ob Ollama erreichbar ist."""
        try:
            url = f"{self.ollama_url}/api/tags"
            with urllib.request.urlopen(url, timeout=5):
                return True
        except Exception:
            logger.warning("Ollama nicht erreichbar — Claude-Fallback wird verwendet falls konfiguriert.")
            return False

    def _lade_prompt(self, dateipfad: str) -> str:
        """Lädt einen System-Prompt aus einer Textdatei."""
        pfad = Path(dateipfad)
        if pfad.exists():
            return pfad.read_text(encoding="utf-8")
        return ""

    def _ollama_anfrage(self, system_prompt: str, nutzer_text: str) -> Optional[str]:
        """
        Sendet eine Anfrage an die Ollama API.

        Args:
            system_prompt: System-Prompt für den Kontext
            nutzer_text: Der zu analysierende Text

        Returns:
            Antwort der KI als String oder None bei Fehler
        """
        url = f"{self.ollama_url}/api/chat"
        payload = json.dumps({
            "model": self.ollama_modell,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": nutzer_text},
            ],
            "stream": False,
            "format": "json",
        }).encode("utf-8")

        try:
            req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=120) as resp:
                antwort = json.loads(resp.read().decode("utf-8"))
                return antwort.get("message", {}).get("content", "")
        except Exception as e:
            logger.error(f"Ollama-Anfrage fehlgeschlagen: {e}")
            return None

    def _claude_anfrage(self, system_prompt: str, nutzer_text: str) -> Optional[str]:
        """
        Sendet eine Anfrage an die Claude API (optionaler Fallback).

        Args:
            system_prompt: System-Prompt für den Kontext
            nutzer_text: Der zu analysierende Text

        Returns:
            Antwort der KI als String oder None bei Fehler
        """
        if not self.claude_api_key:
            logger.warning("Claude API Key nicht konfiguriert.")
            return None

        url = "https://api.anthropic.com/v1/messages"
        payload = json.dumps({
            "model": self.claude_modell,
            "max_tokens": 4096,
            "system": system_prompt,
            "messages": [{"role": "user", "content": nutzer_text}],
        }).encode("utf-8")

        try:
            req = urllib.request.Request(url, data=payload, headers={
                "Content-Type": "application/json",
                "x-api-key": self.claude_api_key,
                "anthropic-version": "2023-06-01",
            })
            with urllib.request.urlopen(req, timeout=120) as resp:
                antwort = json.loads(resp.read().decode("utf-8"))
                # Claude gibt Inhalt als Array zurück
                inhalte = antwort.get("content", [])
                for inhalt in inhalte:
                    if inhalt.get("type") == "text":
                        return inhalt["text"]
                return None
        except Exception as e:
            logger.error(f"Claude-Anfrage fehlgeschlagen: {e}")
            return None

    def _ki_anfrage(self, system_prompt: str, nutzer_text: str) -> Optional[str]:
        """
        Sendet eine KI-Anfrage — primär Ollama, Fallback Claude.

        Args:
            system_prompt: System-Prompt
            nutzer_text: Nutzertext

        Returns:
            KI-Antwort oder None
        """
        # Primär: Ollama
        if self.ollama_verfuegbar:
            ergebnis = self._ollama_anfrage(system_prompt, nutzer_text)
            if ergebnis:
                return ergebnis
            logger.warning("Ollama-Anfrage fehlgeschlagen, versuche Claude-Fallback...")

        # Fallback: Claude
        if self.claude_api_key:
            return self._claude_anfrage(system_prompt, nutzer_text)

        logger.error("Kein KI-Backend verfügbar.")
        return None

    def detect_fristen(self, text: str) -> List[Dict[str, Any]]:
        """
        Erkennt Fristen in einem Verwaltungstext.

        Args:
            text: Der zu analysierende Text

        Returns:
            Liste der erkannten Fristen
        """
        if not text or len(text.strip()) < 20:
            logger.warning("Text zu kurz für Analyse")
            return []

        antwort = self._ki_anfrage(self.prompt_fristenerkennung, text)
        if not antwort:
            return []

        # JSON aus der Antwort extrahieren
        fristen = self._parse_json_antwort(antwort)
        return fristen

    def classify_frist(self, frist: Dict[str, Any]) -> str:
        """
        Klassifiziert eine Frist nach Dringlichkeit.

        Args:
            frist: Fristen-Dictionary

        Returns:
            Klassifizierung: "kritisch", "hoch", "mittel", "niedrig"
        """
        # Regelmäßige Ausdrücke für gesetzliche Fristen
        gesetzlich_kritisch = ["einspruch", "widerspruch", "klage", "anfechtung"]
        gesetzlich_hoch = ["stellungnahme", "anhörung", "auskunft", "mitteilung"]

        beschreibung = frist.get("beschreibung", "").lower()
        typ = frist.get("frist_typ", "").lower()
        gesamt = f"{beschreibung} {typ}"

        if any(wort in gesamt for wort in gesetzlich_kritisch):
            return "kritisch"
        elif any(wort in gesamt for wort in gesetzlich_hoch):
            return "hoch"
        else:
            return "mittel"

    def generate_handlungstipp(self, frist: Dict[str, Any]) -> Optional[str]:
        """
        Generiert einen Handlungstipp für eine erkannte Frist.

        Args:
            frist: Fristen-Dictionary

        Returns:
            Handlungstipp als Text oder None
        """
        frist_text = json.dumps(frist, ensure_ascii=False, indent=2)
        antwort = self._ki_anfrage(self.prompt_handlungstipp, frist_text)

        if antwort:
            return antwort.strip()
        return None

    def estimate_priority(self, frist: Dict[str, Any]) -> str:
        """
        Schätzt die Priorität einer Frist ein.

        Args:
            frist: Fristen-Dictionary mit frist_datum

        Returns:
            Priorität: "kritisch", "hoch", "mittel", "niedrig"
        """
        from datetime import datetime

        # Zeitliche Dringlichkeit
        datum_str = frist.get("frist_datum")
        if datum_str:
            try:
                frist_dt = datetime.fromisoformat(str(datum_str).replace("Z", "+00:00"))
                tage = (frist_dt - datetime.now()).days
                if tage <= 3:
                    return "kritisch"
                elif tage <= 7:
                    return "hoch"
                elif tage <= 14:
                    return "mittel"
                else:
                    return "niedrig"
            except ValueError:
                pass

        # Fallback: Klassifizierung
        return self.classify_frist(frist)

    def _parse_json_antwort(self, antwort: str) -> List[Dict[str, Any]]:
        """
        Extrahiert JSON aus einer KI-Antwort.

        Args:
            antwort: Rohe KI-Antwort

        Returns:
            Liste von Dictionaries
        """
        # Direkt als JSON versuchen
        try:
            daten = json.loads(antwort)
            if isinstance(daten, list):
                return daten
            elif isinstance(daten, dict) and "fristen" in daten:
                return daten["fristen"]
            return [daten]
        except json.JSONDecodeError:
            pass

        # JSON-Block in Markdown-Antwort suchen
        import re
        json_match = re.search(r"```(?:json)?\s*\n?(.*?)\n?\s*```", antwort, re.DOTALL)
        if json_match:
            try:
                daten = json.loads(json_match.group(1))
                if isinstance(daten, list):
                    return daten
                elif isinstance(daten, dict) and "fristen" in daten:
                    return daten["fristen"]
                return [daten]
            except json.JSONDecodeError:
                pass

        # Array-Muster suchen
        array_match = re.search(r"\[.*\]", antwort, re.DOTALL)
        if array_match:
            try:
                return json.loads(array_match.group(0))
            except json.JSONDecodeError:
                pass

        logger.warning("Konnte keine gültige JSON-Fristen aus KI-Antwort extrahieren")
        return []
