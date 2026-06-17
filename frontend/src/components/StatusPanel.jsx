function StatusBadge({ ok, label }) {
  return (
    <span className={`badge ${ok ? "badge-ok" : "badge-error"}`}>
      {ok ? "OK" : "Error"} — {label}
    </span>
  );
}

export default function StatusPanel({ health, readiness, error, loading }) {
  const checks = readiness?.checks ?? {};

  return (
    <section className="card" aria-live="polite">
      <h2>Estado del sistema</h2>

      {loading && <p className="muted">Verificando servicios…</p>}

      <div className="status-grid">
        <StatusBadge ok={health?.status === "ok"} label="API" />
        <StatusBadge ok={Boolean(checks.redis)} label="Redis" />
        <StatusBadge ok={Boolean(checks.chroma)} label="Chroma RAG" />
        <StatusBadge ok={Boolean(checks.ollama)} label="Ollama" />
      </div>

      {checks.chroma_chunks != null && (
        <p className="muted">
          Fragmentos indexados: <strong>{checks.chroma_chunks}</strong>
        </p>
      )}

      {Array.isArray(checks.ollama_models) && checks.ollama_models.length > 0 && (
        <p className="muted">
          Modelos: {checks.ollama_models.join(", ")}
        </p>
      )}

      {error && <p className="error-text">{error}</p>}
    </section>
  );
}
