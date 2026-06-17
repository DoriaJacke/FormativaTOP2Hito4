# Actividad formativa: Experimentación guiada con Minutas IA

> **Versión LaTeX (PDF):** compila `actividad_formativa.tex` con `pdflatex` (dos pasadas).

**Asignatura:** IA Embebida en Sistemas Computacionales  
**Duración estimada:** 50–60 minutos  
**Modalidad:** Individual o parejas  
**Tipo:** Formativa (no calificada con nota, pero con entregable breve)

---

## Propósito

Profundizar en la arquitectura entregada (LLM + RAG + Redis + LangChain) mediante **experimentación controlada**, considerando que **no todos los equipos tienen la misma capacidad** para ejecutar modelos de IA locales.

Al finalizar deberías poder explicar, con evidencia de tu propia prueba:

1. Qué aporta el **RAG** frente a un LLM aislado.
2. Qué aporta **Redis** como memoria de sesión.
3. Cómo el **pre-prompt** y el **tamaño del modelo** afectan calidad, latencia y consumo de recursos.
4. Qué trade-offs harías al desplegar este sistema en un jardín infantil real.

---

## Antes de empezar

### Requisitos mínimos

- Docker Desktop o Docker Engine + Compose v2
- Conexión a internet (solo la primera vez, para descargar imágenes y modelos)
- Repositorio clonado y comando `make up` funcional (o acceso al servidor del curso; ver Perfil R)

### Panel de trabajo

