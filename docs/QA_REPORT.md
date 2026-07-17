# QA Report - ArchitekturBild MVP

## Scope
Verifikation der MVP-Anforderungen aus `AGENTS.md` fuer:
- Positive Flows (Bild, Prompt, Modell)
- Relevante Fehlerfaelle
- Persistenz und Historienfunktion
- MinIO-Storage und Presigned-URL-Auslieferung
- Historienlayout mit Bild links / Text rechts
- Abgleich der Business Requirements

## Testbasis
- Containerisierter Start/Stop ueber `scripts/start_mac.sh` und `scripts/stop_mac.sh` (`docker compose`)
- Backend-API unter `http://localhost:8000`
- Frontend unter `http://localhost:3000`
- Persistente Daten in Docker Volumes `postgres_data` und `minio_data`

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

### Persistenz und Historie
- [x] Historie ist via `GET /api/history` abrufbar.
- [x] Mehrere Calls werden in korrekter Reihenfolge geliefert (neueste oben).
- [x] Historie bleibt nach Backend-Neustart erhalten.
- [x] Frontend ist erreichbar und zeigt Historien-UI unterhalb des aktuellen Calls.
- [x] DB-Fehlerpfad fuer Historienladen ist dokumentiert (Startup-Fehler bei ungueltiger `DATABASE_URL`).

### MinIO und Presigned URLs
- [x] Analyze speichert Bildobjekte in MinIO und persistiert Bucket/Object-Key in PostgreSQL.
- [x] History liefert pro Eintrag eine Presigned `image_url`.
- [x] Presigned URL ist fuer Abruf gueltig (HTTP 200 auf Objekt-URL).
- [x] Presigned URL wird nach Backend-Neustart neu signiert.
- [x] MinIO-Fehlerpfad ist dokumentiert (Startup-Fehler bei unerreichbarem MinIO-Endpunkt).

### Historienlayout
- [x] Historieneintrag zeigt links Bild, rechts Textblock.
- [x] Textblock enthaelt Modell, Dateiname, Prompt und Beschreibung.
- [x] Fallback bei fehlender URL ist vorhanden (`Kein Bild verfuegbar`).
- [x] Responsiv unter kleiner Breite: Bild/Text untereinander.

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

6. **Persistenz + Reihenfolge**
   - Baseline-Historie gelesen (`GET /api/history?limit=1`).
   - Zwei neue Analyze-Calls erzeugt:
     - Call 1: Prompt `AP10 Prompt Eins`, Modell `openai/gpt-4.1-mini`
     - Call 2: Prompt `AP10 Prompt Zwei`, Modell `openai/gpt-4o-mini`
   - Verifikation: `GET /api/history?limit=3` liefert `AP10 Prompt Zwei` vor `AP10 Prompt Eins` (neueste oben).

7. **Persistenz ueber Neustart**
   - Backend gestoppt und neu gestartet.
   - Verifikation: `GET /api/history?limit=3` enthaelt die zuvor erzeugten AP10-Eintraege weiterhin.

8. **Frontend-Erreichbarkeit fuer Historien-UI**
   - `GET http://localhost:3000` => HTTP 200
   - `GET http://localhost:8000/health` => HTTP 200
   - Historien-Rendering ist im Frontend unterhalb des aktuellen Calls implementiert (`frontend/app/page.js`, Sektion `Fruehere LLM-Calls`) und nutzt dieselben Panel-Klassen (`panel`, `historyItem`) wie der aktuelle Call.

9. **DB-Fehlerpfad Historienladen**
   - Backend mit absichtlich ungueltiger `DATABASE_URL` auf separatem Port gestartet.
   - Ergebnis: Startup bricht mit
     - `RuntimeError: PostgreSQL connection failed. Check DATABASE_URL and database availability.`
     - `ERROR: Application startup failed. Exiting.`
   - Damit ist der API/DB-Fehlerpfad fuer Historienzugriff dokumentiert.

