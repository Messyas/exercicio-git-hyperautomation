"""Exercicio 19-X: oito testes do formulario Next.js com Chromium real."""

from __future__ import annotations

import os
from pathlib import Path
from uuid import uuid4

import pytest


pytestmark = [
    pytest.mark.e2e,
    pytest.mark.browser,
    pytest.mark.slow,
    pytest.mark.skipif(
        os.getenv("RUN_BROWSER_E2E") != "1",
        reason=(
            "E2E de browser opcional: defina RUN_BROWSER_E2E=1 e disponibilize "
            "Chromium/frontend"
        ),
    ),
]


class TestFormularioCadastroLotes:
    def test_pagina_carrega_com_titulo_correto(self, formulario_page) -> None:
        assert "Cadastro de Lotes" in formulario_page.page.title()

    def test_campo_numero_lote_aceita_entrada(self, formulario_page) -> None:
        formulario_page.preencher_lote("LT-2026-0001")
        assert formulario_page.campo_lote.input_value() == "LT-2026-0001"

    def test_dropdown_produto_aceita_selecao(self, formulario_page) -> None:
        formulario_page.selecionar_produto("TV55-4K-B")
        assert formulario_page.campo_produto.input_value() == "TV55-4K-B"

    def test_status_aprovado_preenchido_por_padrao(self, formulario_page) -> None:
        assert formulario_page.obter_status_selecionado() == "APROVADO"

    def test_selecionar_status_marca_radio_button_correto(
        self, formulario_page
    ) -> None:
        formulario_page.selecionar_status("NOK")
        assert formulario_page.obter_status_selecionado() == "NOK"

    def test_formulario_completo_exibe_sucesso(self, formulario_page) -> None:
        registro = {
            "lote_id": f"LT-E2E-{uuid4().hex[:8].upper()}",
            "produto": "MON27-QHD",
            "linha": "L2",
            "turno": "B",
            "status": "NOK",
            "responsavel": "Ana Ferreira",
            "data": "14/06/2026",
            "observacao": "Defeito visual",
        }
        formulario_page.preencher_lote(registro["lote_id"])
        formulario_page.selecionar_produto(registro["produto"])
        formulario_page.selecionar_status(registro["status"])
        formulario_page.preencher_e_enviar(registro)
        assert formulario_page.mensagem_sucesso_visivel()
        assert formulario_page.obter_ultimo_cadastro() == registro

    def test_submissao_sem_produto_nao_exibe_sucesso(
        self, formulario_page
    ) -> None:
        formulario_page.preencher_lote("LT-2026-0002")
        formulario_page.submeter()
        assert not formulario_page.mensagem_sucesso_visivel()

    def test_submissao_sem_numero_lote_nao_exibe_sucesso(
        self, formulario_page
    ) -> None:
        formulario_page.selecionar_produto("AC12-SPLIT")
        formulario_page.submeter()
        assert not formulario_page.mensagem_sucesso_visivel()

    def test_screenshot_capturado_como_evidencia(
        self,
        formulario_page,
        e2e_screenshot_dir: Path,
    ) -> None:
        path = e2e_screenshot_dir / "evidencia_formulario.png"
        formulario_page.capturar_evidencia(path)
        assert path.exists()
        assert path.stat().st_size > 0
