function VectorPreview({ label, dimensions, preview }) {
  if (!preview?.length) return null;

  return (
    <div className="vector-preview">
      <p className="vector-label">
        <strong>{label}</strong>
        <span className="muted">
          {" "}
          — {dimensions} dimensiones · primeras 12: [{preview.join(", ")}…]
        </span>
      </p>
      <div className="vector-bars" aria-hidden="true">
        {preview.map((value, index) => (
          <span
            key={`${label}-${index}`}
            className="vector-bar"
            style={{
              height: `${Math.min(Math.abs(value) * 120, 100)}%`,
              backgroundColor: value >= 0 ? "var(--primary)" : "var(--error)",
            }}
          />
        ))}
      </div>
    </div>
  );
}

function ChunkCard({ chunk, variant = "retrieved" }) {
  const source =
    chunk.metadata?.source ??
    chunk.metadata?.file_path ??
    chunk.id ??
    "sin fuente";

  return (
    <article className="chunk-card">
      <header className="chunk-header">
        <span className="chunk-rank">
          {variant === "retrieved" ? `#${chunk.rank}` : chunk.id?.slice(0, 8)}
        </span>
        <span className="muted">{chunk.length} caracteres</span>
        {chunk.similarity_score != null && (
          <span className="badge badge-ok">
            score {chunk.similarity_score}
          </span>
        )}
      </header>
      <p className="chunk-source">{source}</p>
      <pre className="chunk-content">{chunk.content}</pre>
      {chunk.embedding?.preview && (
        <VectorPreview
          label="Vector almacenado"
          dimensions={chunk.embedding.dimensions}
          preview={chunk.embedding.preview}
        />
      )}
    </article>
  );
}

export default function DebugPanel({
  systemPrompt,
  corpus,
  ragDebug,
  loading,
  error,
  onRefreshCorpus,
  onPreviewRag,
  canPreviewRag,
}) {
  return (
    <section className="debug-section" aria-labelledby="debug-title">
      <div className="debug-header">
        <div>
          <h2 id="debug-title">Pre-prompt y vectorización RAG</h2>
          <p className="muted">
            Inspecciona el system prompt y cómo la consulta se recupera del
            corpus indexado en Chroma.
          </p>
        </div>
        <div className="debug-actions">
          <button
            type="button"
            className="btn btn-secondary btn-small"
            onClick={onRefreshCorpus}
            disabled={loading}
          >
            Actualizar corpus
          </button>
          <button
            type="button"
            className="btn btn-secondary btn-small"
            onClick={onPreviewRag}
            disabled={loading || !canPreviewRag}
          >
            {loading ? "Recuperando…" : "Vista previa RAG"}
          </button>
        </div>
      </div>

      <div className="debug-grid">
        <div className="card debug-card">
          <h3>Pre-prompt (system prompt)</h3>
          {systemPrompt ? (
            <pre className="prompt-box">{systemPrompt}</pre>
          ) : (
            <p className="muted">Cargando pre-prompt…</p>
          )}
        </div>

        <div className="card debug-card">
          <h3>Corpus indexado en Chroma</h3>
          {corpus ? (
            <>
              <p className="muted">
                <strong>{corpus.total_chunks}</strong> fragmentos · modelo{" "}
                <code>{corpus.embed_model}</code> · chunk{" "}
                {corpus.chunk_size}/{corpus.chunk_overlap}
              </p>
              <div className="chunk-list">
                {corpus.chunks?.slice(0, 6).map((chunk) => (
                  <ChunkCard key={chunk.id} chunk={chunk} variant="indexed" />
                ))}
              </div>
              {corpus.total_chunks > 6 && (
                <p className="muted">
                  Mostrando 6 de {corpus.total_chunks} fragmentos indexados.
                </p>
              )}
            </>
          ) : (
            <p className="muted">Cargando corpus…</p>
          )}
        </div>
      </div>

      <div className="card debug-card debug-retrieval">
        <h3>Recuperación para la consulta actual</h3>

        {error && (
          <pre className="error-box" role="alert">
            {error}
          </pre>
        )}

        {!ragDebug && !loading && !error && (
          <p className="muted">
            Escribe una consulta y pulsa «Vista previa RAG» o «Generar minuta»
            para ver la vectorización de la consulta y los top-k fragmentos MMR.
          </p>
        )}

        {loading && <p className="muted">Calculando embeddings y recuperación…</p>}

        {ragDebug && (
          <>
            <p className="muted">
              Consulta: <em>{ragDebug.consulta}</em>
            </p>

            <VectorPreview
              label="Embedding de la consulta"
              dimensions={ragDebug.query_embedding?.dimensions}
              preview={ragDebug.query_embedding?.preview}
            />

            <p className="muted retriever-meta">
              Retriever: {ragDebug.retriever?.type} · k={ragDebug.retriever?.k}{" "}
              · fetch_k={ragDebug.retriever?.fetch_k} · λ=
              {ragDebug.retriever?.lambda_mult}
            </p>

            <div className="chunk-list">
              {ragDebug.chunks?.map((chunk) => (
                <ChunkCard key={chunk.rank} chunk={chunk} variant="retrieved" />
              ))}
            </div>
          </>
        )}
      </div>
    </section>
  );
}
