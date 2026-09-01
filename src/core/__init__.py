"""Módulo de Regras de Negócio e Validações Puras (The DX Way)."""

from src.core.base_referencia import (
    carregar_base_referencia,
    verificar_existencia_lote,
)
from src.core.exceptions import (
    CoexistenceConflictError,
    DependencyTimeoutError,
    DesktopAppUnavailableError,
    FalhaInfraestruturaError,
    FalhaItemError,
    HyperautomationError,
    WebPortalUnavailableError,
)
from src.core.regras_negocio import (
    COLUNA_STATUS,
    DOMINIO_STATUS,
    normalizar_status,
    validar_dominio_status,
)
from src.core.servico_validacao import (
    CLASSIFICACOES,
    RegistroValidado,
    data_da_aba,
    texto,
    validar_registro,
)
from src.core.validacao import (
    CAMPOS_OBRIGATORIOS,
    COLUNAS_ESPERADAS,
    DATA_REFERENCIA_PADRAO,
    ErroEstrutural,
    carregar_planilha,
    valida_campos_obrigatorios,
    valida_estrutura,
    validar_data_referencia,
    validar_observacao_reprovado,
)

__all__ = [
    "carregar_base_referencia",
    "verificar_existencia_lote",
    "HyperautomationError",
    "FalhaItemError",
    "FalhaInfraestruturaError",
    "DesktopAppUnavailableError",
    "WebPortalUnavailableError",
    "DependencyTimeoutError",
    "CoexistenceConflictError",
    "ErroEstrutural",
    "COLUNA_STATUS",
    "DOMINIO_STATUS",
    "normalizar_status",
    "validar_dominio_status",
    "CLASSIFICACOES",
    "RegistroValidado",
    "data_da_aba",
    "texto",
    "validar_registro",
    "CAMPOS_OBRIGATORIOS",
    "COLUNAS_ESPERADAS",
    "DATA_REFERENCIA_PADRAO",
    "carregar_planilha",
    "valida_campos_obrigatorios",
    "valida_estrutura",
    "validar_data_referencia",
    "validar_observacao_reprovado",
]
