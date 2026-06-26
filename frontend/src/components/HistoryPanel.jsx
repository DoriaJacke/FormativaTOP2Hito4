export default function HistoryPanel({ history, onClear }) {
  if (history.length === 0) {
    return (
      <section className="card">
        <h2>Historial de sesión (UI)</h2>
        <p className="muted">
          Las consultas de esta pestaña aparecerán aquí. Redis mantiene la
          memoria del LLM entre peticiones con el mismo session_id.
        </p>
      </section>
    );
  }

  return (
    <section className="card">
      <div className="history-header">
        <h2>Historial de sesión (UI)</h2>
        <button type="button" className="btn btn-secondary btn-small" onClick={onClear}>
          Limpiar
        </button>
      </div>

      <ul className="history-list">
        {history.map((entry) => (
          <li key={entry.id} className="history-item">
            <time dateTime={entry.at}>
              {new Date(entry.at).toLocaleString("es-CL")}
            </time>
            <p>
              <strong>{entry.request.ticket_id}</strong> ({entry.request.session_id}) — {entry.request.consulta}
            </p>
            {entry.error ? (
              <p className="error-text">{entry.error}</p>
            ) : (
              <p className="muted">Respuesta OK</p>
            )}
          </li>
        ))}
      </ul>
    </section>
  );
}
