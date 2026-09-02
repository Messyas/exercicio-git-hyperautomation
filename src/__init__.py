"""Pacote Raiz do Projeto (The DX Way).

Subpacotes canônicos:
- `src.core`: Regras de negócio determinísticas e validações estruturais
- `src.automation`: Automação Web/Desktop, DataPool, Maestro e CoexistenceGuard
- `src.ml`: Classificador de divergência e clientes de Machine Learning
- `src.reporting`: Relatórios executivos, despachante de alertas e indicadores
- `src.utils`: Resiliência, Dead Letter, parsing Excel, logging e time utils
- `src.runners`: Executáveis e processos do Produtor, Consumidor, Coletor e Pipeline
- `src.scripts`: Scripts de simulação, torneio, smoke test e auditoria
"""

from __future__ import annotations

import importlib
import sys

_MODULE_MAPPING: dict[str, str] = {
    # utils (sem dependencias)
    "time_utils": "src.utils.time_utils",
    "resilience": "src.utils.resilience",
    "structured_logging": "src.utils.structured_logging",
    "dead_letter": "src.utils.dead_letter",
    "excel_source": "src.utils.excel_source",
    # core (depende de utils)
    "exceptions": "src.core.exceptions",
    "base_referencia": "src.core.base_referencia",
    "regras_negocio": "src.core.regras_negocio",
    "validacao": "src.core.validacao",
    "servico_validacao": "src.core.servico_validacao",
    # ml
    "ml_client": "src.ml.ml_client",
    "ml_client_factory": "src.ml.ml_client_factory",
    "classificador_divergencia": "src.ml.classificador_divergencia",
    # automation
    "coexistence_guard": "src.automation.coexistence_guard",
    "datapool_gateway": "src.automation.datapool_gateway",
    "desktop_automation": "src.automation.desktop_automation",
    "item_processor": "src.automation.item_processor",
    "maestro_client": "src.automation.maestro_client",
    "orchestrator": "src.automation.orchestrator",
    "playwright_automation": "src.automation.playwright_automation",
    "wait_for_predecessor": "src.automation.wait_for_predecessor",
    "web_automation": "src.automation.web_automation",
    # reporting
    "gmail_client": "src.reporting.gmail_client",
    "operational_indicators": "src.reporting.operational_indicators",
    "relatorio": "src.reporting.relatorio",
    "relatorio_executivo": "src.reporting.relatorio_executivo",
    "sistema_alertas": "src.reporting.sistema_alertas",
    # runners
    "coletor": "src.runners.coletor",
    "consumer": "src.runners.consumer",
    "pipeline": "src.runners.pipeline",
    "producer": "src.runners.producer",
    "bot": "src.runners.bot",
}

for _sub, _target in _MODULE_MAPPING.items():
    _mod = importlib.import_module(_target)
    sys.modules[f"src.{_sub}"] = _mod
    globals()[_sub] = _mod
