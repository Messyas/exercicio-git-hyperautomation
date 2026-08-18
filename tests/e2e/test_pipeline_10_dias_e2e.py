"""E2E local: dez abas de entrada até as evidências finais do dashboard (Aula 24)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import openpyxl
import pandas as pd
import pytest

from dashboard.gerar_relatorio import gerar_relatorio


pytestmark = [pytest.mark.e2e, pytest.mark.slow]


def test_pipeline_completo_bate_com_o_gabarito_sem_dependencia_externa(
    planilha_10_dias_factory,
    mock_base_referencia: MagicMock,
    instante_fixo_manaus,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    # Arrange
    entrada, referencias, _ = planilha_10_dias_factory()
    mock_base_referencia.return_value = referencias

    monkeypatch.setattr(
        "dashboard.main.carregar_base_referencia",
        mock_base_referencia,
    )
    monkeypatch.setattr(
        "dashboard.main._agora_manaus",
        lambda: instante_fixo_manaus,
    )
    saida = tmp_path / "saida"

    # Act
    caminho_relatorio = gerar_relatorio(entrada, saida)

    # Assert
    mock_base_referencia.assert_called_once_with(entrada)
    assert caminho_relatorio == saida / "relatorio_conferencia_lotes.xlsx"
    assert caminho_relatorio.exists()
    assert (saida / "resumo_executivo.md").exists()
    assert (saida / "resumo_conferencia_lotes.pdf").read_bytes().startswith(b"%PDF")
    assert "30/06/2026 08:15:00 -0400" in (
        saida / "execucao_dashboard.log"
    ).read_text(encoding="utf-8")

    with pd.ExcelFile(caminho_relatorio) as excel:
        assert excel.sheet_names == [
            "Resumo",
            "Todos",
            "Válidos",
            "Divergências",
            "Ambíguos",
            "Erros de Entrada",
            "Ranking de Regras",
            "Dicionário",
            "Decisões de ML",
        ]

        todos = pd.read_excel(excel, sheet_name="Todos")
        assert todos["Classificação"].value_counts().to_dict() == {
            "Válido": 150,
            "Divergência": 50,
            "Erro de Entrada": 30,
            "Ambíguo": 20,
        }
        assert not todos["Status"].isin(["OK", "NOK"]).any()

    workbook = openpyxl.load_workbook(caminho_relatorio, data_only=True)
    assert workbook["Resumo"]["B3"].value == 250

    # Gabarito do Resumo Executivo Markdown
    texto_md = (saida / "resumo_executivo.md").read_text(encoding="utf-8")
    assert "250 registros" in texto_md
    assert "150 (60,0%)" in texto_md
    assert "50 (20,0%)" in texto_md
    assert "20 (8,0%)" in texto_md
    assert "30 (12,0%)" in texto_md
    assert "## Destaque" in texto_md
    assert "437,5 minutos" in texto_md
    assert "7h17min30s" in texto_md
    assert "estimativa didática" in texto_md
