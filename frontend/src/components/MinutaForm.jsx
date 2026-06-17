export default function MinutaForm({
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
      <h2>Generar minuta</h2>

      <div className="presets">
        <p className="muted">Escenarios de la clase:</p>
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
          <label htmlFor="nino_id">ID del niño</label>
          <input
            id="nino_id"
            name="nino_id"
            type="text"
            value={form.nino_id}
            onChange={updateField("nino_id")}
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
            Usa el mismo session_id para probar memoria contextual entre consultas.
          </p>
        </div>

        <div className="field">
          <label htmlFor="consulta">Consulta</label>
          <textarea
            id="consulta"
            name="consulta"
            rows={5}
            value={form.consulta}
            onChange={updateField("consulta")}
            placeholder="Ej: Maria, 2 años, alergia lactosa. Genera almuerzo del lunes…"
            required
          />
        </div>

        <button type="submit" className="btn btn-primary" disabled={loading}>
          {loading ? "Generando minuta…" : "Generar minuta"}
        </button>
      </form>
    </section>
  );
}
