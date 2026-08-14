"""Contrato unittest das regras finais RN09-RN12."""

from __future__ import annotations

import unittest

import pytest

from dashboard.servico_validacao import validar_registro


@pytest.mark.unit
class TestValidacaoRegrasFinais(unittest.TestCase):
    """Demonstra setUp, subTest e o padrao AAA pedido na Aula 23."""

    def setUp(self) -> None:
        self.lotes_referencia = {"LG-2026-00001"}
        self.registro_base = {
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

    def test_classificacao_de_multiplas_regras(self) -> None:
        casos = (
            ("registro_valido", {}, False, "Válido", None),
            ("status_ambiguo_rn09", {"status": "EM AJUSTE"}, False, "Ambíguo", "RN09"),
            (
                "reprovado_sem_observacao_rn10",
                {"status": "REPROVADO"},
                False,
                "Divergência",
                "RN10",
            ),
            ("duplicado_no_dia_rn11", {}, True, "Divergência", "RN11"),
            ("data_invalida_rn12", {"data": "31/02/2026"}, False, "Erro de Entrada", "RN12"),
            ("produto_ausente_rn02", {"produto": ""}, False, "Erro de Entrada", "RN02"),
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
