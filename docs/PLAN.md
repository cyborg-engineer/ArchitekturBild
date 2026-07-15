# PLAN.md - ArchitekturBild MVP

## Ziel
Den in `AGENTS.md` definierten Scope als lokal lauffaehige Anwendung liefern, bei der Bild, Prompt, Modellauswahl und LLM-Beschreibung synchron sind, alle LLM-Calls historisiert werden und die Daten in PostgreSQL persistent gespeichert sind.

## Referenzen
- Anforderungen: [`AGENTS.md`](../AGENTS.md)
- Ziel-Dokument: [`docs/PLAN.md`](./PLAN.md)

## Fortschritt
- [x] AP1 - Projektgrundlage und Struktur
- [x] AP2 - Backend-MVP (FastAPI + OpenRouter)
- [x] AP3 - Frontend-MVP (Upload, Prompt, Modell, Ausgabe)
- [x] AP4 - End-to-End-Integration und Zustandslogik
- [x] AP5 - UI-Styling gemaess Farbkonzept
- [x] AP6 - Skripte und lokaler Betrieb (Mac)
- [x] AP7 - Qualitaetssicherung und MVP-Abnahme
- [x] AP8 - Persistenzschicht mit PostgreSQL
- [x] AP9 - Historienfunktion im Frontend
- [x] AP10 - QA-Erweiterung fuer Persistenz und Historie

## Arbeitspakete

### AP1 - Projektgrundlage und Struktur
**Ziel:** Saubere Projektbasis fuer lokale Entwicklung und spaetere Umsetzung der Features.

**Deliverables (Checkliste):**
- [x] Verzeichnis `docs/` ist angelegt.
- [x] Datei `docs/PLAN.md` ist angelegt und beinhaltet den abgestimmten Plan.
- [x] Grundstruktur fuer `frontend/`, `backend/`, `scripts/` ist dokumentiert (falls fehlend, angelegt).
- [x] Kurze lokale Setup-Notiz (Startvoraussetzungen, `.env`-Hinweis) ist vorhanden.

**Setup-Notiz (lokal):**
- Voraussetzungen: Aktuelles Node.js (fuer NextJS) und Python (fuer FastAPI) lokal installiert.
- Konfiguration: Root-`.env` muss `OPENROUTER_API_KEY` enthalten.
- Startpunkt: Skripte fuer den lokalen Start/Stopp werden in AP6 unter `scripts/` finalisiert.

**Strukturstatus (Basis):**
- `frontend/` (angelegt)
- `backend/` (vorhanden)
- `scripts/` (vorhanden)
- `docs/` (angelegt)

### AP2 - Backend-MVP (FastAPI + OpenRouter)
**Ziel:** API bereitstellen, die Bild + Prompt + Modell entgegennimmt und eine Beschreibung vom LLM liefert.

**Deliverables (Checkliste):**
- [x] FastAPI-App laeuft lokal stabil.
- [x] Endpoint fuer Bildanalyse ist implementiert (Input: Bild + System-Prompt + Modell).
- [x] OpenRouter-Integration nutzt `OPENROUTER_API_KEY` aus Root-`.env`.
- [x] Fehlerfaelle sind fuer MVP sinnvoll behandelt (z. B. kein API-Key, ungueltiges Bild, API-Fehler).
- [x] Antwortschema ist klar und vom Frontend direkt nutzbar.

### AP3 - Frontend-MVP (Upload, Prompt, Modell, Ausgabe)
**Ziel:** Benutzeroberflaeche liefert alle geforderten Interaktionen inkl. synchroner Aktualisierung.

**Deliverables (Checkliste):**
- [x] Bild-Upload/Anzeige funktioniert.
- [x] Prompt wird ueber Bild und Beschreibung angezeigt.
- [x] Prompt ist editierbar und per Button speicherbar.
- [x] Modell ist per Dropdown auswaehlbar.
- [x] LLM-Aufruf wird automatisch getriggert bei:
  - [x] neuem Bild
  - [x] gespeichertem Prompt
  - [x] geaenderter Modellauswahl
- [x] Ausgabe-Text wird rechts neben dem Bild angezeigt.
- [x] Bild und Beschreibung bleiben logisch synchron (neueste Eingabe -> neueste Ausgabe).

### AP4 - End-to-End-Integration und Zustandslogik
**Ziel:** Robustes Zusammenspiel von Frontend und Backend inklusive klarer Zustandslogik.

**Deliverables (Checkliste):**
- [x] API-Client im Frontend ist integriert und getestet.
- [x] Lade-/Fehlerzustaende sind sichtbar und verstaendlich.
- [x] Race-Conditions bei schnellen Aenderungen sind minimiert (nur letzter Request zaehlt).
- [x] Last-Write-Wins-Verhalten ist fuer die aktuelle Ausgabe stabil umgesetzt.

### AP5 - UI-Styling gemaess Farbkonzept
**Ziel:** Konsistentes Erscheinungsbild nach vorgegebenem Farbschema.

