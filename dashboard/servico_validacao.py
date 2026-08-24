"""Serviço de Validação RN01–RN12 usado pelo relatório executivo.

Este módulo concentra a decisão de negócio. O gerador do relatório apenas
consolida as planilhas, identifica as repetições de cada dia e chama
``validar_registro`` uma vez para cada linha.
"""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Mapping

import pandas as pd

from src.regras_negocio import normalizar_status, validar_dominio_status
from src.validacao import validar_observacao_reprovado


CLASSIFICACOES = ("Válido", "Divergência", "Ambíguo", "Erro de Entrada")
ABAS_DIARIAS = re.compile(r"^Insp_(\d{2})_(\d{2})_(\d{4})$")


def texto(valor: Any) -> str:
    """Converte valores da planilha sem transformar nulos no texto ``nan``."""
    return "" if pd.isna(valor) else str(valor).strip()


def data_da_aba(nome_aba: str) -> str:
    """Converte ``Insp_DD_MM_AAAA`` na data de referência do registro."""
    correspondencia = ABAS_DIARIAS.fullmatch(nome_aba)
    if not correspondencia:
        raise ValueError(f"Nome de aba diária inválido: {nome_aba}")
    dia, mes, ano = correspondencia.groups()
    data_texto = f"{dia}/{mes}/{ano}"
    try:
        return datetime.strptime(data_texto, "%d/%m/%Y").strftime("%d/%m/%Y")
    except ValueError as exc:
        raise ValueError(f"Data inválida no nome da aba: {nome_aba}") from exc


def _data_valida(valor: Any, referencia: str) -> bool:
    """RN12: exige data preenchida, em DD/MM/AAAA e igual à execução."""
    valor_texto = texto(valor)
    if not re.fullmatch(r"\d{2}/\d{2}/\d{4}", valor_texto):
        return False
    try:
        return datetime.strptime(valor_texto, "%d/%m/%Y").strftime(
            "%d/%m/%Y"
        ) == referencia
    except ValueError:
        return False


@dataclass
class RegistroValidado:
    """Resultado auditável de uma chamada a :func:`validar_registro`."""

    lote_id: str
    produto: str
    linha: str
    turno: str
    status: str
    responsavel: str
    data: str
    observacao: str
    data_referencia: str
    status_original: str = ""
    regras_aplicadas: list[str] = field(default_factory=list)
    orientacoes: list[str] = field(default_factory=list)
    classificacao: str = "Válido"

    def adicionar(self, regra: str, orientacao: str) -> None:
        """Registra uma regra uma única vez e conserva sua orientação."""
        if regra not in self.regras_aplicadas:
            self.regras_aplicadas.append(regra)
            self.orientacoes.append(orientacao)

    def to_dict(self) -> dict[str, Any]:
        """Converte o objeto para o formato consumido pelo pandas."""
        return {
            "lote_id": self.lote_id,
            "produto": self.produto,
            "linha": self.linha,
            "turno": self.turno,
            "status_original": self.status_original,
            "status_normalizado": self.status,
            "responsavel": self.responsavel,
            "data": self.data,
            "data_referencia": self.data_referencia,
            "observacao": self.observacao,
            "regras_aplicadas": "; ".join(self.regras_aplicadas),
            "descricao_validacao": " | ".join(self.orientacoes),
            "classificacao": self.classificacao,
        }


