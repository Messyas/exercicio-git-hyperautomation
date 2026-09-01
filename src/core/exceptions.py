"""Hierarquia formal de exceções do pipeline de Hyperautomation (The DX Way).

Distingue rigorosamente:
1. `FalhaItemError`: Falhas relacionadas ao dado de entrada do item (ex.: campo nulo, formato inválido,
   lote corrompido). O item deve ir para a Dead Letter Queue após as tentativas, sem travar o pipeline.
2. `FalhaInfraestruturaError`: Falhas operacionais e de ambiente (ex.: sistema desktop fora do ar,
   queda de conexão com portal web, timeout de orquestrador). O pipeline aciona retry com backoff,
   alerta de infraestrutura e modo degradado quando aplicável.
"""

from __future__ import annotations

from typing import Any, Optional


class HyperautomationError(Exception):
    """Exceção base para o ecossistema de Hyperautomation."""


class FalhaItemError(HyperautomationError):
    """Erro originado por dados inválidos, corrompidos ou inconsistentes de um item.

    Itens com este erro são encaminhados para a Dead Letter Queue para auditoria
    e reprocessamento manual, sem abortar a execução do lote/pipeline.
    """

    def __init__(
        self,
        mensagem: str,
        *,
        item_id: Optional[str] = None,
        campo_afetado: Optional[str] = None,
        dados_brutos: Optional[dict[str, Any]] = None,
    ) -> None:
        super().__init__(mensagem)
        self.item_id = item_id or "DESCONHECIDO"
        self.campo_afetado = campo_afetado
        self.dados_brutos = dados_brutos or {}

    def to_dict(self) -> dict[str, Any]:
        return {
            "tipo_erro": "FALHA_ITEM",
            "mensagem": str(self),
            "item_id": self.item_id,
            "campo_afetado": self.campo_afetado,
            "dados_brutos": self.dados_brutos,
        }


class FalhaInfraestruturaError(HyperautomationError):
    """Erro de infraestrutura, ambiente, rede ou comunicação de sistemas.

    Dispara retries com backoff, alertas operacionais multicanal e acionamento
    de modo de contingência/degradado para manter a operação em andamento.
    """

    def __init__(
        self,
        mensagem: str,
        *,
        sistema_alvo: str = "GERAL",
        tentativa: int = 1,
        max_tentativas: int = 3,
        detalhes: Optional[dict[str, Any]] = None,
    ) -> None:
        super().__init__(mensagem)
        self.sistema_alvo = sistema_alvo
        self.tentativa = tentativa
        self.max_tentativas = max_tentativas
        self.detalhes = detalhes or {}

    def to_dict(self) -> dict[str, Any]:
        return {
            "tipo_erro": "FALHA_INFRAESTRUTURA",
            "mensagem": str(self),
            "sistema_alvo": self.sistema_alvo,
            "tentativa": self.tentativa,
            "max_tentativas": self.max_tentativas,
            "detalhes": self.detalhes,
        }


class DesktopAppUnavailableError(FalhaInfraestruturaError):
    """O sistema desktop legado não responde ou sua janela não foi localizada."""

    def __init__(self, mensagem: str = "Sistema desktop de estoque indisponível ou inacessível.", **kwargs) -> None:
        super().__init__(mensagem, sistema_alvo="DESKTOP_ESTOQUE", **kwargs)


class WebPortalUnavailableError(FalhaInfraestruturaError):
    """O portal web de fornecedores/pedidos falhou na comunicação ou autenticação."""

    def __init__(self, mensagem: str = "Portal web de fornecedores indisponível.", **kwargs) -> None:
        super().__init__(mensagem, sistema_alvo="PORTAL_WEB_FORNECEDORES", **kwargs)


class DependencyTimeoutError(FalhaInfraestruturaError):
    """Uma tarefa predecessora excedeu o tempo limite configurado no orquestrador."""

    def __init__(self, mensagem: str = "Timeout aguardando tarefa predecessora na cadeia.", **kwargs) -> None:
        super().__init__(mensagem, sistema_alvo="SMART_OFFICE_ORCHESTRATOR", **kwargs)


class CoexistenceConflictError(FalhaInfraestruturaError):
    """Conflito de sessão gráfica detectado entre múltiplos orquestradores no mesmo Runner."""

    def __init__(self, mensagem: str = "Conflito de Runner: Sessão gráfica ocupada por outro orquestrador.", **kwargs) -> None:
        super().__init__(mensagem, sistema_alvo="RUNNER_GRAPHICAL_SESSION", **kwargs)
