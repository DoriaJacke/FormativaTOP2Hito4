const API_BASE = import.meta.env.VITE_API_BASE ?? "/api";

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
    ...options,
  });

  const text = await response.text();
  let data = null;

  if (text) {
    try {
      data = JSON.parse(text);
    } catch {
      data = { raw: text };
    }
  }

  if (!response.ok) {
    const message =
      data?.detail ??
      data?.error ??
      (typeof data === "string" ? data : `Error HTTP ${response.status}`);
    throw new Error(
      typeof message === "object" ? JSON.stringify(message, null, 2) : message,
    );
  }

  return data;
}

export function getHealth() {
  return request("/health");
}

export function getReadiness() {
  return request("/health/ready");
}

export function consultarSoporte(payload) {
  return request("/soporte/consultar", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function reindexCorpus() {
  return request("/admin/reindex", { method: "POST" });
}

export function getSystemPrompt() {
  return request("/debug/system-prompt");
}

export function getRagCorpus() {
  return request("/debug/rag/corpus");
}

export function retrieveRagDebug(consulta) {
  return request("/debug/rag/retrieve", {
    method: "POST",
    body: JSON.stringify({ consulta }),
  });
}