**Deliverables (Checkliste):**
- [x] Farben `#ecad0a`, `#209dd7`, `#753991`, `#032147`, `#888888` sind im UI sinnvoll verwendet.
- [x] Typische UI-Bereiche (Heading, CTA, Links, Begleittext) folgen der definierten Zuordnung.
- [x] Layout bleibt auch bei laengerer Modellantwort lesbar.

### AP6 - Skripte und lokaler Betrieb (Mac)
**Ziel:** Anwendung mit einfachen Skripten start-/stoppbar machen.

**Deliverables (Checkliste):**
- [x] Startskript in `scripts/` startet Backend und Frontend fuer lokale Nutzung.
- [x] Stoppskript in `scripts/` beendet die Prozesse zuverlaessig.
- [x] Kurzer Ablauf fuer lokale Inbetriebnahme ist dokumentiert.

### AP7 - Qualitaetssicherung und MVP-Abnahme
**Ziel:** Nachweis, dass alle Anforderungen aus `AGENTS.md` erfuellt sind.

**Deliverables (Checkliste):**
- [x] Manuelle Test-Checkliste pro Kernfunktion ist erstellt und abgearbeitet.
- [x] Positive Flows getestet (Upload, Prompt-Aenderung, Modellwechsel).
- [x] Relevante Fehlerfaelle getestet (fehlender Key, API-Fehler, ungueltige Datei).
- [x] Abgleich mit allen Business Requirements in `AGENTS.md` ist dokumentiert.

### AP8 - Persistenzschicht mit PostgreSQL
**Ziel:** LLM-Calls dauerhaft speichern und nach Backend-Neustart wieder verfuegbar machen.

**Deliverables (Checkliste):**
- [x] PostgreSQL ist als lokale Datenbank eingebunden und erreichbar.
- [x] Datenbankschema fuer LLM-Calls ist definiert (Bildmetadaten, Prompt, Modell, Antwort, Zeitstempel).
- [x] Jeder erfolgreiche Analyze-Call wird persistent gespeichert.
- [ ] Optional: Fehlerhafte Calls werden mit Status/Fallback nachvollziehbar abgelegt (falls vorgesehen).
- [x] Backend bietet einen Read-Endpoint fuer die Historie in absteigend chronologischer Reihenfolge.
**Statushinweis:** End-to-End verifiziert (Analyze speichern, History lesen, Persistenz nach Backend-Neustart).

### AP9 - Historienfunktion im Frontend
**Ziel:** Alle bisherigen LLM-Calls unterhalb des aktuellen Calls im selben Design darstellen (neueste oben).

**Deliverables (Checkliste):**
- [x] Frontend laedt die Historie beim Start und zeigt sie unterhalb des aktuellen Ergebnisses an.
- [x] Historienelemente nutzen dasselbe Grundlayout wie der aktuelle Call.
- [x] Sortierung ist korrekt: neueste Eintraege oben.
- [x] Nach neuem Analyze-Call wird die Historie sofort aktualisiert.
- [x] Historieneintraege enthalten mindestens Bildbezug, Prompt, Modell, Beschreibung und Zeitpunkt.

### AP10 - QA-Erweiterung fuer Persistenz und Historie
**Ziel:** Nachweis, dass Persistenz und Historienanzeige stabil funktionieren.

**Deliverables (Checkliste):**
- [x] Testfall: Analyze-Call erzeugen, Backend neustarten, Historie weiterhin vorhanden.
- [x] Testfall: Mehrere Calls, Reihenfolge in UI korrekt (neueste oben).
- [x] Testfall: Historie und aktueller Call visuell konsistent.
- [x] Testfall: API/DB-Fehlerpfade fuer Historienladevorgang dokumentiert.
- [x] QA-Report in `docs/QA_REPORT.md` um die neuen Anforderungen erweitert.

## Umsetzungsreihenfolge
1. AP1 Projektgrundlage
2. AP2 Backend-MVP
3. AP3 Frontend-MVP
4. AP4 Integration/Zustandslogik
5. AP5 Styling
6. AP6 Skripte
7. AP7 QA und Abnahme
8. AP8 Persistenz mit PostgreSQL
9. AP9 Historie im Frontend
10. AP10 QA-Erweiterung

## Architektur-Uebersicht (MVP)
```mermaid
flowchart LR
    user[User] --> frontend[NextJSFrontend]
    frontend -->|Bild Prompt Modell| backend[FastAPIBackend]
    backend -->|Request| openrouter[OpenRouterAPI]
    openrouter -->|Beschreibung| backend
    backend -->|WriteCall| postgres[PostgreSQL]
    postgres -->|ReadHistory| backend
    backend -->|AktuelleAntwort+Historie| frontend
    frontend --> view[BildBeschreibungHistorieSynchron]
```

## Abnahmekriterien (kompakt)
- Alle in `AGENTS.md` genannten Funktionen sind vorhanden und nachvollziehbar testbar.
- Lokaler Betrieb funktioniert ohne Docker.
- LLM-Calls sind persistent gespeichert und nach Backend-Neustart wieder abrufbar.
