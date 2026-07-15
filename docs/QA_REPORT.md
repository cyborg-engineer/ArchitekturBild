# QA Report - ArchitekturBild MVP

## Scope
Verifikation der MVP-Anforderungen aus `AGENTS.md` fuer:
- Positive Flows (Bild, Prompt, Modell)
- Relevante Fehlerfaelle
- Abgleich der Business Requirements

## Testbasis
- Lokaler Start/Stop ueber `scripts/start_mac.sh` und `scripts/stop_mac.sh`
- Backend-API unter `http://localhost:8000`
- Frontend unter `http://localhost:3000`
- Testartefakte in `.run/`

## Testcheckliste (ausgefuehrt)

### Positive Flows
- [x] Frontend erreichbar (`GET /` => HTTP 200)
- [x] Backend Health erreichbar (`GET /health` => `{\"status\":\"ok\"}`)
- [x] Bild-Upload/Analyse erfolgreich (`POST /api/analyze` mit JPEG => HTTP 200, Beschreibung vorhanden)
- [x] Prompt-Aenderung erfolgreich (`POST /api/analyze` mit geaendertem Prompt => HTTP 200)
- [x] Modellwechsel erfolgreich (`POST /api/analyze` mit anderem Modell => HTTP 200)

### Fehlerfaelle
- [x] Ungueltiger Dateityp (`text/plain`) liefert HTTP 400 mit `Uploaded file must be an image`
- [x] Fehlender API-Key liefert HTTP 500 mit `OPENROUTER_API_KEY is missing in root .env`
- [x] Upstream-LLM-Fehler wird als HTTP 502 durchgereicht (OpenRouter Provider-Fehler reproduziert)

## Ausgefuehrte Tests (Evidence)

1. **Health + Erreichbarkeit**
   - `GET http://localhost:8000/health` => 200
   - `GET http://localhost:3000` => 200

2. **Analyse mit gueltigem Bild**
   - Generiertes Testbild: `.run/qa_valid.jpg`
   - Request: `POST /api/analyze` mit Modell `openai/gpt-4.1-mini`
   - Ergebnis: HTTP 200, `description` nicht leer, `model` korrekt im Response

3. **Prompt-Aenderung**
   - Zwei Requests mit gleichem Bild/Modell, unterschiedlichem Prompt
   - Ergebnis: beide Requests HTTP 200 mit Beschreibung

4. **Modellwechsel**
   - Request mit Modell `openai/gpt-4o-mini`
   - Ergebnis: HTTP 200, `model` im Response entspricht neuer Auswahl

5. **Negativtests**
   - Datei ohne Bildtyp -> HTTP 400
   - Lauf ohne API-Key -> HTTP 500
   - Provider-seitige Bildvalidierung (synthetischer Minimal-PNG-Fall) -> HTTP 502

## Requirement Mapping gegen `AGENTS.md`

- [x] Bild wird geladen/angezeigt  
  Verifiziert durch Frontend-Implementierung in `frontend/app/page.js` (Upload + Preview) und erfolgreichen Analysefluss mit Testbild.

- [x] Externes LLM wird zur Bildbeschreibung aufgerufen  
  Verifiziert durch erfolgreiche `POST /api/analyze`-Antworten (HTTP 200, Beschreibung vorhanden).

- [x] LLM-Ausgabe wird rechts neben dem Bild angezeigt  
  Verifiziert durch Frontend-Struktur in `frontend/app/page.js` (zweispaltige Ausgabe, Panel Bild/Beschreibung).

- [x] System Prompt ueber Bild/Beschreibung sichtbar und editierbar  
  Verifiziert durch Prompt-Block inkl. Textarea + Save-Button in `frontend/app/page.js`.

- [x] Modell ueber Dropdown waehlbar  
  Verifiziert durch `select` + erfolgreiche Modellwechsel-Analyse (HTTP 200).

- [x] Automatischer Trigger bei Bild-Upload, Prompt-Save, Modellwechsel  
  Verifiziert durch Event-Handler in `frontend/app/page.js` und erfolgreiche API-Aufrufe fuer alle drei Faelle.

- [x] Synchronitaet Bild/Beschreibung (Latest Request wins)  
  Verifiziert durch AP4-Logik mit `AbortController` und Request-ID-Guard in `frontend/app/page.js`.

## Limitations Check
- [x] Keine Persistenz implementiert (MVP-konform)
- [x] Lokaler Betrieb ohne Docker (MVP-konform)
