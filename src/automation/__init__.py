"""Módulo de Automação, Integrações RPA e Orquestração (The DX Way)."""

from src.automation.coexistence_guard import CoexistenceGuard
from src.automation.datapool_gateway import (
    BotCityDatapoolConsumer,
    BotCityDatapoolPublisher,
    LocalDatapoolConsumer,
    LocalDatapoolPublisher,
)
from src.automation.desktop_automation import DesktopAutomationClient
from src.automation.item_processor import ItemProcessor, MLDecision
from src.automation.maestro_client import (
    ExecutionResult,
    MaestroClient,
    configure_local_logging,
    write_execution_report,
)
from src.automation.orchestrator import PipelineOrchestrator
from src.automation.playwright_automation import PlaywrightAutomation
from src.automation.wait_for_predecessor import wait_for_predecessor
from src.automation.web_automation import EM_CONTAINER, iniciar_browser

__all__ = [
    "CoexistenceGuard",
    "BotCityDatapoolConsumer",
    "BotCityDatapoolPublisher",
    "LocalDatapoolConsumer",
    "LocalDatapoolPublisher",
    "DesktopAutomationClient",
    "ItemProcessor",
    "MLDecision",
    "ExecutionResult",
    "MaestroClient",
    "configure_local_logging",
    "write_execution_report",
    "PipelineOrchestrator",
    "PlaywrightAutomation",
    "wait_for_predecessor",
    "EM_CONTAINER",
    "iniciar_browser",
]
