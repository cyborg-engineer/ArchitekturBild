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
const SEARCH_RELEVANCE_THRESHOLD = 0.18;

function normalizeText(value) {
  return String(value || "").toLowerCase().trim();
}

function buildTrigrams(value) {
  const normalized = `  ${normalizeText(value).replace(/\s+/g, " ")}  `;
  if (normalized.length < 3) return [];
  const trigrams = [];
  for (let index = 0; index <= normalized.length - 3; index += 1) {
    trigrams.push(normalized.slice(index, index + 3));
  }
  return trigrams;
}

function trigramSimilarity(left, right) {
  const leftTrigrams = buildTrigrams(left);
  const rightTrigrams = buildTrigrams(right);
  if (!leftTrigrams.length || !rightTrigrams.length) return 0;

  const rightSet = new Set(rightTrigrams);
  let intersectionCount = 0;
  for (const trigram of leftTrigrams) {
    if (rightSet.has(trigram)) intersectionCount += 1;
  }

  const denominator = Math.max(leftTrigrams.length, rightTrigrams.length);
  return denominator ? intersectionCount / denominator : 0;
}

function computeRelevance(itemText, queryText) {
  const query = normalizeText(queryText);
  const text = normalizeText(itemText);
  if (!query) return 1;
  if (!text) return 0;

  const exactIncludesBoost = text.includes(query) ? 0.45 : 0;
  const tokenMatches = query
    .split(/\s+/)
    .filter(Boolean)
    .reduce((accumulator, token) => (text.includes(token) ? accumulator + 1 : accumulator), 0);
  const tokenBoost = Math.min(0.35, tokenMatches * 0.12);
  const trigramScore = trigramSimilarity(text, query);

  return Math.min(1, trigramScore + exactIncludesBoost + tokenBoost);
}

