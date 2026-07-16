# PLAN.md - ArchitekturBild MVP

## Ziel
Den in `AGENTS.md` definierten Scope als lokal lauffaehige Anwendung liefern, bei der Bild, Prompt, Modellauswahl und LLM-Beschreibung synchron sind, alle LLM-Calls historisiert werden, Metadaten in PostgreSQL persistent gespeichert sind und Bilder in MinIO gespeichert/ueber Presigned URLs ausgeliefert werden. Zusaetzlich werden zwei manuell gestartete Suchen geliefert: eine Fuzzy-Suche (case-insensitive, trigram-basiert, Relevanzsortierung, leere Suche zeigt alle Eintraege) und eine Vektor-Suche mit Backend-RAG auf PostgreSQL mit pgvector (semantische Relevanzsortierung, leere Suche zeigt alle Eintraege).

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
- [x] AP11 - MinIO-Integration im Backend
- [x] AP12 - History-API mit Presigned URLs
- [x] AP13 - Historienlayout Bild links, Text rechts
- [x] AP14 - QA-Erweiterung fuer MinIO und Layout
- [ ] AP15 - Such-UI (Eingabefeld + suchen-Button + Triggerlogik)
- [ ] AP16 - Relevanzsuche und Ergebnisfilterung
- [ ] AP17 - QA-Erweiterung fuer Suche
- [ ] AP18 - UI-Erweiterung: Vektor-Suche neben Fuzzy-Suche
- [ ] AP19 - Backend-RAG mit PostgreSQL pgvector
- [ ] AP20 - API-Integration fuer Vektor-Suche
- [ ] AP21 - QA-Erweiterung fuer Fuzzy + Vektor-Suche

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

### AP11 - MinIO-Integration im Backend
**Ziel:** Jedes neu hochgeladene Bild wird bei erfolgreichem Analyze-Flow in MinIO gespeichert.

**Deliverables (Checkliste):**
- [x] MinIO-Client im Backend integriert (Konfiguration ueber `.env`).
- [x] Upload-Logik in `/api/analyze` mit deterministischem Objekt-Key umgesetzt.
- [x] Fehlerbehandlung: MinIO-Upload-Fehler fuehren zu klarer API-Fehlermeldung.
- [x] Start-/Run-Doku um MinIO-Env-Variablen erweitert.

### AP12 - History-API mit Presigned URLs
**Ziel:** Historieneintraege liefern pro Bild eine Presigned URL.

**Deliverables (Checkliste):**
- [x] DB-Schema erweitert um `storage_bucket` und `storage_object_key`.
- [x] Persistenz schreibt Objektreferenzen je Call in PostgreSQL.
- [x] `/api/history` liefert `image_url` per Presigned URL.
- [x] Backward-Compatibility fuer alte Datensaetze ohne Objekt-Key umgesetzt (Fallback auf kein Bild).

### AP13 - Historienlayout Bild links, Text rechts
**Ziel:** Historienzeilen zeigen links Bild und rechts Modell, Dateiname, Prompt, Beschreibung.

**Deliverables (Checkliste):**
- [x] 2-Spalten-Layout pro Historieneintrag umgesetzt.
- [x] Textblock enthaelt Modell, Dateiname, Prompt, Beschreibung.
- [x] Fallback bei fehlender/abgelaufener URL umgesetzt.
- [x] Responsives Verhalten fuer kleine Screens umgesetzt.

### AP14 - QA-Erweiterung fuer MinIO und Layout
**Ziel:** Nachweis, dass Storage, URL-Erzeugung und UI-Layout stabil funktionieren.

**Deliverables (Checkliste):**
- [x] Test: Analyze erzeugt DB-Eintrag + MinIO-Objekt.
- [x] Test: `/api/history` liefert gueltige Presigned URL.
- [x] Test: Historie zeigt links Bild, rechts Modell/Dateiname/Prompt/Beschreibung.
- [x] Test: Nach Backend-Neustart bleiben Eintraege sichtbar; URLs werden neu signiert.
- [x] Fehlerfall-Test: MinIO nicht erreichbar -> klare Backend-Fehlermeldung.
- [x] `docs/QA_REPORT.md` um MinIO-/Layout-Tests erweitert.

### AP15 - Such-UI (Eingabefeld + suchen-Button + Triggerlogik)
**Ziel:** Eine klar sichtbare Suchbedienung im oberen Suchbereich bereitstellen, die Suche nur manuell ausloest.

**Deliverables (Checkliste):**
- [ ] Suchfelder im oberen Suchbereich, zweizeilig und deutlich breiter als hoch.
- [ ] Button `suchen` direkt neben dem Suchfeld.
- [ ] Suche startet ausschliesslich per Button-Klick.
- [ ] Leerer Suchstring zeigt alle Eintraege.

### AP16 - Relevanzsuche und Ergebnisfilterung
**Ziel:** Relevante Treffer ueber aktuelle Ausgabe und Historie robust finden und sortieren.

**Deliverables (Checkliste):**
- [ ] Suchscope deckt `model`, `filename`, `prompt`, `description` fuer aktuellen Call und Historie ab.
- [ ] Case-insensitive Normalisierung ist umgesetzt.
- [ ] Trigram-basierter Fuzzy-Score pro Eintrag ist umgesetzt.
- [ ] Treffer werden nach Relevanz absteigend sortiert.
- [ ] Mindestschwelle fuer nicht-abwegige Relevanz ist definiert und angewandt.

