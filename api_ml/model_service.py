import logging
from pathlib import Path
from typing import Any, Optional
import unicodedata
import joblib
import pandas as pd

from api_ml.features import FEATURE_ORDER, normalizar_status_raw
from api_ml.schemas import (
    AcaoML,
    ClasseML,
    LoteInput,
    DivergenciaInput,
    DivergenciaOutput,
    NivelConfianca,
    PredictionOutput,
    determinar_acao,
)

logger = logging.getLogger(__name__)


class ModelUnavailableError(RuntimeError):
    """Exceção lançada quando o modelo não está carregado ou indisponível."""
    pass


class ModelService:
    def __init__(self, model_path: Path):
        self.model_path = Path(model_path)
        self._pipeline: Optional[Any] = None
        self._model_version: Optional[str] = None
        self._classes: list[str] = []
        self._is_loaded: bool = False
        self._bundle: Optional[dict[str, Any]] = None

    def load(self) -> None:
        """Carrega o modelo do caminho especificado e valida o bundle."""
        if not self.model_path.exists():
            self._is_loaded = False
            raise ModelUnavailableError(f"Arquivo do modelo não encontrado: {self.model_path}")

        try:
            bundle = joblib.load(self.model_path)
            if not isinstance(bundle, dict):
                raise ValueError("Formato de bundle inválido: esperado dicionário")

            required_keys = {"pipeline", "model_version", "feature_order", "classes"}
            missing_keys = required_keys - set(bundle.keys())
            if missing_keys:
                raise ValueError(f"Chaves ausentes no bundle do modelo: {missing_keys}")

            loaded_feature_order = list(bundle["feature_order"])
            if loaded_feature_order != list(FEATURE_ORDER):
                raise ValueError(
                    f"Ordem de features incompatível. Esperado {list(FEATURE_ORDER)}, obtido {loaded_feature_order}"
                )

            self._pipeline = bundle["pipeline"]
            self._model_version = bundle["model_version"]
            self._classes = [str(c) for c in bundle["classes"]]
            self._bundle = bundle
            self._is_loaded = True
            logger.info(f"Modelo {self._model_version} carregado com sucesso de {self.model_path}")
        except Exception as e:
            self._is_loaded = False
            logger.error(f"Falha ao carregar o modelo de {self.model_path}: {e}")
            if isinstance(e, (ModelUnavailableError, ValueError)):
                raise
            raise ModelUnavailableError(f"Erro ao carregar modelo: {e}") from e

    @property
    def is_loaded(self) -> bool:
        return self._is_loaded

    @property
    def model_version(self) -> Optional[str]:
        return self._model_version

    def predict(self, lote: LoteInput) -> PredictionOutput:
        """Realiza a predição para um lote informado."""
        if not self.is_loaded or self._pipeline is None:
            raise ModelUnavailableError("Modelo de ML não está carregado ou indisponível")

        status_norm = normalizar_status_raw(lote.status_raw)
        
        # Cria DataFrame para manter colunas e tipos consistentes
        df_input = pd.DataFrame(
            [[status_norm, lote.turno, bool(lote.tem_obs)]],
            columns=list(FEATURE_ORDER),
        )

        try:
            probas = self._pipeline.predict_proba(df_input)[0]
            
            # Identifica a classe com maior probabilidade
            max_idx = int(probas.argmax())
            best_proba = float(probas[max_idx])
            best_class_raw = self._classes[max_idx]

            # Converte a classe para o Enum ClasseML se possível
            classe_enum = ClasseML(best_class_raw)
            nivel_confianca, acao = determinar_acao(classe_enum, best_proba)

            return PredictionOutput(
                lote_id=lote.lote_id,
                classe=classe_enum,
                probabilidade=round(best_proba, 4),
                nivel_confianca=nivel_confianca,
                acao=acao,
                modelo_versao=self._model_version or "unknown",
            )
        except Exception as e:
            logger.error(f"Erro durante predição para lote {lote.lote_id}: {e}")
            raise RuntimeError(f"Erro interno no processamento de predição: {e}") from e

    def classify_divergence(self, lote: DivergenciaInput) -> DivergenciaOutput:
        """Classifica a observação livre com um mock NLP determinístico.

        O enunciado S10-B permite um mock controlável. Esta implementação é
        intencionalmente pequena e transparente para demonstração: a sugestão
        é derivada exclusivamente do texto do operador e jamais altera o
        resultado das RN01--RN03/RN01--RN07.
        """
        if not self.is_loaded:
            raise ModelUnavailableError("Modelo de ML não está carregado ou indisponível")

        texto = unicodedata.normalize("NFKD", lote.observacao)
        texto = "".join(char for char in texto if not unicodedata.combining(char)).lower()
        regras = (
            (("duplic", "repet", "lancamento duplic"), "duplicidade_lancamento", 0.94),
            (("digita", "codigo incorreto", "codigo errado", "digitei errado"), "erro_digitacao_codigo", 0.92),
            (("falt", "peca", "doca"), "divergencia_quantidade_pecas", 0.89),
            (("avaria", "quebrad", "danific"), "avaria_produto", 0.87),
        )
        for termos, causa, confianca in regras:
            if any(termo in texto for termo in termos):
                return DivergenciaOutput(
                    lote_id=lote.lote_id,
                    causa_provavel=causa,
                    probabilidade=confianca,
                    modelo_versao="s10b-text-mock-1.0.0",
                )
        return DivergenciaOutput(
            lote_id=lote.lote_id,
            causa_provavel="nao_classificado",
            probabilidade=0.45,
            modelo_versao="s10b-text-mock-1.0.0",
        )
