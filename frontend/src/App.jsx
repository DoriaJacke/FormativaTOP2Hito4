import { useCallback, useEffect, useState } from "react";
import {
  generarMinuta,
  getHealth,
  getRagCorpus,
  getReadiness,
  getSystemPrompt,
  reindexCorpus,
  retrieveRagDebug,
} from "./api";
import StatusPanel from "./components/StatusPanel";
import MinutaForm from "./components/MinutaForm";
import MinutaResult from "./components/MinutaResult";
import HistoryPanel from "./components/HistoryPanel";
import DebugPanel from "./components/DebugPanel";

const DEMO_PRESETS = [
  {
    id: "maria",
    label: "Actividad 1 — María (lactosa)",
    nino_id: "maria_001",
    session_id: "jard01:maria",
    consulta:
      "Maria, 2 anios, alergia lactosa. Genera almuerzo del lunes.",
  },
  {
    id: "pedro-1",
    label: "Actividad 2 — Pedro consulta 1",
    nino_id: "pedro_001",
    session_id: "test:pedro",
    consulta:
      "Pedro, 2 anios, alergico a mariscos y huevo. Genera desayuno del lunes.",
  },
  {
    id: "pedro-2",
    label: "Actividad 2 — Pedro consulta 2 (memoria)",
    nino_id: "pedro_001",
    session_id: "test:pedro",
    consulta:
      "Genera almuerzo del lunes respetando todas sus restricciones alimentarias.",
  },
];

const INITIAL_FORM = {
  nino_id: "maria_001",
  session_id: "jard01:maria",
  consulta: "",
};

export default function App() {
  const [form, setForm] = useState(INITIAL_FORM);
  const [health, setHealth] = useState(null);
  const [readiness, setReadiness] = useState(null);
  const [statusError, setStatusError] = useState("");
  const [loadingStatus, setLoadingStatus] = useState(false);

  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [loadingMinuta, setLoadingMinuta] = useState(false);
  const [reindexing, setReindexing] = useState(false);
  const [history, setHistory] = useState([]);

  const [systemPrompt, setSystemPrompt] = useState("");
  const [corpus, setCorpus] = useState(null);
  const [ragDebug, setRagDebug] = useState(null);
  const [debugLoading, setDebugLoading] = useState(false);
  const [debugError, setDebugError] = useState("");

  const loadDebugData = useCallback(async () => {
    try {
      const [promptData, corpusData] = await Promise.all([
        getSystemPrompt(),
        getRagCorpus(),
      ]);
      setSystemPrompt(promptData.system_prompt ?? "");
      setCorpus(corpusData);
    } catch (err) {
      setDebugError(err.message ?? "Error al cargar datos de depuración");
    }
  }, []);

  const fetchRagDebug = useCallback(async (consulta) => {
    if (!consulta.trim()) return;

    setDebugLoading(true);
    setDebugError("");

    try {
      const data = await retrieveRagDebug(consulta.trim());
      setRagDebug(data);
    } catch (err) {
      setRagDebug(null);
      setDebugError(err.message ?? "Error al recuperar fragmentos RAG");
    } finally {
      setDebugLoading(false);
    }
  }, []);

  const refreshStatus = useCallback(async () => {
    setLoadingStatus(true);
    setStatusError("");

    try {
      const [healthData, readyData] = await Promise.allSettled([
        getHealth(),
        getReadiness(),
      ]);

      if (healthData.status === "fulfilled") {
        setHealth(healthData.value);
      } else {
        setHealth(null);
      }

      if (readyData.status === "fulfilled") {
        setReadiness(readyData.value);
      } else {
        setReadiness(null);
        setStatusError(
          readyData.reason?.message ?? "El sistema aun no esta listo",
        );
      }
    } finally {
      setLoadingStatus(false);
    }
  }, []);

  useEffect(() => {
    refreshStatus();
    loadDebugData();
  }, [refreshStatus, loadDebugData]);

  async function handleSubmit(event) {
    event.preventDefault();
    setLoadingMinuta(true);
    setError("");
    setResult(null);

    const entry = {
      id: crypto.randomUUID(),
      at: new Date().toISOString(),
      request: { ...form },
      response: null,
      error: null,
    };

    try {
      const consulta = `ID del nino: ${form.nino_id}\n${form.consulta}`;
      void fetchRagDebug(consulta);
      const data = await generarMinuta(form);
      setResult(data);
      entry.response = data;
      setHistory((prev) => [entry, ...prev]);
    } catch (err) {
      const message = err.message ?? "Error desconocido";
      setError(message);
      entry.error = message;
      setHistory((prev) => [entry, ...prev]);
    } finally {
      setLoadingMinuta(false);
    }
  }

  function applyPreset(preset) {
    setForm({
      nino_id: preset.nino_id,
      session_id: preset.session_id,
      consulta: preset.consulta,
    });
    setError("");
    setResult(null);
  }

  async function handleReindex() {
    setReindexing(true);
    setError("");

    try {
      const data = await reindexCorpus();
      setResult(data);
      await refreshStatus();
      await loadDebugData();
      setRagDebug(null);
    } catch (err) {
      setError(err.message ?? "Error al reindexar");
    } finally {
      setReindexing(false);
    }
  }

  return (
    <div className="app">
      <a className="skip-link" href="#main-content">
        Saltar al contenido
      </a>

      <header className="header">
        <div>
          <p className="eyebrow">Ingeniería Informática — IA Embebida</p>
          <h1>Minutas IA</h1>
          <p className="subtitle">
            Panel de pruebas para LLM + RAG + Redis + LangChain + Ollama
          </p>
        </div>
        <div className="header-actions">
          <button
            type="button"
            className="btn btn-secondary"
            onClick={refreshStatus}
            disabled={loadingStatus}
          >
            {loadingStatus ? "Verificando…" : "Verificar estado"}
          </button>
          <button
            type="button"
            className="btn btn-secondary"
            onClick={handleReindex}
            disabled={reindexing}
          >
            {reindexing ? "Reindexando…" : "Reindexar RAG"}
          </button>
        </div>
      </header>

      <main id="main-content" className="layout">
        <section className="column">
          <StatusPanel
            health={health}
            readiness={readiness}
            error={statusError}
            loading={loadingStatus}
          />

          <MinutaForm
            form={form}
            setForm={setForm}
            onSubmit={handleSubmit}
            loading={loadingMinuta}
            presets={DEMO_PRESETS}
            onPreset={applyPreset}
          />
        </section>

        <section className="column">
          <MinutaResult result={result} error={error} loading={loadingMinuta} />
          <HistoryPanel history={history} onClear={() => setHistory([])} />
        </section>
      </main>

      <DebugPanel
        systemPrompt={systemPrompt}
        corpus={corpus}
        ragDebug={ragDebug}
        loading={debugLoading || loadingMinuta}
        error={debugError}
        onRefreshCorpus={loadDebugData}
        onPreviewRag={() =>
          fetchRagDebug(`ID del nino: ${form.nino_id}\n${form.consulta}`)
        }
        canPreviewRag={Boolean(form.consulta.trim())}
      />
    </div>
  );
}
