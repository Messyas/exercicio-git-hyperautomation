"""Exercicio 19-X: oito testes do formulario Next.js com Chromium real."""

from __future__ import annotations

from pathlib import Path

import pytest


pytestmark = pytest.mark.e2e


class TestFormularioCadastroLotes:
    def test_pagina_carrega_com_titulo_correto(self, formulario_page) -> None:
        assert "Cadastro de Lotes" in formulario_page.page.title()

    def test_campo_numero_lote_aceita_entrada(self, formulario_page) -> None:
        formulario_page.preencher_lote("LT-2026-0001")
        assert formulario_page.campo_lote.input_value() == "LT-2026-0001"

    def test_dropdown_produto_aceita_selecao(self, formulario_page) -> None:
        formulario_page.selecionar_produto("TV55-4K-B")
        assert formulario_page.campo_produto.input_value() == "TV55-4K-B"

    def test_status_aprovado_selecionado_por_padrao(self, formulario_page) -> None:
        assert formulario_page.obter_status_selecionado() == "APROVADO"

    def test_formulario_completo_exibe_sucesso(self, formulario_page) -> None:
        formulario_page.preencher_lote("LT-2026-9999")
        formulario_page.selecionar_produto("MON27-QHD")
        formulario_page.selecionar_status("APROVADO")
        formulario_page.submeter()
        assert formulario_page.mensagem_sucesso_visivel()

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
