function IngredientList({ ingredientes }) {
  if (!ingredientes?.length) return null;

  return (
    <ul className="ingredient-list">
      {ingredientes.map((ing, index) => (
        <li key={`${ing.nombre}-${index}`}>
          <span>{ing.nombre}</span>
          <span className="muted">{ing.gramos} g</span>
        </li>
      ))}
    </ul>
  );
}

function MinutaView({ minuta }) {
  if (!minuta) return null;

  return (
    <div className="minuta-view">
      <div className="minuta-meta">
        <p>
          <strong>Niño:</strong> {minuta.nino_id}
        </p>
        <p>
          <strong>Semana:</strong> {minuta.semana}
        </p>
        {minuta.alergenos_excluidos?.length > 0 && (
          <p>
            <strong>Alérgenos excluidos:</strong>{" "}
            {minuta.alergenos_excluidos.join(", ")}
          </p>
        )}
      </div>

      {minuta.dias?.map((dia) => (
        <article key={dia.dia} className="dia-card">
          <h3>{dia.dia}</h3>
          {dia.tiempos?.map((tiempo) => (
            <div key={`${dia.dia}-${tiempo.nombre}`} className="tiempo-card">
              <div className="tiempo-header">
                <h4>{tiempo.nombre}</h4>
                <span
                  className={`badge ${
                    tiempo.verificado_alergenos ? "badge-ok" : "badge-error"
                  }`}
                >
                  {tiempo.verificado_alergenos
                    ? "Alérgenos verificados"
                    : "Sin verificar"}
                </span>
              </div>
              <p className="plato">{tiempo.plato}</p>
              <IngredientList ingredientes={tiempo.ingredientes} />
              <p className="muted">
                {tiempo.kcal != null && <span>{tiempo.kcal} kcal</span>}
                {tiempo.fuente_normativa && (
                  <span> · {tiempo.fuente_normativa}</span>
                )}
              </p>
            </div>
          ))}
        </article>
      ))}
    </div>
  );
}

export default function MinutaResult({ result, error, loading }) {
  const minuta = result?.minuta;

  return (
    <section className="card" aria-live="polite">
      <h2>Resultado</h2>

      {loading && <p className="muted">Esperando respuesta del LLM…</p>}

      {error && (
        <pre className="error-box" role="alert">
          {error}
        </pre>
      )}

      {!loading && !error && !result && (
        <p className="muted">
          Envía una consulta para ver la minuta estructurada en JSON.
        </p>
      )}

      {minuta && <MinutaView minuta={minuta} />}

      {result && (
        <details className="json-details">
          <summary>Ver JSON completo</summary>
          <pre>{JSON.stringify(result, null, 2)}</pre>
        </details>
      )}
    </section>
  );
}
