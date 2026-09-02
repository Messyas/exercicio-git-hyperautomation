"""Testes unitários da automação desktop (The DX Way)."""

import pytest
from src.desktop_automation import DesktopAutomationClient
from src.exceptions import DesktopAppUnavailableError


def test_desktop_automation_consulta_sucesso():
    client = DesktopAutomationClient()
    assert client.conectar_sistema_desktop() is True
    res = client.consultar_lote("LOTE-001")
    assert res["encontrado"] is True
    assert res["produto"] == "TV 55 OLED"
    assert res["saldo_fisico"] == 150


def test_desktop_automation_lote_inexistente():
    client = DesktopAutomationClient()
    res = client.consultar_lote("LOTE-INEXISTENTE-999")
    assert res["encontrado"] is False
    assert res["status_estoque"] == "NAO_ENCONTRADO"


def test_desktop_automation_falha_com_retry_e_excecao():
    client_sabotado = DesktopAutomationClient(max_retries=2, backoff_seconds=0.01, force_fail=True)
    with pytest.raises(DesktopAppUnavailableError):
        client_sabotado.conectar_sistema_desktop()

    with pytest.raises(DesktopAppUnavailableError):
        client_sabotado.consultar_lote("LOTE-001")
