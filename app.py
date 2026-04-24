"""
Fristenmanager-KI — Streamlit Web-App
Automatische Fristenerkennung für deutsche Behörden
"""

import streamlit as st
import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Konfiguration laden
CONFIG_PATH = os.environ.get("CONFIG_PATH", "config/settings.yaml")

# Seiten-Konfiguration
st.set_page_config(
    page_title="Fristenmanager-KI",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Benutzerdefiniertes CSS für Ampelfarben
st.markdown("""
<style>
.ampel-gruen { background-color: #22c55e; color: white; padding: 8px 16px; border-radius: 8px; font-weight: bold; }
.ampel-gelb { background-color: #eab308; color: white; padding: 8px 16px; border-radius: 8px; font-weight: bold; }
.ampel-rot { background-color: #ef4444; color: white; padding: 8px 16px; border-radius: 8px; font-weight: bold; }
.metric-card { background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 12px; padding: 20px; text-align: center; }
.big-number { font-size: 2.5em; font-weight: bold; }
.stTabs [data-baseweb="tab-list"] { gap: 8px; }
.stTabs [data-baseweb="tab"] { border-radius: 8px 8px 0 0; }
</style>
""", unsafe_allow_html=True)


# ──────────────────────────────────────────────
# Hilfsfunktionen
# ──────────────────────────────────────────────

def lade_konfiguration():
    """Lädt die YAML-Konfiguration oder gibt Standardwerte zurück."""
    try:
        import yaml
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except Exception:
        return {
            "app": {"name": "Fristenmanager-KI", "version": "1.0.0"},
            "ki": {"backend": "ollama", "ollama_url": "http://localhost:11434"},
            "erinnerung": {"vorab_tage": [14, 7, 3, 1]},
        }


def ampel_farbe(tage_verbleibend):
    """Gibt Ampelfarbe basierend auf verbleibenden Tagen zurück."""
    if tage_verbleibend > 14:
        return "gruen"
    elif tage_verbleibend > 3:
        return "gelb"
    else:
        return "rot"


def ampel_emoji(tage_verbleibend):
    """Gibt passendes Emoji für Ampelfarbe zurück."""
    farbe = ampel_farbe(tage_verbleibend)
    emojis = {"gruen": "🟢", "gelb": "🟡", "rot": "🔴"}
    return emojis.get(farbe, "⚪")


def ampel_css_klasse(tage_verbleibend):
    """Gibt CSS-Klasse für Ampelfarbe zurück."""
    return f"ampel-{ampel_farbe(tage_verbleibend)}"


def format_datum(datum):
    """Formatiert ein Datum im deutschen Format."""
    if isinstance(datum, str):
        datum = datetime.fromisoformat(datum)
    return datum.strftime("%d.%m.%Y")


def tage_verbleibend(frist_datum):
    """Berechnet verbleibende Tage bis zur Frist."""
    if isinstance(frist_datum, str):
        frist_datum = datetime.fromisoformat(frist_datum)
    heute = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    frist = frist_datum.replace(hour=0, minute=0, second=0, microsecond=0)
    return (frist - heute).days


# ──────────────────────────────────────────────
# Demo-Daten (wenn keine DB verfügbar)
# ──────────────────────────────────────────────

def erstelle_demo_fristen():
    """Erstellt Demo-Fristen für die Vorschau."""
    heute = datetime.now()
    return [
        {
            "id": 1,
            "aktenzeichen": "AZ 2024/1234",
            "beschreibung": "Stellungnahme zum Bebauungsplan B-4711",
            "frist_datum": (heute + timedelta(days=21)).isoformat(),
            "frist_typ": "Stellungnahme",
            "gesetzliche_grundlage": "§ 3 BauGB",
            "sachbearbeiter": "Müller, Anna",
            "prioritaet": "hoch",
            "status": "offen",
        },
        {
            "id": 2,
            "aktenzeichen": "AZ 2024/5678",
            "beschreibung": "Widerspruchsfrist Bescheid vom 15.03.2024",
            "frist_datum": (heute + timedelta(days=5)).isoformat(),
            "frist_typ": "Widerspruch",
            "gesetzliche_grundlage": "§ 70 VwGO",
            "sachbearbeiter": "Schmidt, Klaus",
            "prioritaet": "hoch",
            "status": "offen",
        },
        {
            "id": 3,
            "aktenzeichen": "AZ 2024/9012",
            "beschreibung": "Genehmigungsfrist Gewerbeanmeldung Fa. Meyer GmbH",
            "frist_datum": (heute + timedelta(days=2)).isoformat(),
            "frist_typ": "Genehmigung",
            "gesetzliche_grundlage": "§ 14 GewO",
            "sachbearbeiter": "Weber, Petra",
            "prioritaet": "kritisch",
            "status": "offen",
        },
        {
            "id": 4,
            "aktenzeichen": "AZ 2024/3456",
            "beschreibung": "Auskunftserteilung nach UIG-Anfrage",
            "frist_datum": (heute + timedelta(days=10)).isoformat(),
            "frist_typ": "Auskunft",
            "gesetzliche_grundlage": "§ 5 UIG",
            "sachbearbeiter": "Müller, Anna",
            "prioritaet": "mittel",
            "status": "in_bearbeitung",
        },
        {
            "id": 5,
            "aktenzeichen": "AZ 2024/7890",
            "beschreibung": "Entschädigungsangebot nach Enteignungsverfahren",
            "frist_datum": (heute - timedelta(days=1)).isoformat(),
            "frist_typ": "Entschädigung",
            "gesetzliche_grundlage": "§ 95 BauGB",
            "sachbearbeiter": "Schmidt, Klaus",
            "prioritaet": "kritisch",
            "status": "abgelaufen",
        },
        {
            "id": 6,
            "aktenzeichen": "AZ 2024/2345",
            "beschreibung": "Bauvoranfrage Bebauungsplan C-0815",
            "frist_datum": (heute + timedelta(days=30)).isoformat(),
            "frist_typ": "Stellungnahme",
            "gesetzliche_grundlage": "§ 2 BauGB",
            "sachbearbeiter": "Weber, Petra",
            "prioritaet": "niedrig",
            "status": "offen",
        },
        {
            "id": 7,
            "aktenzeichen": "AZ 2024/6789",
            "beschreibung": "Anhörung im Planfeststellungsverfahren A7",
            "frist_datum": (heute + timedelta(days=7)).isoformat(),
            "frist_typ": "Anhörung",
            "gesetzliche_grundlage": "§ 73 VwVfG",
            "sachbearbeiter": "Müller, Anna",
            "prioritaet": "hoch",
            "status": "offen",
        },
    ]


# ──────────────────────────────────────────────
# Datenbank-Initialisierung
# ──────────────────────────────────────────────

def initialisiere_db():
    """Versucht die Datenbank zu initialisieren, fällt auf Demo-Modus zurück."""
    try:
        sys.path.insert(0, ".")
        from database.db_manager import DatabaseManager
        config = lade_konfiguration()
        db_config = config.get("datenbank", {})
        db = DatabaseManager(
            host=db_config.get("host", "localhost"),
            port=db_config.get("port", 5432),
            datenbank=db_config.get("name", "fristenmanager"),
            benutzer=db_config.get("user", "fristen"),
            passwort=db_config.get("password", ""),
        )
        db.verbinde()
        return db
    except Exception:
        return None


# ──────────────────────────────────────────────
# Seiten-Funktionen
# ──────────────────────────────────────────────

def seite_dashboard(db, config):
    """Haupt-Dashboard mit Ampel-Übersicht."""
    st.title("🏛️ Fristenmanager-KI — Dashboard")
    st.markdown("---")

    # Fristen laden
    if db:
        try:
            fristen = db.lade_alle_fristen()
            fristen = [dict(f) for f in fristen]
        except Exception:
            fristen = erstelle_demo_fristen()
    else:
        fristen = erstelle_demo_fristen()
        st.info("💡 Demo-Modus aktiv — keine Datenbank verbunden. Starten Sie `docker compose up -d` für den vollen Betrieb.")

    # Kennzahlen
    heute = datetime.now()
    offen = [f for f in fristen if f.get("status") == "offen" or f.get("status") == "in_bearbeitung"]
    kritisch = [f for f in offen if tage_verbleibend(f["frist_datum"]) <= 3]
    abgelaufen = [f for f in fristen if f.get("status") == "abgelaufen" or tage_verbleibend(f["frist_datum"]) < 0]
    diese_woche = [f for f in offen if 0 <= tage_verbleibend(f["frist_datum"]) <= 7]

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("📋 Offene Fristen", len(offen))
    with col2:
        st.metric("🔴 Kritisch", len(kritisch))
    with col3:
        st.metric("⚠️ Diese Woche", len(diese_woche))
    with col4:
        st.metric("❌ Abgelaufen", len(abgelaufen))

    st.markdown("---")

    # Tabs
    tab_offen, tab_kritisch, tab_abgelaufen = st.tabs(["📋 Alle offenen Fristen", "🔴 Kritisch (< 3 Tage)", "❌ Abgelaufen"])

    with tab_offen:
        if not offen:
            st.success("Keine offenen Fristen vorhanden.")
            return
        for f in sorted(offen, key=lambda x: tage_verbleibend(x["frist_datum"])):
            tv = tage_verbleibend(f["frist_datum"])
            if tv < 0:
                continue
            with st.expander(f"{ampel_emoji(tv)} {f['aktenzeichen']} — {f['beschreibung']}", expanded=(tv <= 3)):
                col_a, col_b, col_c = st.columns(3)
                with col_a:
                    st.markdown(f"**📅 Frist:** {format_datum(f['frist_datum'])}")
                    st.markdown(f"**⏳ Verbleibend:** {tv} Tage")
                with col_b:
                    st.markdown(f"**🏷️ Typ:** {f.get('frist_typ', '—')}")
                    st.markdown(f"**📋 Rechtsgrundlage:** {f.get('gesetzliche_grundlage', '—')}")
                with col_c:
                    st.markdown(f"**👤 Sachbearbeiter:** {f.get('sachbearbeiter', '—')}")
                    st.markdown(f"**⚡ Priorität:** {f.get('prioritaet', '—').capitalize()}")
                if tv <= 3:
                    st.markdown(f"<span class='{ampel_css_klasse(tv)}'>⚠️ DRINGEND — Nur noch {tv} Tage!</span>", unsafe_allow_html=True)

    with tab_kritisch:
        if not kritisch:
            st.success("Keine kritischen Fristen.")
            return
        for f in sorted(kritisch, key=lambda x: tage_verbleibend(x["frist_datum"])):
            tv = tage_verbleibend(f["frist_datum"])
            st.error(f"🔴 {f['aktenzeichen']} — {f['beschreibung']} — **Noch {tv} Tage** (bis {format_datum(f['frist_datum'])})")
            st.caption(f"Sachbearbeiter: {f.get('sachbearbeiter', '—')} | {f.get('gesetzliche_grundlage', '—')}")

    with tab_abgelaufen:
        if not abgelaufen:
            st.success("Keine abgelaufenen Fristen.")
            return
        for f in abgelaufen:
            tv = tage_verbleibend(f["frist_datum"])
            st.error(f"❌ {f['aktenzeichen']} — {f['beschreibung']} — **Seit {abs(tv)} Tagen abgelaufen**")


def seite_neue_frist(db):
    """Seite zum manuellen Erfassen einer neuen Frist."""
    st.title("➕ Neue Frist erfassen")
    st.markdown("---")

    with st.form("neue_frist_form"):
        col1, col2 = st.columns(2)

        with col1:
            aktenzeichen = st.text_input("Aktenzeichen *", placeholder="z.B. AZ 2024/1234")
            frist_typ = st.selectbox("Frist-Typ *", [
                "Wiedervorlage", "Stellungnahme", "Widerspruch", "Einspruch",
                "Genehmigung", "Auskunft", "Anhörung", "Entschädigung",
                "Mitteilung", "Sonstige",
            ])
            beschreibung = st.text_area("Beschreibung *", placeholder="Kurze Beschreibung des Sachverhalts...")
            ges_grundlage = st.text_input("Gesetzliche Grundlage", placeholder="z.B. § 70 VwGO")

        with col2:
            frist_datum = st.date_input("Frist-Datum *")
            sachbearbeiter = st.text_input("Sachbearbeiter *", placeholder="Nachname, Vorname")
            prioritaet = st.selectbox("Priorität", ["niedrig", "mittel", "hoch", "kritisch"])
            betroffene_person = st.text_input("Betroffene Person", placeholder="Optional")
            notizen = st.text_area("Interne Notizen", placeholder="Zusätzliche Hinweise...")

        submitted = st.form_submit_button("💾 Frist speichern", type="primary", use_container_width=True)

        if submitted:
            if not all([aktenzeichen, beschreibung, frist_datum, sachbearbeiter]):
                st.error("Bitte alle Pflichtfelder (*) ausfüllen.")
                return

            frist_daten = {
                "aktenzeichen": aktenzeichen,
                "frist_typ": frist_typ,
                "beschreibung": beschreibung,
                "gesetzliche_grundlage": ges_grundlage,
                "frist_datum": frist_datum.isoformat(),
                "sachbearbeiter": sachbearbeiter,
                "prioritaet": prioritaet,
                "betroffene_person": betroffene_person or None,
                "notizen": notizen or None,
                "status": "offen",
                "erstellt_am": datetime.now().isoformat(),
            }

            if db:
                try:
                    db.erstelle_frist(frist_daten)
                    st.success(f"✅ Frist {aktenzeichen} erfolgreich gespeichert!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Fehler beim Speichern: {e}")
            else:
                st.warning("Demo-Modus — Frist würde gespeichert werden:")
                st.json(frist_daten)


def seite_dokument_analyse(db, config):
    """Seite zum Hochladen und Analysieren von Dokumenten."""
    st.title("📄 Dokument-Analyse")
    st.markdown("---")
    st.info("Laden Sie ein PDF- oder DOCX-Dokument hoch. Die KI erkennt automatisch enthaltene Fristen.")

    hochgeladene_datei = st.file_uploader(
        "Dokument hochladen",
        type=["pdf", "docx"],
        help="Unterstützte Formate: PDF, DOCX",
    )

    if hochgeladene_datei:
        with st.spinner("Dokument wird analysiert..."):
            try:
                sys.path.insert(0, ".")
                from processor.document_scanner import DocumentScanner

                scanner = DocumentScanner(config)
                # Datei speichern
                upload_dir = Path("uploads")
                upload_dir.mkdir(exist_ok=True)
                dateipfad = upload_dir / hochgeladene_datei.name
                dateipfad.write_bytes(hochgeladene_datei.read())

                # Scannen
                ergebnis = scanner.scan_document(str(dateipfad))

                if ergebnis and ergebnis.get("fristen"):
                    st.success(f"✅ {len(ergebnis['fristen'])} Frist(en) erkannt!")

                    for i, frist in enumerate(ergebnis["fristen"]):
                        with st.expander(f"📋 Frist {i+1}: {frist.get('beschreibung', 'Unbekannt')}"):
                            col_a, col_b = st.columns(2)
                            with col_a:
                                st.markdown(f"**📅 Datum:** {frist.get('frist_datum', '—')}")
                                st.markdown(f"**🏷️ Typ:** {frist.get('frist_typ', '—')}")
                            with col_b:
                                st.markdown(f"**📋 Grundlage:** {frist.get('gesetzliche_grundlage', '—')}")
                                st.markdown(f"**👤 Betroffener:** {frist.get('betroffene_person', '—')}")
                                st.markdown(f"**🔑 Aktenzeichen:** {frist.get('aktenzeichen', '—')}")

                    # Fristen importieren
                    if st.button("📥 Erkannte Fristen importieren", type="primary"):
                        for frist in ergebnis["fristen"]:
                            frist["status"] = "offen"
                            frist["erstellt_am"] = datetime.now().isoformat()
                            frist["sachbearbeiter"] = st.session_state.get("user", "Unbekannt")
                            if db:
                                db.erstelle_frist(frist)
                        st.success("Alle erkannten Fristen wurden importiert!")
                else:
                    st.warning("⚠️ Keine Fristen im Dokument erkannt.")

                    # Rohtext anzeigen
                    with st.expander("🔍 Extrahierter Text"):
                        st.text(ergebnis.get("rohtext", "Kein Text extrahiert.")[:3000])

            except ImportError:
                st.warning("Dokument-Scanner nicht verfügbar. Versuchen Sie die manuelle Fristenerfassung.")
            except Exception as e:
                st.error(f"Fehler bei der Analyse: {e}")

    st.markdown("---")
    st.subheader("🧠 KI-Textanalyse (manuell)")
    st.markdown("Alternativ können Sie einen Text direkt eingeben:")

    text_input = st.text_area("Verwaltungstext einfügen", height=200,
                               placeholder="Fügen Sie hier den Text eines Bescheides, Schreibens oder Verwaltungsaktes ein...")

    if st.button("🔍 Text analysieren", type="primary") and text_input:
        with st.spinner("KI analysiert den Text..."):
            try:
                sys.path.insert(0, ".")
                from processor.ki_analyzer import FristenAnalyzer

                analyzer = FristenAnalyzer(config)
                fristen = analyzer.detect_fristen(text_input)

                if fristen:
                    st.success(f"✅ {len(fristen)} Frist(en) erkannt!")
                    for i, frist in enumerate(fristen):
                        with st.expander(f"📋 Frist {i+1}"):
                            st.json(frist, expanded=False)
                else:
                    st.info("Keine Fristen erkannt.")
            except Exception as e:
                st.error(f"KI-Analyse fehlgeschlagen: {e}")


def seite_statistiken(db):
    """Statistik-Übersicht."""
    st.title("📊 Statistiken")
    st.markdown("---")

    if db:
        try:
            fristen = [dict(f) for f in db.lade_alle_fristen()]
        except Exception:
            fristen = erstelle_demo_fristen()
    else:
        fristen = erstelle_demo_fristen()

    if not fristen:
        st.info("Noch keine Daten vorhanden.")
        return

    # Fristentypen-Verteilung
    typen = {}
    for f in fristen:
        t = f.get("frist_typ", "Sonstige")
        typen[t] = typen.get(t, 0) + 1

    # Sachbearbeiter-Verteilung
    bearbeiter = {}
    for f in fristen:
        sb = f.get("sachbearbeiter", "Unbekannt")
        bearbeiter[sb] = bearbeiter.get(sb, 0) + 1

    # Prioritäten
    prioritaeten = {}
    for f in fristen:
        p = f.get("prioritaet", "unbekannt")
        prioritaeten[p] = prioritaeten.get(p, 0) + 1

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🏷️ Fristen nach Typ")
        if typen:
            st.bar_chart(typen)
        else:
            st.caption("Keine Daten")

    with col2:
        st.subheader("👤 Fristen nach Sachbearbeiter")
        if bearbeiter:
            st.bar_chart(bearbeiter)
        else:
            st.caption("Keine Daten")

    st.markdown("---")

    col3, col4 = st.columns(2)

    with col3:
        st.subheader("⚡ Prioritätsverteilung")
        if prioritaeten:
            # Farbliche Darstellung
            for prio, anzahl in sorted(prioritaeten.items()):
                farbe = {"kritisch": "🔴", "hoch": "🟠", "mittel": "🟡", "niedrig": "🟢"}.get(prio, "⚪")
                st.markdown(f"{farbe} **{prio.capitalize()}**: {anzahl} Fristen")
        else:
            st.caption("Keine Daten")

    with col4:
        st.subheader("📅 Fristen-Fälligkeitsübersicht")
        # Nächste 30 Tage
        zeitraum = {}
        for i in range(30):
            tag = (datetime.now() + timedelta(days=i)).strftime("%d.%m")
            zeitraum[tag] = sum(
                1 for f in fristen
                if datetime.fromisoformat(f["frist_datum"]).date() == (datetime.now() + timedelta(days=i)).date()
            )
        if any(v > 0 for v in zeitraum.values()):
            st.bar_chart(zeitraum)
        else:
            st.caption("Keine Fristen in den nächsten 30 Tagen")


def seite_einstellungen(config):
    """Einstellungsseite."""
    st.title("⚙️ Einstellungen")
    st.markdown("---")

    tab_ki, tab_email, tab_system = st.tabs(["🧠 KI-Backend", "📧 E-Mail", "🖥️ System"])

    with tab_ki:
        st.subheader("KI-Backend konfigurieren")
        st.info("Ollama ist das Standard-Backend (DSGVO-konform, lokal). Claude API ist optional.")

        backend = st.selectbox("KI-Backend", ["ollama", "claude"], index=0,
                                help="Ollama: Lokal & DSGVO-konform | Claude: Cloud-Fallback")
        ollama_url = st.text_input("Ollama URL", value=config.get("ki", {}).get("ollama_url", "http://localhost:11434"))
        ollama_modell = st.text_input("Ollama Modell", value=config.get("ki", {}).get("ollama_modell", "llama3"))

        st.divider()
        st.subheader("Optional: Claude API")
        claude_api_key = st.text_input("Claude API Key", type="password",
                                        value=config.get("ki", {}).get("claude_api_key", ""),
                                        help="Wird nur verwendet, wenn Ollama nicht verfügbar ist.")
        claude_modell = st.text_input("Claude Modell", value=config.get("ki", {}).get("claude_modell", "claude-3-haiku-20240307"))

        if st.button("💾 KI-Einstellungen speichern", type="primary"):
            st.success("Einstellungen gespeichert! (In der YAML-Datei aktualisieren)")

        st.divider()
        st.subheader("🔍 Verbindung testen")
        if st.button("Ollama testen"):
            import urllib.request
            try:
                url = f"{ollama_url}/api/tags"
                with urllib.request.urlopen(url, timeout=5) as resp:
                    modelle = json.loads(resp.read())
                    verfuegbare = [m["name"] for m in modelle.get("models", [])]
                    st.success(f"✅ Ollama erreichbar! Verfügbare Modelle: {', '.join(verfuegbare)}")
            except Exception as e:
                st.error(f"❌ Ollama nicht erreichbar: {e}")

    with tab_email:
        st.subheader("E-Mail-Einstellungen (SMTP)")
        smtp_host = st.text_input("SMTP-Server", value=config.get("email", {}).get("smtp_host", "mail.beispiel.de"))
        smtp_port = st.number_input("SMTP-Port", value=config.get("email", {}).get("smtp_port", 587))
        smtp_benutzer = st.text_input("Benutzername", value=config.get("email", {}).get("smtp_user", ""))
        smtp_passwort = st.text_input("Passwort", type="password", value=config.get("email", {}).get("smtp_pass", ""))
        absender = st.text_input("Absender-E-Mail", value=config.get("email", {}).get("absender", "fristenmanager@behoerde.de"))

        if st.button("📧 Test-E-Mail senden"):
            st.info("Test-E-Mail-Funktion wird in der YAML-Konfiguration konfiguriert.")

    with tab_system:
        st.subheader("Systeminformationen")
        st.json({
            "App-Version": config.get("app", {}).get("version", "1.0.0"),
            "KI-Backend": config.get("ki", {}).get("backend", "ollama"),
            "Ollama URL": config.get("ki", {}).get("ollama_url", "http://localhost:11434"),
            "Python-Version": sys.version.split()[0],
        })

        st.divider()
        st.subheader("🗑️ Datenbank-Wartung")
        if st.button("Audit-Log bereinigen (älter als 90 Tage)"):
            st.warning("Funktion erfordert aktive Datenbankverbindung.")

        if st.button("Abgelaufene Fristen archivieren"):
            st.warning("Funktion erfordert aktive Datenbankverbindung.")


# ──────────────────────────────────────────────
# Hauptprogramm
# ──────────────────────────────────────────────

def main():
    """Hauptfunktion der Streamlit-App."""
    config = lade_konfiguration()
    db = initialisiere_db()

    # Sidebar
    with st.sidebar:
        st.title("🏛️ Fristenmanager-KI")
        st.caption("Automatische Fristenerkennung\nfür Behörden")

        st.markdown("---")

        # Navigation
        seite = st.radio(
            "Navigation",
            [
                "📊 Dashboard",
                "➕ Neue Frist",
                "📄 Dokument-Analyse",
                "📈 Statistiken",
                "⚙️ Einstellungen",
            ],
            label_visibility="collapsed",
        )

        st.markdown("---")

        # KI-Status
        ki_status = config.get("ki", {}).get("backend", "ollama")
        st.caption(f"🧠 KI: {ki_status.upper()}")

        if db:
            st.caption("💾 DB: Verbunden")
        else:
            st.caption("💾 DB: Demo-Modus")

        st.markdown("---")
        st.caption("Fristenmanager-KI v1.0.0\nMIT License | DSGVO-konform")

    # Seite anzeigen
    if "Dashboard" in seite:
        seite_dashboard(db, config)
    elif "Neue Frist" in seite:
        seite_neue_frist(db)
    elif "Dokument" in seite:
        seite_dokument_analyse(db, config)
    elif "Statistiken" in seite:
        seite_statistiken(db)
    elif "Einstellungen" in seite:
        seite_einstellungen(config)


if __name__ == "__main__":
    main()