export default function HomePage() {
  const [selectedModel, setSelectedModel] = useState(DEFAULT_MODEL);
  const [draftPrompt, setDraftPrompt] = useState(DEFAULT_PROMPT);
  const [savedPrompt, setSavedPrompt] = useState(DEFAULT_PROMPT);
  const [imageFile, setImageFile] = useState(null);
  const [imagePreviewUrl, setImagePreviewUrl] = useState("");
  const [description, setDescription] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");
  const [errorDetail, setErrorDetail] = useState(null);
  const [activeSource, setActiveSource] = useState("");
  const [historyItems, setHistoryItems] = useState([]);
  const [historyError, setHistoryError] = useState("");
  const [fuzzySearchInput, setFuzzySearchInput] = useState("");
  const [appliedFuzzyQuery, setAppliedFuzzyQuery] = useState("");
  const [vectorSearchInput, setVectorSearchInput] = useState("");
  const [appliedVectorQuery, setAppliedVectorQuery] = useState("");
  const [vectorItems, setVectorItems] = useState([]);
  const [vectorError, setVectorError] = useState("");
  const [isVectorLoading, setIsVectorLoading] = useState(false);
  const [activeSearchMode, setActiveSearchMode] = useState("fuzzy");
  const latestRequestIdRef = useRef(0);
  const activeControllerRef = useRef(null);
  const historyControllerRef = useRef(null);
  const vectorControllerRef = useRef(null);

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

  const currentCallItem = useMemo(() => {
    const hasCurrentContent = Boolean(imagePreviewUrl || description || imageFile?.name);
    if (!hasCurrentContent) return null;

    return {
      id: "current-call",
      source_type: "current",
      model: selectedModel || "",
      image_filename: imageFile?.name || "",
      system_prompt: savedPrompt || "",
      description: description || "",
      image_url: imagePreviewUrl || "",
      created_at: null
    };
  }, [description, imageFile, imagePreviewUrl, savedPrompt, selectedModel]);

  const searchableItems = useMemo(() => {
    const current = currentCallItem ? [currentCallItem] : [];
    return [...current, ...visibleHistoryItems.map((item) => ({ ...item, source_type: "history" }))];
  }, [currentCallItem, visibleHistoryItems]);

  const fuzzyFilteredItems = useMemo(() => {
    const query = normalizeText(appliedFuzzyQuery);
    if (!query) return searchableItems;

    return searchableItems
      .map((item) => {
        const combinedText = [
          item.model,
          item.image_filename,
          item.system_prompt,
          item.description
        ]
          .filter(Boolean)
          .join(" \n ");

        const relevance = computeRelevance(combinedText, query);
        return { item, relevance };
      })
      .filter((entry) => entry.relevance >= SEARCH_RELEVANCE_THRESHOLD)
      .sort((left, right) => right.relevance - left.relevance)
      .map((entry) => entry.item);
  }, [appliedFuzzyQuery, searchableItems]);

  const vectorResultItems = useMemo(
    () => vectorItems.map((item) => ({ ...item, source_type: "history" })),
    [vectorItems]
  );

  const displayedItems = activeSearchMode === "vector" ? vectorResultItems : fuzzyFilteredItems;

  useEffect(() => {
    return () => {
      if (activeControllerRef.current) {
        activeControllerRef.current.abort();
      }
      if (historyControllerRef.current) {
        historyControllerRef.current.abort();
      }
      if (vectorControllerRef.current) {
        vectorControllerRef.current.abort();
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

  async function loadVectorSearch(queryText) {
    if (vectorControllerRef.current) {
      vectorControllerRef.current.abort();
    }

    const controller = new AbortController();
    vectorControllerRef.current = controller;
    setVectorError("");
    setIsVectorLoading(true);

    try {
      const items = await fetchHistory({
        limit: 20,
        signal: controller.signal,
        vectorQuery: queryText
      });
      setVectorItems(items);
    } catch (error) {
      if (error?.name === "AbortError") {
        return;
      }
      setVectorItems([]);
      setVectorError(error.message || "Vektor-Suche konnte nicht geladen werden.");
    } finally {
      setIsVectorLoading(false);
    }
  }

  async function analyze(fileArg, promptArg, modelArg, sourceLabel) {
    if (!fileArg) {
      setDescription("");
      setErrorMessage("");
      setErrorDetail(null);
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
    setErrorDetail(null);
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
      setErrorDetail(null);
      await loadHistory();
      if (activeSearchMode === "vector") {
        await loadVectorSearch(appliedVectorQuery);
      }
    } catch (error) {
      if (error?.name === "AbortError") {
        return;
      }
      if (requestId !== latestRequestIdRef.current) {
        return;
      }
      setDescription("");
      const detail = error?.detail && typeof error.detail === "object" ? error.detail : null;
      setErrorDetail(detail);
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

  function handleFuzzySearchClick() {
    setActiveSearchMode("fuzzy");
    setAppliedFuzzyQuery(fuzzySearchInput);
  }

  async function handleVectorSearchClick() {
    setActiveSearchMode("vector");
    setAppliedVectorQuery(vectorSearchInput);
    await loadVectorSearch(vectorSearchInput);
  }

  return (
    <main className="page">
      <h1>ArchitekturBild MVP</h1>

      <section className="searchSection">
        <div className="searchRow">
          <div className="searchBlock">
            <label htmlFor="vectorSearchInput" className="searchLabel">
              Vektor-Suche
            </label>
            <div className="searchActionRow">
              <textarea
                id="vectorSearchInput"
                className="searchInput"
                rows={2}
                value={vectorSearchInput}
                onChange={(event) => setVectorSearchInput(event.target.value)}
                placeholder="Semantische Suche eingeben"
              />
              <button type="button" onClick={() => void handleVectorSearchClick()} disabled={isVectorLoading}>
                suchen
              </button>
            </div>
          </div>
          <div className="searchBlock">
            <label htmlFor="fuzzySearchInput" className="searchLabel">
              Fuzzy-Suche
            </label>
            <div className="searchActionRow">
              <textarea
                id="fuzzySearchInput"
                className="searchInput"
                rows={2}
                value={fuzzySearchInput}
                onChange={(event) => setFuzzySearchInput(event.target.value)}
                placeholder="Fuzzy Suche eingeben"
              />
              <button type="button" onClick={handleFuzzySearchClick}>
                suchen
              </button>
            </div>
          </div>
        </div>
      </section>

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
      {errorDetail?.kind === "openrouter_html_error" ? (
        <section className="panel errorHtmlPanel">
          <h2>OpenRouter Fehlerseite ({errorDetail.status_code || 502})</h2>
          {errorDetail.request_id ? (
            <p className="metaLine">Request-ID: {errorDetail.request_id}</p>
          ) : null}
          <iframe
            title="OpenRouter HTML-Fehler"
            className="errorHtmlFrame"
            sandbox=""
            srcDoc={String(errorDetail.html || "")}
          />
        </section>
      ) : null}
      {errorMessage && errorDetail?.kind !== "openrouter_html_error" ? <p className="error">{errorMessage}</p> : null}

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
        <h2>LLM-Calls</h2>
        {historyError ? <p className="error">{historyError}</p> : null}
        {vectorError && activeSearchMode === "vector" ? <p className="error">{vectorError}</p> : null}
        {activeSearchMode === "vector" && isVectorLoading ? <p className="muted">Vektor-Suche laeuft...</p> : null}
        {activeSearchMode === "fuzzy" && normalizeText(appliedFuzzyQuery) ? (
          <p className="metaLine">
            Fuzzy-Treffer fuer: <strong>{appliedFuzzyQuery}</strong>
          </p>
        ) : null}
        {activeSearchMode === "vector" && normalizeText(appliedVectorQuery) ? (
          <p className="metaLine">
            Vektor-Treffer fuer: <strong>{appliedVectorQuery}</strong>
          </p>
        ) : null}
        {!displayedItems.length ? (
          <p className="muted">
            {(activeSearchMode === "fuzzy" && normalizeText(appliedFuzzyQuery)) ||
            (activeSearchMode === "vector" && normalizeText(appliedVectorQuery))
              ? "Keine relevanten Treffer gefunden."
              : "Noch keine frueheren Calls vorhanden."}
          </p>
        ) : (
          <div className="historyList">
            {displayedItems.map((item) => (
              <article key={`${item.source_type}-${item.id}`} className="panel historyItem">
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
                    <p className="sourceBadge">
                      {item.source_type === "current" ? "Aktueller Call" : "Historie"}
                    </p>
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
