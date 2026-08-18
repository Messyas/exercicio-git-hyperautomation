"""Testes de degradação elegante para o marcador de término do pipeline."""

import logging

import consumer
import pipeline


def _raise_permission_error(_path):
    raise PermissionError("volume sem permissão de escrita")


def test_sinalizacao_do_consumer_nao_invalida_execucao_por_permissao(monkeypatch, caplog):
    monkeypatch.setenv("SHUTDOWN_FILE", "pipeline-finished")
    monkeypatch.setattr(consumer.Path, "touch", _raise_permission_error)

    with caplog.at_level(logging.WARNING, logger="botcity.validador"):
        consumer._signal_pipeline_finished()

    assert "Não foi possível registrar o marcador de término" in caplog.text


def test_sinalizacao_final_nao_sobrescreve_resultado_por_permissao(monkeypatch, caplog):
    monkeypatch.setenv("SHUTDOWN_FILE", "pipeline-finished")
    monkeypatch.setattr(pipeline.Path, "touch", _raise_permission_error)

    with caplog.at_level(logging.WARNING, logger="botcity.pipeline"):
        pipeline._signal_finished()

    assert "Não foi possível registrar o marcador de término" in caplog.text
