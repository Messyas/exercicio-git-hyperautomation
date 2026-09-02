"""Testes unitários da hierarquia de exceções (The DX Way)."""

from src.exceptions import (
    CoexistenceConflictError,
    DependencyTimeoutError,
    DesktopAppUnavailableError,
    FalhaInfraestruturaError,
    FalhaItemError,
    HyperautomationError,
)


def test_falha_item_error_estrutura():
    err = FalhaItemError(
        "Lote sem identificador",
        item_id="ITEM-01",
        campo_afetado="lote_id",
        dados_brutos={"lote_id": None, "produto": "TV"},
    )
    assert isinstance(err, HyperautomationError)
    data = err.to_dict()
    assert data["tipo_erro"] == "FALHA_ITEM"
    assert data["item_id"] == "ITEM-01"
    assert data["campo_afetado"] == "lote_id"


def test_falha_infraestrutura_error_estrutura():
    err = DesktopAppUnavailableError("Janela não encontrada", tentativa=2, max_tentativas=3)
    assert isinstance(err, FalhaInfraestruturaError)
    data = err.to_dict()
    assert data["tipo_erro"] == "FALHA_INFRAESTRUTURA"
    assert data["sistema_alvo"] == "DESKTOP_ESTOQUE"
    assert data["tentativa"] == 2


def test_dependency_timeout_error():
    err = DependencyTimeoutError("Timeout excedido")
    assert isinstance(err, FalhaInfraestruturaError)
    assert err.sistema_alvo == "SMART_OFFICE_ORCHESTRATOR"


def test_coexistence_conflict_error():
    err = CoexistenceConflictError("Conflito de sessão gráfica")
    assert isinstance(err, FalhaInfraestruturaError)
    assert err.sistema_alvo == "RUNNER_GRAPHICAL_SESSION"
