function SourceCard({ fuente }) {
  return (
    <article className="chunk-card">
      <header className="chunk-header">
        <span className="chunk-rank">#{fuente.rank}</span>
        <span className="muted">{fuente.length} caracteres</span>
        {fuente.similarity_score != null && (
          <span className="badge badge-ok">
            score {fuente.similarity_score}
          </span>
        )}
      </header>
      <p className="chunk-source">{fuente.source}</p>
      <pre className="chunk-content">{fuente.content}</pre>
    </article>
  );
}

function ConfidenceBadge({ nivel }) {
  const className =
    nivel === "alta"
      ? "badge badge-ok"
      : nivel === "media"
        ? "badge"
        : "badge badge-error";

  return <span className={className}>Confianza {nivel}</span>;
}

function SupportView({ respuesta }) {
  if (!respuesta) return null;

  return (
    <div className="support-view">
      <div className="support-meta">
        <p>
          <strong>Ticket:</strong> {respuesta.ticket_id}
        </p>
        <p>
          <strong>Categoría:</strong>{" "}
          <span className="categoria-tag">{respuesta.categoria}</span>
        </p>
        <p className="resumen">{respuesta.resumen}</p>
        <ConfidenceBadge nivel={respuesta.nivel_confianza} />
        {respuesta.nivel_confianza === "baja" &&
          respuesta.resumen
            ?.toLowerCase()
            .includes("no registra el procedimiento") && (
            <p className="sin-cobertura">
              Sin cobertura documental en el corpus indexado. Respuesta basada en
              incertidumbre razonable y escalamiento.
            </p>
          )}
      </div>

      {respuesta.pasos?.length > 0 && (
        <div className="pasos-section">
          <h3>Pasos de solución</h3>
          <ol className="pasos-list">
            {respuesta.pasos.map((paso) => (
              <li key={paso.orden} className="paso-card">
                <p>{paso.descripcion}</p>
                {paso.comando && (
                  <pre className="comando-box">{paso.comando}</pre>
                )}
              </li>
            ))}
          </ol>
        </div>
      )}

      {respuesta.referencias_documentales?.length > 0 && (
        <div className="refs-section">
          <h3>Referencias documentales</h3>
          <ul className="refs-list">
            {respuesta.referencias_documentales.map((ref, index) => (
              <li key={`${ref.fuente_documento}-${index}`}>
                <strong>{ref.documento}</strong> — {ref.seccion}
                <span className="muted"> ({ref.fuente_documento})</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {respuesta.notas_adicionales && (
        <p className="notas">
          <strong>Notas:</strong> {respuesta.notas_adicionales}
        </p>
      )}
    </div>
  );
}

export default function SupportResult({ result, error, loading }) {
  const respuesta = result?.respuesta;
  const fuentes = result?.fuentes ?? [];

  return (
    <section className="card" aria-live="polite">
      <h2>Respuesta + Fuentes</h2>

      {loading && <p className="muted">Esperando respuesta del LLM…</p>}

      {error && (
        <pre className="error-box" role="alert">
          {error}
        </pre>
      )}

      {!loading && !error && !result && (
        <p className="muted">
          Envía una consulta de soporte para ver la respuesta estructurada y las
          fuentes documentales recuperadas.
        </p>
      )}

      {respuesta && <SupportView respuesta={respuesta} />}

      {fuentes.length > 0 && (
        <div className="fuentes-section">
          <h3>Fuentes RAG consultadas ({fuentes.length})</h3>
          <p className="muted">
            Fragmentos de manuales Docker/Linux/Git, procedimientos y FAQ
            usados como contexto.
          </p>
          <div className="chunk-list">
            {fuentes.map((fuente) => (
              <SourceCard key={fuente.rank} fuente={fuente} />
            ))}
          </div>
        </div>
      )}

      {result && (
        <details className="json-details">
          <summary>Ver JSON completo</summary>
          <pre>{JSON.stringify(result, null, 2)}</pre>
        </details>
      )}
    </section>
  );
}
