"""Contrato unittest das regras finais e combinadas de validacao."""

from __future__ import annotations

import unittest

import pytest

from src.servico_validacao import validar_registro


def _criar_registro_base() -> dict[str, str]:
    """Helper interno para construir o contrato base de validacao."""
    return {
        "lote_id": "LG-2026-00001",
        "produto": "TV",
        "linha": "L1",
        "turno": "A",
        "status": "APROVADO",
        "responsavel": "Ana",
        "data": "15/06/2026",
        "observacao": "",
        "data_referencia": "15/06/2026",
    }


@pytest.mark.unit
class TestValidacaoRegrasFinais(unittest.TestCase):
    """Demonstra setUp, subTest e o padrao AAA pedido na Aula 23."""

    def setUp(self) -> None:
        self.lotes_referencia = {"LG-2026-00001"}
        self.registro_base = _criar_registro_base()

    def test_classificacao_de_multiplas_regras_e_casos_compostos(self) -> None:
        casos = (
            (
                "registro_valido_com_observacao_opcional",
                {"observacao": "Inspecionado sem anomalias"},
                False,
                "Válido",
                None,
            ),
            (
                "produto_e_linha_ausentes_multipla_falha",
                {"produto": "", "linha": ""},
                False,
                "Erro de Entrada",
                "RN02",
            ),
            (
                "status_ambiguo_rn09",
                {"status": "EM AJUSTE"},
                False,
                "Ambíguo",
                "RN09",
            ),
            (
                "reprovado_sem_observacao_rn10",
                {"status": "REPROVADO", "observacao": ""},
                False,
                "Divergência",
                "RN10",
            ),
            (
                "duplicado_no_dia_rn11",
                {},
                True,
                "Divergência",
                "RN11",
            ),
            (
                "lote_valido_com_espacos_nas_extremidades",
                {"lote_id": " LG-2026-00001 "},
                False,
                "Válido",
                None,
            ),
        )

        for nome, alteracoes, duplicado, classificacao, regra in casos:
            with self.subTest(cenario=nome):
                # Arrange
                dados = {**self.registro_base, **alteracoes}

                # Act
                resultado = validar_registro(
                    dados,
                    self.lotes_referencia,
                    duplicado_no_dia=duplicado,
                )

                # Assert
                self.assertEqual(resultado.classificacao, classificacao)
                if regra is None:
                    self.assertEqual(resultado.regras_aplicadas, [])
                else:
                    self.assertIn(regra, resultado.regras_aplicadas)
