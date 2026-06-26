import { useCallback, useEffect, useState } from "react";
import {
  consultarSoporte,
  getHealth,
  getRagCorpus,
  getReadiness,
  getSystemPrompt,
  reindexCorpus,
  retrieveRagDebug,
} from "./api";
import StatusPanel from "./components/StatusPanel";
import SupportForm from "./components/SupportForm";
import SupportResult from "./components/SupportResult";
import HistoryPanel from "./components/HistoryPanel";
import DebugPanel from "./components/DebugPanel";

const DEMO_PRESETS = [
  {
    id: "docker-simple",
    label: "Docker - consulta simple",
    ticket_id: "TKT-0042",
    session_id: "soporte:docker",
    nivel_usuario: "tecnico",
    consulta:
      "Mi contenedor web no inicia. El error dice 'port is already allocated' en el puerto 8080.",
  },
  {
    id: "docker-complex",
    label: "Docker - consulta compleja",
    ticket_id: "TKT-0187",
    session_id: "soporte:infra",
    nivel_usuario: "tecnico",
    consulta:
      "Tenemos un servicio web en Docker Compose que dejó de levantarse en producción (P2). El error es \"port is already allocated\" en el puerto 8080. Ya ejecuté docker ps y veo otro contenedor usando ese puerto, pero al intentar detenerlo con docker stop me da \"Permission denied\". En el host (Ubuntu) sospecho que hay un proceso del sistema ocupando el puerto. Necesito: (1) identificar qué ocupa el 8080, (2) liberar el puerto de forma segura, (3) relanzar el stack con docker compose up -d, y (4) saber si debo escalar a Nivel 2 o si puedo cerrar el ticket yo mismo según los procedimientos internos.",
  },
  {
    id: "escenario-3",
    label: "Escenario 3 - consulta sin respuesta documental",
    ticket_id: "TKT-0300",
    session_id: "soporte:escenario3",
    nivel_usuario: "usuario",
    consulta:
      "Necesito configurar la autenticacion SSO con Azure Active Directory para nuestra aplicacion interna de nominas. ¿Existe un procedimiento documentado para integrar SAML 2.0, que permisos debo solicitar y que pasos debo seguir segun la documentacion interna?",
  },
];

const INITIAL_FORM = {
  ticket_id: "TKT-0042",
  session_id: "soporte:docker",
  nivel_usuario: "tecnico",
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
  const [loadingSoporte, setLoadingSoporte] = useState(false);
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

  function buildConsulta(payload) {
    return (
      `Ticket: ${payload.ticket_id}\n` +
      `Nivel usuario: ${payload.nivel_usuario}\n` +
      payload.consulta
    );
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setLoadingSoporte(true);
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
      const data = await consultarSoporte(form);
      setResult(data);
      entry.response = data;
      setHistory((prev) => [entry, ...prev]);
    } catch (err) {
      const message = err.message ?? "Error desconocido";
      setError(message);
      entry.error = message;
      setHistory((prev) => [entry, ...prev]);
    } finally {
      setLoadingSoporte(false);
    }
  }

  function applyPreset(preset) {
    setForm({
      ticket_id: preset.ticket_id,
      session_id: preset.session_id,
      nivel_usuario: preset.nivel_usuario,
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
          <p className="eyebrow">Caso 2 — Asistente de Soporte Técnico</p>
          <h1>Soporte IA — Arquitectura RAG</h1>
          <p className="subtitle">
            Usuario → Pregunta → Embedding → Base Vectorial → Recuperación →
            LLM → Respuesta + Fuentes
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

          <SupportForm
            form={form}
            setForm={setForm}
            onSubmit={handleSubmit}
            loading={loadingSoporte}
            presets={DEMO_PRESETS}
            onPreset={applyPreset}
          />

        </section>

        <section className="column">
          <SupportResult
            result={result}
            error={error}
            loading={loadingSoporte}
          />
          <HistoryPanel history={history} onClear={() => setHistory([])} />
        </section>
      </main>

      <DebugPanel
        systemPrompt={systemPrompt}
        corpus={corpus}
        ragDebug={ragDebug}
        loading={debugLoading}
        error={debugError}
        onRefreshCorpus={loadDebugData}
        onPreviewRag={() => fetchRagDebug(buildConsulta(form))}
        canPreviewRag={Boolean(form.consulta.trim())}
      />
    </div>
  );
}