10. **MinIO Storage + Presigned URL**
   - Lokale MinIO-Instanz via Docker gestartet (`minio/minio`, Port 9000/9001).
   - Analyze-Request mit Testbild (`.run/minio_test.jpg`) erfolgreich (`HTTP 200`).
   - `GET /api/history?limit=1` liefert:
     - `storage_bucket=architekturbild-images`
     - `storage_object_key=images/...`
     - `image_url` vorhanden
   - Abruf der `image_url` liefert `HTTP 200` (Objekt direkt aus MinIO via Presigned URL).

11. **Presigned URL nach Restart**
   - Backend auf Testport neu gestartet.
   - Historie erneut gelesen.
   - Vergleich: Presigned URL vor/nach Neustart unterschiedlich (`url_regenerated=true`), Datensatz bleibt erhalten.

12. **MinIO-Fehlerpfad**
   - Backend mit absichtlich unerreichbarem MinIO-Endpunkt (`127.0.0.1:6555`) gestartet.
   - Ergebnis: klarer Startup-Fehler
     - `RuntimeError: MinIO configuration/startup failed: Failed to initialize MinIO: ...`
     - `ERROR: Application startup failed. Exiting.`

13. **MinIO-Volume-Persistenz (Container-Neuerstellung)**
   - Stack gestartet, neuer Analyze-Call erzeugt (`HTTP 200`), `storage_object_key` notiert.
   - Stack gestoppt, MinIO-Container explizit entfernt, anschließend per Script neu erstellt.
   - Verifikation:
     - `storage_object_key` nach Neustart unverändert im neuesten History-Eintrag.
     - `image_url` weiterhin vorhanden.
     - Objektabruf per Presigned URL weiterhin erfolgreich (`HTTP 200`).

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

- [x] Fruehere LLM-Calls werden unterhalb des aktuellen Calls gelistet (neueste oben)  
  Verifiziert durch Historien-Endpoint `GET /api/history` und Frontend-Rendering in `frontend/app/page.js`.

- [x] LLM-Calls werden in Datenbank gespeichert (PostgreSQL)  
  Verifiziert durch persistente History-Eintraege nach erfolgreichen Analyze-Calls.

- [x] Calls sind nach Backend-Neustart weiterhin abrufbar  
  Verifiziert durch Neustart-Test mit unveraenderter Historie.

- [x] Bilder der Calls werden in MinIO gespeichert  
  Verifiziert durch `storage_bucket`/`storage_object_key` in Historie und erfolgreichen Objektabruf via Presigned URL.

- [x] Zukuenftige Bilder bleiben auch nach MinIO-Container-Neuerstellung sichtbar  
  Verifiziert durch named Docker volume (`MINIO_DOCKER_VOLUME_NAME`) und erfolgreichen Abruf desselben Objekts nach Container-Recreate.

- [x] Historie zeigt pro Call links das Bild und rechts Modell, Dateiname, Prompt, Beschreibung  
  Verifiziert durch Frontend-Implementierung in `frontend/app/page.js` und zugehoeriges Styling in `frontend/app/globals.css`.

## Limitations Check
- [x] Lokaler Betrieb via Docker Compose (MVP-konform)
- [x] Persistenz ist fuer PostgreSQL und MinIO ueber Docker Volumes umgesetzt.

## Container-QA (AP27)
- [x] Komplettstart des Stacks mit `docker compose up -d --build` erfolgreich.
- [x] Healthchecks fuer `postgres`, `minio`, `backend` und `frontend` erfolgreich.
- [x] Persistenztest PostgreSQL: Marker-Datensatz bleibt nach `down`/`up` erhalten.
- [x] Persistenztest MinIO: Marker-Objekt bleibt nach `down`/`up` erhalten.
- [x] API-Smoke-Test fuer Historie inkl. `vector_query` liefert HTTP 200.
