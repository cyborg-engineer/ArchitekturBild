"use client";

import { useEffect, useMemo, useRef, useState } from "react";

import { analyzeImage, fetchHistory } from "../lib/analyzeClient";

const DEFAULT_PROMPT =
  "Du bist ein Architektur-Assistent. Beschreibe das Bild praezise, strukturiert und ohne Spekulation.";

const DEFAULT_MODEL = "openai/gpt-4.1-mini";
const MODEL_OPTIONS = [
  "openai/gpt-4.1-mini",
  "openai/gpt-4o-mini",
  "openai/gpt-4.1"
];

export default function HomePage() {
  const [selectedModel, setSelectedModel] = useState(DEFAULT_MODEL);
  const [draftPrompt, setDraftPrompt] = useState(DEFAULT_PROMPT);
  const [savedPrompt, setSavedPrompt] = useState(DEFAULT_PROMPT);
  const [imageFile, setImageFile] = useState(null);
  const [imagePreviewUrl, setImagePreviewUrl] = useState("");
  const [description, setDescription] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");
  const [activeSource, setActiveSource] = useState("");
  const [historyItems, setHistoryItems] = useState([]);
  const [historyError, setHistoryError] = useState("");
  const latestRequestIdRef = useRef(0);
  const activeControllerRef = useRef(null);
  const historyControllerRef = useRef(null);

  const hasImage = Boolean(imageFile);
  const promptHasChanges = draftPrompt !== savedPrompt;

  const headlineStatus = useMemo(() => {
    if (isLoading) return "Analysiere Bild...";
    if (errorMessage) return "Analyse fehlgeschlagen";
    if (!hasImage) return "Bitte ein Bild hochladen";
    if (!description) return "Warte auf Analyse";
    return "Analyse aktuell";
  }, [description, errorMessage, hasImage, isLoading]);

  const visibleHistoryItems = useMemo(() => {
    if (!historyItems.length) return [];
    if (!description) return historyItems;

    const first = historyItems[0];
    const matchesCurrent =
      first?.description === description &&
      first?.model === selectedModel &&
      first?.system_prompt === savedPrompt;

    if (matchesCurrent) {
      return historyItems.slice(1);
    }

    return historyItems;
  }, [description, historyItems, savedPrompt, selectedModel]);

  useEffect(() => {
    return () => {
      if (activeControllerRef.current) {
        activeControllerRef.current.abort();
      }
      if (historyControllerRef.current) {
        historyControllerRef.current.abort();
      }
    };
  }, []);

  useEffect(() => {
    return () => {
      if (imagePreviewUrl) {
        URL.revokeObjectURL(imagePreviewUrl);
      }
    };
  }, [imagePreviewUrl]);

  useEffect(() => {
    void loadHistory();
  }, []);

  async function loadHistory() {
    if (historyControllerRef.current) {
      historyControllerRef.current.abort();
    }

    const controller = new AbortController();
    historyControllerRef.current = controller;
    setHistoryError("");

    try {
      const items = await fetchHistory({ limit: 20, signal: controller.signal });
      setHistoryItems(items);
    } catch (error) {
      if (error?.name === "AbortError") {
        return;
      }
      setHistoryError(error.message || "Historie konnte nicht geladen werden.");
    }
  }

  async function analyze(fileArg, promptArg, modelArg, sourceLabel) {
    if (!fileArg) {
      setDescription("");
      setErrorMessage("");
      setIsLoading(false);
      setActiveSource("");
      return;
    }

    if (activeControllerRef.current) {
      activeControllerRef.current.abort();
    }

    const controller = new AbortController();
    activeControllerRef.current = controller;
    const requestId = latestRequestIdRef.current + 1;
    latestRequestIdRef.current = requestId;

    setIsLoading(true);
    setErrorMessage("");
    setActiveSource(sourceLabel);

    try {
      const payload = await analyzeImage({
        file: fileArg,
        systemPrompt: promptArg,
        model: modelArg,
        signal: controller.signal
      });
      if (requestId !== latestRequestIdRef.current) {
        return;
      }
      setDescription(payload.description || "");
      await loadHistory();
    } catch (error) {
      if (error?.name === "AbortError") {
        return;
      }
      if (requestId !== latestRequestIdRef.current) {
        return;
      }
      setDescription("");
      setErrorMessage(error.message || "Analyse konnte nicht geladen werden.");
    } finally {
      if (requestId === latestRequestIdRef.current) {
        setIsLoading(false);
      }
    }
  }

  async function handleImageUpload(event) {
    const nextFile = event.target.files?.[0];
    if (!nextFile) return;

    setImageFile(nextFile);
    setImagePreviewUrl(URL.createObjectURL(nextFile));
    await analyze(nextFile, savedPrompt, selectedModel, "bild");
  }

  async function handleSavePrompt() {
    setSavedPrompt(draftPrompt);
    await analyze(imageFile, draftPrompt, selectedModel, "prompt");
  }

  async function handleModelChange(event) {
    const nextModel = event.target.value;
    setSelectedModel(nextModel);
    await analyze(imageFile, savedPrompt, nextModel, "modell");
  }

  return (
    <main className="page">
      <h1>ArchitekturBild MVP</h1>

      <section className="controls">
        <label className="control">
          <span>Bild hochladen</span>
          <input type="file" accept="image/*" onChange={handleImageUpload} />
        </label>

        <label className="control">
          <span>Modell</span>
          <select value={selectedModel} onChange={handleModelChange}>
            {MODEL_OPTIONS.map((model) => (
              <option key={model} value={model}>
                {model}
              </option>
            ))}
          </select>
        </label>
      </section>

      <section className="promptBlock">
        <label htmlFor="promptInput">System Prompt</label>
        <textarea
          id="promptInput"
          value={draftPrompt}
          onChange={(event) => setDraftPrompt(event.target.value)}
          rows={4}
        />
        <button type="button" onClick={handleSavePrompt} disabled={!promptHasChanges}>
          Prompt speichern
        </button>
      </section>

      <p className="status">
        {headlineStatus}
        {isLoading && activeSource ? ` (Quelle: ${activeSource})` : ""}
      </p>
      {errorMessage ? <p className="error">{errorMessage}</p> : null}

      <section className="content">
        <article className="panel">
          <h2>Bild</h2>
          {imagePreviewUrl ? (
            <img src={imagePreviewUrl} alt="Hochgeladenes Architekturmotiv" className="previewImage" />
          ) : (
            <p className="muted">Kein Bild geladen.</p>
          )}
        </article>

        <article className="panel">
          <h2>Beschreibung</h2>
          {isLoading ? (
            <p className="muted">Analyse laeuft...</p>
          ) : (
            <p>{description || <span className="muted">Noch keine Beschreibung vorhanden.</span>}</p>
          )}
        </article>
      </section>

      <section className="historySection">
        <h2>Fruehere LLM-Calls</h2>
        {historyError ? <p className="error">{historyError}</p> : null}
        {!visibleHistoryItems.length ? (
          <p className="muted">Noch keine frueheren Calls vorhanden.</p>
        ) : (
          <div className="historyList">
            {visibleHistoryItems.map((item) => (
              <article key={item.id} className="panel historyItem">
                <div className="historyItemLayout">
                  <div className="historyImagePane">
                    {item.image_url ? (
                      <img
                        src={item.image_url}
                        alt={item.image_filename || "Historienbild"}
                        className="historyImage"
                      />
                    ) : (
                      <div className="historyImageFallback">Kein Bild verfuegbar</div>
                    )}
                  </div>

                  <div className="historyTextPane">
                    <p>
                      <strong>Modell:</strong> {item.model || "Unbekanntes Modell"}
                    </p>
                    <p>
                      <strong>Dateiname:</strong> {item.image_filename || "ohne Dateiname"}
                    </p>
                    <p>
                      <strong>Prompt:</strong> {item.system_prompt || "-"}
                    </p>
                    <p>
                      <strong>Beschreibung:</strong> {item.description || "-"}
                    </p>
                    <p className="metaLine">
                      {item.created_at ? new Date(item.created_at).toLocaleString("de-DE") : "Ohne Zeitstempel"}
                    </p>
                  </div>
                </div>
              </article>
            ))}
          </div>
        )}
      </section>
    </main>
  );
}