def validar_registro(
    dados: Mapping[str, Any],
    lotes_referencia: set[str],
    *,
    duplicado_no_dia: bool = False,
) -> RegistroValidado:
    """Aplica RN01–RN12 a uma linha e retorna um ``RegistroValidado``.

    A precedência garante uma classificação exclusiva: Erro de Entrada,
    Ambíguo, Divergência e Válido. ``duplicado_no_dia`` deve ser calculado
    antes desta chamada com um ``Counter`` isolado por execução diária.
    """
    status_original = texto(dados.get("status"))
    normalizado = normalizar_status({"status": dados.get("status")})
    status_final = texto(normalizado.get("status")).upper()

    registro = RegistroValidado(
        lote_id=texto(dados.get("lote_id")),
        produto=texto(dados.get("produto")),
        linha=texto(dados.get("linha")),
        turno=texto(dados.get("turno")),
        status=status_final,
        responsavel=texto(dados.get("responsavel")),
        data=texto(dados.get("data")),
        observacao=texto(dados.get("observacao")),
        data_referencia=texto(dados.get("data_referencia")),
        status_original=status_original,
    )

    campos_obrigatorios = (
        ("lote_id", "RN01"),
        ("produto", "RN02"),
        ("linha", "RN03"),
        # O serviço-base da Aula 22 também trata os campos operacionais
        # de identificação como obrigatórios. O dataset do exercício possui
        # dois responsáveis vazios que fazem parte dos 30 erros do gabarito.
        ("turno", "RN04"),
        ("status_original", "RN04"),
        ("responsavel", "RN04"),
    )
    for campo, regra in campos_obrigatorios:
        if not getattr(registro, campo):
            registro.adicionar(regra, f"Campo obrigatório vazio: {campo}.")

    if not _data_valida(registro.data, registro.data_referencia):
        registro.adicionar(
            "RN12",
            f"Data deve ser {registro.data_referencia} no formato DD/MM/AAAA.",
        )

    if registro.lote_id and registro.lote_id not in lotes_referencia:
        registro.adicionar("RN05", "lote_id não encontrado na Base_Referencia.")

    status_original_canonico = status_original.upper()
    if status_original_canonico == "OK":
        registro.adicionar("RN06", "Status OK normalizado para APROVADO.")
    elif status_original_canonico == "NOK":
        registro.adicionar("RN07", "Status NOK normalizado para REPROVADO.")

    if status_original:
        dominio = validar_dominio_status({"status": status_final})
        if dominio.get("status_ambiguo", False):
            registro.adicionar(
                "RN09",
                f"Status '{status_final}' desconhecido; encaminhar para revisão humana.",
            )

    observacao = validar_observacao_reprovado(
        {"status": status_final, "observacao": registro.observacao}
    )
    if observacao.get("divergencias"):
        registro.adicionar(
            "RN10", "Status REPROVADO exige observação preenchida."
        )

    if duplicado_no_dia:
        registro.adicionar(
            "RN11", "lote_id duplicado na mesma execução diária."
        )

    regras = set(registro.regras_aplicadas)
    if regras.intersection({"RN01", "RN02", "RN03", "RN04", "RN12"}):
        registro.classificacao = "Erro de Entrada"
    elif "RN09" in regras:
        registro.classificacao = "Ambíguo"
    elif regras.intersection({"RN05", "RN10", "RN11"}):
        registro.classificacao = "Divergência"

    return registro


def validar_registros_lista(
    df: pd.DataFrame, lotes_referencia: set[str]
) -> list[RegistroValidado]:
    """Deduplica por dia e aplica RN01–RN12 para cada linha de um DataFrame.

    Retorna a lista preservada de ``RegistroValidado`` sem converter para DataFrame.
    """
    repetidos: set[int] = set()
    for _, diario in df.groupby("aba_origem", sort=False):
        ids = [texto(valor) for valor in diario["lote_id"]]
        contador = Counter(lote_id for lote_id in ids if lote_id)
        vistos: Counter[str] = Counter()
        for indice, lote_id in zip(diario.index, ids):
            vistos[lote_id] += 1
            if lote_id and contador[lote_id] > 1 and vistos[lote_id] > 1:
                repetidos.add(indice)

    validados: list[RegistroValidado] = []
    for indice, linha in df.iterrows():
        registro = validar_registro(
            linha.to_dict(),
            lotes_referencia,
            duplicado_no_dia=indice in repetidos,
        )
        validados.append(registro)
    return validados
