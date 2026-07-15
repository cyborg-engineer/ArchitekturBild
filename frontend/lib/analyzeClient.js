const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

export async function analyzeImage({ file, systemPrompt, model, signal }) {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("system_prompt", systemPrompt);
  formData.append("model", model);

  const response = await fetch(`${API_BASE_URL}/api/analyze`, {
    method: "POST",
    body: formData,
    signal
  });

  let payload = null;
  try {
    payload = await response.json();
  } catch {
    payload = null;
  }

  if (!response.ok) {
    throw new Error(payload?.detail || "Unbekannter Backend-Fehler");
  }

  return {
    description: payload?.description || "",
    model: payload?.model || model,
    systemPrompt: payload?.system_prompt || systemPrompt
  };
}

export async function fetchHistory({ limit = 20, signal } = {}) {
  const response = await fetch(`${API_BASE_URL}/api/history?limit=${limit}`, {
    method: "GET",
    signal
  });

  let payload = null;
  try {
    payload = await response.json();
  } catch {
    payload = null;
  }

  if (!response.ok) {
    throw new Error(payload?.detail || "Historie konnte nicht geladen werden.");
  }

  return Array.isArray(payload?.items) ? payload.items : [];
}