Abre **[http://localhost:3000](http://localhost:3000)** y ubica estas secciones:

- Formulario de generación de minutas
- **Pre-prompt y vectorización RAG** (bloque inferior)
- Presets de actividades (María, Pedro consulta 1 y 2)

---

## Paso 0: Elige tu perfil de hardware (5 min)

No todos corren el mismo modelo. **Elige un perfil según tu equipo** y configúralo antes de los experimentos.

| Perfil | RAM aprox. | Modelo LLM sugerido | Comando de configuración |
|--------|------------|---------------------|--------------------------|
| **L — Ligero** | 8 GB, sin GPU | `llama3.2:1b` | `make perfil-ligero` |
| **M — Medio** | 16 GB | `llama3.2` (3B) | `make perfil-medio` |
| **A — Alto** | 16+ GB + GPU / Apple Silicon | `llama3.1:8b` | `make perfil-alto` |
| **R — Remoto** | PC débil o sin Docker | Usa Ollama del laboratorio | Ver sección al final |

Después de elegir perfil:

```bash
make perfil-ligero   # o perfil-medio / perfil-alto
docker compose down
make up
make ready
```

Anota en tu bitácora:

- Perfil elegido: ___
- Modelo activo (ver en panel «Estado del sistema» o `make ready`): ___
- Tiempo aproximado de la **primera** respuesta del LLM (segundos): ___

> **Nota docente:** El objetivo no es comparar notas por velocidad, sino **razonar sobre trade-offs** con el hardware disponible.

---

## Experimento 1: ¿Qué aporta el RAG? (12 min)

### Hipótesis

*Sin contexto documental, el LLM ignora la normativa JUNJI/MINSAL y responde de forma genérica.*

### Procedimiento

1. En el panel inferior, revisa el **pre-prompt** y al menos **2 fragmentos** del corpus indexado.
2. Usa el preset **«Actividad 1 — María (lactosa)»**.
3. Pulsa **«Vista previa RAG»** y observa:
   - Embedding de la consulta (dimensiones y preview)
   - Fragmentos recuperados (contenido y `similarity_score`)
4. Genera la minuta y compara el resultado con los fragmentos recuperados.
5. Abre `documentos_normativos/normativa_junji_demo.txt` y verifica si algún fragmento recuperado menciona:
   - rango calórico 200–350 kcal
   - alérgenos a excluir
   - nombres de ingredientes chilenos

### Registro (completa en tu entrega)

| Pregunta | Tu observación |
|----------|----------------|
| ¿Cuántos fragmentos recuperó el retriever? | |
| ¿Algún fragmento menciona kcal o alérgenos? Cita una línea. | |
| ¿El plato generado respeta la lactosa? | |
| ¿El campo `fuente_normativa` aparece? ¿Es creíble? | |

### Pregunta de reflexión

Si mañana se publica una nueva circular JUNJI, **¿qué componente actualizas sin reentrenar el LLM?** Justifica en 2–3 líneas.

---

## Experimento 2: Memoria con Redis (10 min)

### Hipótesis

*Con el mismo `session_id`, el sistema no debería obligar a repetir las alergias en cada consulta.*

### Procedimiento

1. Preset **«Actividad 2 — Pedro consulta 1»** → Generar minuta.
2. Preset **«Actividad 2 — Pedro consulta 2 (memoria)»** → Generar minuta **sin** editar el `session_id`.
3. (Opcional) Repite la consulta 2 cambiando `session_id` a `test:pedro-nuevo` y compara.

### Verificación técnica (elige una)

```bash
# Opción A: Redis CLI
docker compose exec redis redis-cli LRANGE minuta:test:pedro 0 -1

# Opción B: solo observación en el panel de historial (UI)
```

### Registro

| Escenario | ¿Excluyó huevo/mariscos? | ¿Por qué? |
|-----------|--------------------------|-----------|
| Consulta 2, mismo `session_id` | | |
| Consulta 2, `session_id` distinto (opcional) | | |

### Pregunta de reflexión

¿Redis almacena «inteligencia» o solo **historial de mensajes**? ¿Qué pasaría si el TTL fuera de 24 h a 7 días en un jardín con 80 niños?

---

## Experimento 3: Pre-prompt y calidad del JSON (10 min)

### Procedimiento

1. Lee el pre-prompt en el panel inferior (reglas 1–9).
2. Genera una minuta con esta consulta personalizada:

   > *«Niño de 18 meses, sin alergias. Once del miércoles con ingredientes de temporada.»*

3. Abre **«Ver JSON completo»** en el resultado.
4. Marca con ✓ o ✗:

   - [ ] `nino_id` es un valor real (no `"string"`)
   - [ ] `generada_en` es fecha ISO válida
   - [ ] `kcal` está entre 200 y 350
   - [ ] `verificado_alergenos` es coherente con la consulta
   - [ ] Ingredientes con nombres locales (porotos, choclo, etc.)

### Variante según perfil de hardware

| Perfil | Variante extra |
|--------|----------------|
| **L** | Si la respuesta tarda >90 s o falla, reduce `RETRIEVER_K=1` en `.env`, reinicia API y reintenta. Anota el cambio. |
| **M** | Sin variante; registra tiempo de respuesta. |
| **A** | Prueba `LLM_TEMPERATURE=0.5` en `.env`, reinicia y compara creatividad vs. consistencia. |
| **R** | Mismo flujo contra el servidor remoto; anota latencia de red. |

### Pregunta de reflexión

¿Basta con `format=json` en Ollama para garantizar un JSON **válido para producción**? Menciona al menos un caso que Pydantic podría rechazar.

---

## Experimento 4: Trade-off de modelos (8 min)

Objetivo: relacionar **potencia del equipo** con **calidad y latencia**, sin competir por hardware.

### Procedimiento

1. Anota tu perfil y modelo actual.
2. Si tu equipo lo permite **y el docente lo autoriza**, cambia temporalmente de perfil (ej. de M a L) y repite la consulta de María.
3. Completa la tabla (si no puedes cambiar de perfil, completa solo tu fila y en clase compararán entre pares):

| Métrica | Mi perfil | Otro perfil (opcional) |
|---------|-----------|-------------------------|
| Modelo | | |
| Tiempo 1.ª respuesta (s) | | |
| ¿JSON válido a la 1.ª? | | |
| ¿Plato nutricionalmente plausible? | | |
| ¿Alucinó ingredientes raros? | | |

### Pregunta de reflexión

En producción, ¿siempre conviene el modelo más grande? Nombra **dos criterios** además de la calidad del texto (ej. costo, latencia, privacidad, energía).

---

## Entregable formativo (máx. 1 página)

Sube un PDF o Markdown con:

1. **Perfil de hardware** usado y modelo Ollama activo.
2. **Tablas de registro** de los experimentos 1 y 2 (aunque sea incompleto si hubo fallos).
3. **Respuestas breves** (3–5 líneas cada una) a **dos** preguntas de reflexión a elección.
4. **Captura** del panel «Pre-prompt y vectorización RAG» mostrando al menos un fragmento recuperado.
5. **Un problema real** que detectaste (lento, JSON inválido, ingrediente incorrecto, etc.) y **qué capa** falló: LLM, RAG, Redis, prompt o validación.

> Si tu equipo no pudo ejecutar localmente, indica uso del **Perfil R** y adjunta capturas del servidor del curso con tu `session_id` identificable.

---

## Perfil R — Estudiantes sin PC potente (acceso remoto)

Si tu laptop no puede ejecutar Ollama de forma razonable:

1. Solicita al docente la URL del servidor (ej. `http://lab-ia.universidad.cl:11434`).
2. Crea un `.env` local con:

   ```env
   OLLAMA_BASE_URL=http://<servidor-del-curso>:11434
   LLM_MODEL=llama3.2:1b
   LLM_NUM_CTX=2048
   RETRIEVER_K=2
   ```

3. Levanta solo API + Redis + Web (sin contenedor `ollama` local), o usa el frontend apuntando al stack del laboratorio según indique el docente.

4. En la entrega, documenta claramente: **«Ejecución remota — sin inferencia local»**.

### Alternativa mínima sin Docker

Observa la demo del docente y completa los experimentos 1 y 3 **teóricamente**, citando capturas del proyector y el archivo `normativa_junji_demo.txt`. El docente puede aceptar esta vía solo si quedó sin equipo; prioriza siempre intentar Perfil L primero.

---

## Criterios de logro (autoevaluación)

| Criterio | Lo logré |
|----------|----------|
| Identifiqué qué hace el RAG en la arquitectura | ☐ |
| Demostré memoria de sesión con Redis | ☐ |
| Interpreté el pre-prompt y los fragmentos vectorizados | ☐ |
| Relacioné tamaño de modelo con latencia/calidad en mi contexto | ☐ |
| Distinguí fallo de LLM vs. fallo de validación/RAG | ☐ |

---

## Para seguir explorando (opcional)

- Agrega un párrafo propio a `documentos_normativos/` y ejecuta **Reindexar RAG**.
- Modifica una regla del pre-prompt en `app/system_prompt.py`, reconstruye la API y observa el cambio.
- Compara `RETRIEVER_K=2` vs. `RETRIEVER_K=6` y mide si el prompt se vuelve más lento.

---

## Comandos de referencia rápida

```bash
make perfil-ligero    # 8 GB RAM
make perfil-medio     # 16 GB RAM (default clase)
make perfil-alto      # equipos potentes
make up && make ready
make web-dev          # frontend en desarrollo
docker compose logs -f api
```

---

*Actividad alineada con el caso de estudio: sistema de minutas alimentarias JUNJI — Ingeniería Informática.*