### AP17 - QA-Erweiterung fuer Suche
**Ziel:** Nachweis, dass Such-Trigger, Matching und Sortierung stabil funktionieren.

**Deliverables (Checkliste):**
- [ ] Test: Exakter Treffer wird gefunden und korrekt sortiert.
- [ ] Test: Gross-/Kleinschreibung beeinflusst Ergebnis nicht.
- [ ] Test: Aehnlicher Begriff liefert fuzzy Treffer.
- [ ] Test: Leere Suche zeigt alle Eintraege.
- [ ] Test: Suche startet nur mit Button-Klick.

### AP18 - UI-Erweiterung: Vektor-Suche neben Fuzzy-Suche
**Ziel:** Eine zweite Suchbedienung fuer semantische Suche links neben der Fuzzy-Suche bereitstellen.

**Deliverables (Checkliste):**
- [ ] Neues Feld `Vektor-Suche` links vom bestehenden Suchfeld umgesetzt.
- [ ] Bestehendes Feld klar als `Fuzzy-Suche` beschriftet.
- [ ] Eigener `suchen`-Button je Suchfeld umgesetzt.
- [ ] Beide Suchmodi werden ausschliesslich per jeweiligem Button getriggert.

### AP19 - Backend-RAG mit PostgreSQL pgvector
**Ziel:** Semantische Suche ueber persistierte LLM-Calls serverseitig bereitstellen.

**Deliverables (Checkliste):**
- [ ] PostgreSQL um `pgvector` erweitert und Schema um Embedding-Spalte aktualisiert.
- [ ] Embedding-Erzeugung ueber OpenRouter im Backend integriert.
- [ ] Embeddings werden fuer neue LLM-Calls beim Persistieren gespeichert.
- [ ] Backfill-Strategie fuer bestehende LLM-Calls definiert und umgesetzt.
- [ ] Vektor-Aehnlichkeitssuche mit Relevanzscore serverseitig verfuegbar.

### AP20 - API-Integration fuer Vektor-Suche
**Ziel:** Vektor-Suche ueber API an das Frontend anbinden, ohne das Ergebnislayout zu brechen.

**Deliverables (Checkliste):**
- [ ] API-Parameter oder Endpoint fuer Vektor-Suchquery ergaenzt.
- [ ] Leere Vektor-Query liefert alle Eintraege.
- [ ] Ergebnisformat bleibt kompatibel zur bestehenden Ergebnisliste.
- [ ] Fehlerpfade fuer Embedding-/DB-Ausfaelle liefern klare Fehlermeldungen.

### AP21 - QA-Erweiterung fuer Fuzzy + Vektor-Suche
**Ziel:** Nachweis, dass beide Suchmodi stabil und nachvollziehbar funktionieren.

**Deliverables (Checkliste):**
- [ ] Test: Fuzzy-Suche arbeitet weiterhin korrekt.
- [ ] Test: Vektor-Suche findet semantisch aehnliche Eintraege.
- [ ] Test: Vektor-Treffer sind nach semantischer Relevanz sortiert.
- [ ] Test: Leere Vektor-Query zeigt alle Eintraege.
- [ ] Test: Persistenz/Neustart beeintraechtigt Vektor-Suche nicht.

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
11. AP11 MinIO-Integration
12. AP12 Presigned URLs
13. AP13 Historienlayout
14. AP14 QA MinIO/Layout
15. AP15 Such-UI
16. AP16 Relevanzsuche
17. AP17 QA Suche
18. AP18 UI Vektor-Suche
19. AP19 Backend-RAG pgvector
20. AP20 API Vektor-Suche
21. AP21 QA Fuzzy+Vektor

## Architektur-Uebersicht (MVP)
```mermaid
flowchart LR
    user[User] --> frontend[NextJSFrontend]
    frontend -->|Bild Prompt Modell| backend[FastAPIBackend]
    backend -->|Request| openrouter[OpenRouterAPI]
    openrouter -->|Beschreibung| backend
    backend -->|StoreImage| minio[MinIO]
    backend -->|WriteCall| postgres[PostgreSQL]
    postgres -->|ReadHistory| backend
    minio -->|PresignedURL| backend
    backend -->|AktuelleAntwort+Historie+BildURL| frontend
    frontend --> view[BildBeschreibungHistorieSynchron]
```

## Abnahmekriterien (kompakt)
- Alle in `AGENTS.md` genannten Funktionen sind vorhanden und nachvollziehbar testbar.
- Lokaler Betrieb funktioniert; optionale Docker-Nutzung fuer MinIO wird unterstuetzt.
- LLM-Calls sind persistent gespeichert und nach Backend-Neustart wieder abrufbar.
- Alle neuen Bild-Uploads werden in MinIO gespeichert und in der Historie nach Neustart sichtbar angezeigt.
- Fuzzy-Suche und Vektor-Suche sind im oberen Suchbereich vorhanden, jeweils per Button triggerbar, und liefern relevante Treffer in sortierter Reihenfolge.
- Vektor-Suche laeuft ueber Backend-RAG mit PostgreSQL und `pgvector` und durchsucht semantisch die persistierten LLM-Calls.
