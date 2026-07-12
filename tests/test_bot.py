"""Testes end-to-end do fluxo inicial do bot."""

import json

import pandas as pd

from bot import executar_bot


ARQUIVO_AMOSTRA = "data/samples/inspecao_lotes_dia.xlsx"


def test_executar_bot_produz_evidencias_do_pdd(tmp_path) -> None:
    """A planilha de exemplo deve cumprir os números do PDD v0.2."""
    resultado = executar_bot(ARQUIVO_AMOSTRA, tmp_path)

    assert resultado["status_execucao"] == "SUCESSO"
    assert resultado["total_registros"] == 25
    assert resultado["total_divergencias"] == 9
    assert resultado["total_regras_violadas"] == 10
    assert resultado["total_lotes_validados"] == 16
    assert resultado["total_revisao_humana"] == 2

    with pd.ExcelFile(resultado["relatorio"]) as arquivo:
        assert set(arquivo.sheet_names) == {
            "divergencias",
            "lotes_validados",
            "revisao_humana",
        }
        divergencias = pd.read_excel(arquivo, sheet_name="divergencias")
        validos = pd.read_excel(arquivo, sheet_name="lotes_validados")
        revisao = pd.read_excel(arquivo, sheet_name="revisao_humana")

    assert len(divergencias) == 9
    assert {"lote_id", "regra_violada", "descricao_do_erro"}.issubset(
        divergencias.columns
    )
    assert len(validos) == 16
    assert len(revisao) == 2
    assert "LG-2026-00115" in divergencias["lote_id"].tolist()
    assert any(
        "RN05" in regra and "RN07" in regra
        for regra in divergencias["regra_violada"]
    )

    log = json.loads(resultado["log"].read_text(encoding="utf-8"))
    assert log["status_execucao"] == "SUCESSO"
    assert log["total_registros"] == 25
    assert log["total_divergencias"] == 9
    assert len(log["hash_md5"]) == 32
    assert log["timestamp_inicio"]
    assert log["timestamp_fim"]


def test_arquivo_ausente_gera_log_de_erro(tmp_path) -> None:
    """O bot deve encerrar com ERRO_ARQUIVO sem tentar validar registros."""
    resultado = executar_bot(tmp_path / "ausente.xlsx", tmp_path / "saida")

    assert resultado["status_execucao"] == "ERRO_ARQUIVO"
    assert resultado["relatorio"] is None
    log = json.loads(resultado["log"].read_text(encoding="utf-8"))
    assert log["status_execucao"] == "ERRO_ARQUIVO"


def test_estrutura_invalida_gera_log_de_erro(tmp_path, monkeypatch) -> None:
    """O bot deve interromper antes das regras quando RN01 falhar."""
    entrada = pd.DataFrame({"status": ["APROVADO"]})
    caminho_entrada = tmp_path / "entrada.xlsx"
    caminho_entrada.touch()
    monkeypatch.setattr("bot.carregar_planilha", lambda _: entrada)

    resultado = executar_bot(caminho_entrada, tmp_path / "saida")

    assert resultado["status_execucao"] == "ERRO_ESTRUTURA"
    assert resultado["relatorio"] is None
    log = json.loads(resultado["log"].read_text(encoding="utf-8"))
    assert log["status_execucao"] == "ERRO_ESTRUTURA"
