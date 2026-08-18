from enum import Enum
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator


class ClasseML(str, Enum):
    VALIDO_AUTOMATICO = "valido_automatico"
    REVISAR = "revisar"
    RECUSAR_AUTOMATICO = "recusar_automatico"


class NivelConfianca(str, Enum):
    ALTA = "alta"
    MEDIA = "media"
    BAIXA = "baixa"


class AcaoML(str, Enum):
    VALIDO_AUTOMATICO = "VALIDO_AUTOMATICO"
    RECUSAR_AUTOMATICO = "RECUSAR_AUTOMATICO"
    REVISAR = "REVISAR"
    REVISAO_PRIORITARIA = "REVISAO_PRIORITARIA"
    REVISAO_ML_OFFLINE = "REVISAO_ML_OFFLINE"


class LoteInput(BaseModel):
    """Contrato estrito para requisições recebidas pela API."""

    model_config = ConfigDict(extra="forbid", strict=True)

    lote_id: str = Field(min_length=1, max_length=80)
    status_raw: str = Field(min_length=1, max_length=100)
    turno: str
    tem_obs: bool

    @field_validator("turno")
    @classmethod
    def validar_turno(cls, value: str) -> str:
        if not isinstance(value, str):
            raise ValueError("turno deve ser uma string")
        turno = value.strip().upper()
        if turno not in {"A", "B", "C"}:
            raise ValueError("turno deve ser A, B ou C")
        return turno


class PredictionOutput(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    lote_id: str
    classe: ClasseML
    probabilidade: float = Field(ge=0.0, le=1.0)
    nivel_confianca: NivelConfianca
    acao: AcaoML
    modelo_versao: str


class HealthOutput(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    status: str
    model_loaded: bool
    modelo_versao: Optional[str] = None


def determinar_acao(classe: ClasseML | str, probabilidade: float) -> tuple[NivelConfianca, AcaoML]:
    """Determina o nível de confiança e a ação final com base na classe predita e na probabilidade.
    
    Regras:
    - probabilidade >= 0.85: ALTA confiança.
        - se classe == valido_automatico -> VALIDO_AUTOMATICO
        - se classe == recusar_automatico -> RECUSAR_AUTOMATICO
        - se classe == revisar -> REVISAR
    - 0.65 <= probabilidade < 0.85: MEDIA confiança e ação REVISAR.
    - probabilidade < 0.65: BAIXA confiança e ação REVISAO_PRIORITARIA.
    """
    classe_str = classe.value if isinstance(classe, ClasseML) else str(classe)

    if probabilidade >= 0.85:
        nivel = NivelConfianca.ALTA
        if classe_str == ClasseML.VALIDO_AUTOMATICO.value:
            acao = AcaoML.VALIDO_AUTOMATICO
        elif classe_str == ClasseML.RECUSAR_AUTOMATICO.value:
            acao = AcaoML.RECUSAR_AUTOMATICO
        else:
            acao = AcaoML.REVISAR
    elif probabilidade >= 0.65:
        nivel = NivelConfianca.MEDIA
        acao = AcaoML.REVISAR
    else:
        nivel = NivelConfianca.BAIXA
        acao = AcaoML.REVISAO_PRIORITARIA

    return nivel, acao
