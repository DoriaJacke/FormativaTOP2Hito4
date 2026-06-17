from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class Ingrediente(BaseModel):
    nombre: str
    gramos: float = Field(gt=0, lt=500, description="Peso en gramos")


class TiempoComida(BaseModel):
    nombre: str
    plato: str
    ingredientes: List[Ingrediente]
    kcal: Optional[float] = Field(default=None, gt=0, lt=600)
    proteinas_g: Optional[float] = None
    carbohidratos_g: Optional[float] = None
    grasas_g: Optional[float] = None
    verificado_alergenos: bool
    fuente_normativa: Optional[str] = None


class DiaSemana(BaseModel):
    dia: str
    tiempos: List[TiempoComida]


class Minuta(BaseModel):
    nino_id: str
    semana: str
    alergenos_excluidos: List[str]
    generada_en: datetime
    dias: List[DiaSemana]

    def verificar_alergenos(self, alergenos: List[str]) -> bool:
        for dia in self.dias:
            for tiempo in dia.tiempos:
                for ingrediente in tiempo.ingredientes:
                    for alergeno in alergenos:
                        if alergeno.lower() in ingrediente.nombre.lower():
                            return False
        return True


class SolicitudMinuta(BaseModel):
    nino_id: str
    consulta: str
    session_id: str


class ConsultaRagDebug(BaseModel):
    consulta: str
