from dataclasses import dataclass
import logging
from unittest.mock import MagicMock
import pytest

from src.item_processor import ItemProcessor, MLDecision
from src.ml_client import MLPrediction


@dataclass
class DummyRegistro:
    lote_id: str
    status_original: str
    status: str
    turno: str
    observacao: str
    classificacao: str


def test_registro_nao_ambiguo_nao_chama_ml_client():
    """Registros Válidos, Divergências ou Erros de Entrada não devem acionar o cliente ML."""
    ml_client = MagicMock()
    logger = MagicMock()
    processor = ItemProcessor(ml_client, logger)

    reg_valido = DummyRegistro(
        lote_id="LOTE-001",
        status_original="APROVADO",
        status="APROVADO",
        turno="A",
        observacao="Tudo ok",
        classificacao="Válido",
    )
    res = processor.processar(reg_valido)
    assert res is None
    ml_client.classificar.assert_not_called()


def test_predicao_valida_gera_decisao_e_log():
    """Registro ambíguo com resposta válida do ML gera MLDecision e emite log estruturado."""
    ml_client = MagicMock()
    ml_client.classificar.return_value = MLPrediction(
        lote_id="LOTE-AMB-01",
        classe="valido_automatico",
        probabilidade=0.92,
        nivel_confianca="alta",
        acao="VALIDO_AUTOMATICO",
        modelo_versao="rf-lotes-1.0.0",
    )
    logger = MagicMock()
    processor = ItemProcessor(ml_client, logger)

    reg_amb = DummyRegistro(
        lote_id="LOTE-AMB-01",
        status_original="APROVADO PARCIAL",
        status="APROVADO PARCIAL",
        turno="B",
        observacao="Seguiu com desvio restrito",
        classificacao="Ambíguo",
    )

    res = processor.processar(reg_amb)
    assert res is not None
    assert res.lote_id == "LOTE-AMB-01"
    assert res.acao_final == "VALIDO_AUTOMATICO"
    assert res.tentou_rede is True
    assert res.circuit_open is False
    assert res.erro_tipo is None

    # Verifica se registrou log INFO com ML_DECISION
    logger.info.assert_called_once()
    args, kwargs = logger.info.call_args
    assert args[0] == "ML_DECISION"
    assert kwargs["extra"]["lote_id"] == "LOTE-AMB-01"
    assert kwargs["extra"]["event"] == "ML_DECISION"


def test_erro_ou_none_gera_revisao_ml_offline_e_continua():
    """Quando o MLClient retorna None, a ação deve ser REVISAO_ML_OFFLINE e o lote continua."""
    ml_client = MagicMock()
    ml_client.classificar.return_value = None
    logger = MagicMock()
    processor = ItemProcessor(ml_client, logger)

    regs = [
        DummyRegistro("LOTE-1", "PENDENTE", "PENDENTE", "A", "", "Ambíguo"),
        DummyRegistro("LOTE-2", "CANCELADO", "CANCELADO", "B", "", "Ambíguo"),
    ]

    decisoes = processor.processar_lote(regs)
    assert len(decisoes) == 2
    for dec in decisoes:
        assert dec.acao_final == "REVISAO_ML_OFFLINE"
        assert dec.classe is None
        assert dec.probabilidade is None


def test_circuito_aberto_gera_linha_para_cada_lote_restante():
    """Se o circuito estiver aberto, gera decisão REVISAO_ML_OFFLINE indicando tentou_rede=False."""
    ml_client = MagicMock()
    ml_client.circuit_breaker.is_open = True
    ml_client.classificar.return_value = None

    logger = MagicMock()
    processor = ItemProcessor(ml_client, logger)

    regs = [
        DummyRegistro("LOTE-CB-1", "PENDENTE", "PENDENTE", "A", "", "Ambíguo"),
        DummyRegistro("LOTE-CB-2", "EM AJUSTE", "EM AJUSTE", "C", "", "Ambíguo"),
    ]

    decisoes = processor.processar_lote(regs)
    assert len(decisoes) == 2
    for dec in decisoes:
        assert dec.acao_final == "REVISAO_ML_OFFLINE"
        assert dec.circuit_open is True
        assert dec.tentou_rede is False
        assert dec.erro_tipo == "circuit_open"


def test_log_nao_contem_texto_da_observacao():
    """Garantir que o texto livre da observação não vaza no log estruturado por privacidade."""
    ml_client = MagicMock()
    ml_client.classificar.return_value = MLPrediction(
        lote_id="LOTE-OBS",
        classe="revisar",
        probabilidade=0.75,
        nivel_confianca="media",
        acao="REVISAR",
        modelo_versao="rf-lotes-1.0.0",
    )
    logger = MagicMock()
    processor = ItemProcessor(ml_client, logger)

    texto_privado = "TEXTO CONFIDENCIAL DE OBSERVACAO DO LOTE DE PRODUCAO 12345"
    reg = DummyRegistro("LOTE-OBS", "PENDENTE", "PENDENTE", "A", texto_privado, "Ambíguo")

    dec = processor.processar(reg)
    assert dec is not None
    log_dict = dec.to_log_dict()

    assert texto_privado not in str(log_dict)
    assert log_dict["tem_obs"] is True
