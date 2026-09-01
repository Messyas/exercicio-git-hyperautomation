"""Módulo puro para cálculo de indicadores operacionais (Aula 24).

Este módulo calcula os dez indicadores da solução sem depender de bibliotecas
externas de apresentação ou processamento de dados (pandas, openpyxl, etc.).
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Iterable, Sequence

if TYPE_CHECKING:
    from src.core.servico_validacao import RegistroValidado


CLASSIFICACOES_VALIDAS = frozenset(
    {"Válido", "Divergência", "Ambíguo", "Erro de Entrada"}
)

CATALOGO_REGRAS: dict[str, str] = {
    "RN01": "Lote obrigatório",
    "RN02": "Produto obrigatório",
    "RN03": "Linha obrigatória",
    "RN04": "Campos operacionais obrigatórios",
    "RN05": "Lote ausente da Base de Referência",
    "RN06": "Normalização de OK para APROVADO",
    "RN07": "Normalização de NOK para REPROVADO",
    "RN08": "Status canônico aceito, sem ocorrência registrada",
    "RN09": "Status desconhecido encaminhado à revisão humana",
    "RN10": "Reprovado sem observação",
    "RN11": "Lote duplicado no mesmo dia",
    "RN12": "Data inválida ou diferente da referência diária",
}


@dataclass(frozen=True)
class RankedRule:
    """Representa uma regra ranqueada por número de ocorrências."""

    codigo: str
    nome: str
    ocorrencias: int
    percentual_total: float


@dataclass(frozen=True)
class OperationalIndicators:
    """Estrutura consolidada dos dez indicadores operacionais da Aula 24."""

    total_registros: int
    registros_validos: int
    percentual_validos: float
    divergencias: int
    percentual_divergencias: float
    ambiguos: int
    percentual_ambiguos: float
    erros_entrada: int
    percentual_erros_entrada: float
    regra_mais_acionada: RankedRule | None
    taxa_qualidade_entrada: float
    taxa_revisao_humana: float
    taxa_retrabalho: float
    tempo_manual_minutos: float
    tempo_automatizado_minutos: float
    ganho_estimado_minutos: float
    ranking_regras: tuple[RankedRule, ...]


def _percentual(parte: int, total: int) -> float:
    """Calcula a porcentagem como um número entre 0 e 100."""
    if total <= 0:
        return 0.0
    return (parte / total) * 100.0


def calcular_indicadores(
    registros: Sequence[Any],
    *,
    tempo_manual_minutos: float = 2.0,
    tempo_automatizado_minutos: float = 0.25,
) -> OperationalIndicators:
    """Calcula os dez indicadores operacionais a partir da lista validada."""
    if tempo_manual_minutos < 0 or tempo_automatizado_minutos < 0:
        raise ValueError("Os tempos de processamento não podem ser negativos.")
    if tempo_automatizado_minutos > tempo_manual_minutos:
        raise ValueError(
            "O tempo automatizado não pode ser superior ao tempo manual."
        )

    registros_lista = list(registros)
    total_registros = len(registros_lista)

    classificacoes_counter: Counter[str] = Counter()
    rule_counts: Counter[str] = Counter()

    for reg in registros_lista:
        classificacao = getattr(reg, "classificacao", None)
        if classificacao not in CLASSIFICACOES_VALIDAS:
            raise ValueError(
                f"Classificação desconhecida encontrada: {classificacao}"
            )

        classificacoes_counter[classificacao] += 1

        regras_aplicadas = getattr(reg, "regras_aplicadas", ())
        for regra in regras_aplicadas:
            rule_counts[regra] += 1

    registros_validos = classificacoes_counter["Válido"]
    divergencias = classificacoes_counter["Divergência"]
    ambiguos = classificacoes_counter["Ambíguo"]
    erros_entrada = classificacoes_counter["Erro de Entrada"]

    percentual_validos = _percentual(registros_validos, total_registros)
    percentual_divergencias = _percentual(divergencias, total_registros)
    percentual_ambiguos = _percentual(ambiguos, total_registros)
    percentual_erros_entrada = _percentual(erros_entrada, total_registros)

    taxa_qualidade_entrada = _percentual(
        total_registros - erros_entrada, total_registros
    )
    taxa_revisao_humana = _percentual(ambiguos, total_registros)
    taxa_retrabalho = _percentual(divergencias, total_registros)

    ganho_estimado_minutos = total_registros * (
        tempo_manual_minutos - tempo_automatizado_minutos
    )

    ranking_list: list[RankedRule] = []
    # Counter preserva a ordem da primeira ocorrência em empates de contagem.
    for code, ocorrencias in rule_counts.most_common():
        nome = CATALOGO_REGRAS.get(code, f"Regra {code}")
        pct_total = _percentual(ocorrencias, total_registros)
        ranking_list.append(
            RankedRule(
                codigo=code,
                nome=nome,
                ocorrencias=ocorrencias,
                percentual_total=pct_total,
            )
        )

    ranking_regras = tuple(ranking_list)
    regra_mais_acionada = ranking_regras[0] if ranking_regras else None

    return OperationalIndicators(
        total_registros=total_registros,
        registros_validos=registros_validos,
        percentual_validos=percentual_validos,
        divergencias=divergencias,
        percentual_divergencias=percentual_divergencias,
        ambiguos=ambiguos,
        percentual_ambiguos=percentual_ambiguos,
        erros_entrada=erros_entrada,
        percentual_erros_entrada=percentual_erros_entrada,
        regra_mais_acionada=regra_mais_acionada,
        taxa_qualidade_entrada=taxa_qualidade_entrada,
        taxa_revisao_humana=taxa_revisao_humana,
        taxa_retrabalho=taxa_retrabalho,
        tempo_manual_minutos=tempo_manual_minutos,
        tempo_automatizado_minutos=tempo_automatizado_minutos,
        ganho_estimado_minutos=ganho_estimado_minutos,
        ranking_regras=ranking_regras,
    )
