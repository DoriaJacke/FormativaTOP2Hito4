export default function SupportForm({
  form,
  setForm,
  onSubmit,
  loading,
  presets,
  onPreset,
}) {
  function updateField(field) {
    return (event) => {
      setForm((prev) => ({ ...prev, [field]: event.target.value }));
    };
  }

  return (
    <section className="card">
      <h2>Consulta de soporte</h2>

      <div className="presets">
        <p className="muted">Escenarios de prueba:</p>
        <div className="preset-buttons">
          {presets.map((preset) => (
            <button
              key={preset.id}
              type="button"
              className="btn btn-preset"
              onClick={() => onPreset(preset)}
            >
              {preset.label}
            </button>
          ))}
        </div>
      </div>

      <form onSubmit={onSubmit} className="form">
        <div className="field">
          <label htmlFor="ticket_id">ID del ticket</label>
          <input
            id="ticket_id"
            name="ticket_id"
            type="text"
            value={form.ticket_id}
            onChange={updateField("ticket_id")}
            autoComplete="off"
            spellCheck={false}
            required
          />
        </div>

        <div className="field">
          <label htmlFor="session_id">Session ID (Redis)</label>
          <input
            id="session_id"
            name="session_id"
            type="text"
            value={form.session_id}
            onChange={updateField("session_id")}
            autoComplete="off"
            spellCheck={false}
            required
          />
          <p className="hint">
            Usa el mismo session_id para probar memoria contextual entre consultas
            del mismo ticket.
          </p>
        </div>

        <div className="field">
          <label htmlFor="nivel_usuario">Nivel del usuario</label>
          <select
            id="nivel_usuario"
            name="nivel_usuario"
            value={form.nivel_usuario}
            onChange={updateField("nivel_usuario")}
          >
            <option value="usuario">Usuario final</option>
            <option value="tecnico">Técnico de soporte</option>
          </select>
        </div>

        <div className="field">
          <label htmlFor="consulta">Problema / consulta</label>
          <textarea
            id="consulta"
            name="consulta"
            rows={5}
            value={form.consulta}
            onChange={updateField("consulta")}
            placeholder="Ej: Mi contenedor Docker no inicia, error port is already allocated en 8080…"
            required
          />
        </div>

        <button type="submit" className="btn btn-primary" disabled={loading}>
          {loading ? "Procesando RAG + LLM…" : "Enviar consulta (RAG)"}
        </button>
      </form>
    </section>
  );
}
