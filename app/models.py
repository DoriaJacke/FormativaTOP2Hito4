from datetime import datetime
from typing import Any, List, Literal, Optional

from pydantic import BaseModel, Field


class PasoSolucion(BaseModel):
    orden: int = Field(ge=1)
    descripcion: str
    comando: Optional[str] = None


class ReferenciaDocumental(BaseModel):
    documento: str
    seccion: str
    fuente_documento: str


class RespuestaSoporte(BaseModel):
    ticket_id: str
    categoria: Literal["docker", "linux", "git", "infra", "acceso", "faq", "general"]
    resumen: str
    nivel_confianza: Literal["alta", "media", "baja"]
    generada_en: datetime
    pasos: List[PasoSolucion]
    referencias_documentales: List[ReferenciaDocumental] = Field(default_factory=list)
    notas_adicionales: Optional[str] = None


class SolicitudSoporte(BaseModel):
    ticket_id: str
    consulta: str
    session_id: str
    nivel_usuario: Optional[Literal["usuario", "tecnico"]] = "usuario"


class ConsultaRagDebug(BaseModel):
    consulta: str


class FuenteRag(BaseModel):
    rank: int
    content: str
    source: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    length: int
    similarity_score: Optional[float] = None


class PipelineRag(BaseModel):
    pregunta: str
    embed_model: str
    query_embedding: dict[str, Any]
    vector_store: dict[str, Any]
    retriever: dict[str, Any]
    llm_model: str
    chunks_recuperados: int
