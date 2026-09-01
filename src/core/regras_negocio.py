"""Regras de negócio relacionadas à coluna ``status``.

Este módulo implementa as regras RN04 (validação do domínio de status) e
RN05 (normalização dos valores não canônicos ``OK`` e ``NOK``). Os registros
que não puderem ser classificados automaticamente permanecem sem alteração
e são identificados como casos ambíguos para revisão humana.
"""

from __future__ import annotations

from collections.abc import MutableMapping
from typing import Any, TypeVar, overload

import pandas as pd


COLUNA_STATUS = "status"
DOMINIO_STATUS = frozenset({"APROVADO", "REPROVADO", "PENDENTE"})

_T = TypeVar("_T")


def _status_canonico(valor: Any) -> str | Any:
    """Retorna uma representação comparável do status sem converter nulos."""
    if pd.isna(valor):
        return valor
    return str(valor).strip().upper()


def _normalizar_registro(registro: MutableMapping[str, Any]) -> MutableMapping[str, Any]:
    """Aplica RN05 a um registro representado por um mapeamento."""
    if COLUNA_STATUS not in registro:
        raise ValueError("[RN05] O registro não possui a coluna 'status'.")

    status_original = registro[COLUNA_STATUS]
    status = _status_canonico(status_original)
    registro.setdefault("status_original", status_original)

    if status == "OK":
        registro[COLUNA_STATUS] = "APROVADO"
        mensagem = "[RN05] Status 'OK' normalizado para 'APROVADO'."
    elif status == "NOK":
        registro[COLUNA_STATUS] = "REPROVADO"
        mensagem = "[RN05] Status 'NOK' normalizado para 'REPROVADO'."
    else:
        mensagem = None

    registro["divergencia_rn05"] = mensagem
    return registro


@overload
def normalizar_status(status: pd.DataFrame) -> pd.DataFrame: ...


@overload
def normalizar_status(status: MutableMapping[str, Any]) -> MutableMapping[str, Any]: ...


def normalizar_status(
    status: pd.DataFrame | MutableMapping[str, Any],
) -> pd.DataFrame | MutableMapping[str, Any]:
    """Normaliza os status conhecidos e registra a divergência de padronização.

    Regra aplicada: RN05 - Normalização. ``OK`` é convertido para
    ``APROVADO`` e ``NOK`` para ``REPROVADO``. Toda linha convertida recebe a
    mensagem em ``divergencia_rn05`` e conserva o valor de entrada em
    ``status_original`` para rastreabilidade. Valores desconhecidos não são
    decididos automaticamente; eles ficam para a validação RN04/RN06.

    Parâmetros
    ----------
    status : pd.DataFrame ou MutableMapping
        DataFrame com a coluna ``status`` ou um registro representado por
        dicionário.

    Retorna
    -------
    pd.DataFrame ou MutableMapping
        Cópia normalizada do DataFrame ou o registro atualizado.
    """
    if isinstance(status, pd.DataFrame):
        if COLUNA_STATUS not in status.columns:
            raise ValueError("[RN05] DataFrame não possui a coluna 'status'.")

        resultado = status.copy()
        resultado["status_original"] = resultado[COLUNA_STATUS]
        valores = resultado[COLUNA_STATUS].map(_status_canonico)
        resultado[COLUNA_STATUS] = valores.replace(
            {"OK": "APROVADO", "NOK": "REPROVADO"}
        )
        resultado["divergencia_rn05"] = pd.NA
        resultado.loc[valores == "OK", "divergencia_rn05"] = (
            "[RN05] Status 'OK' normalizado para 'APROVADO'."
        )
        resultado.loc[valores == "NOK", "divergencia_rn05"] = (
            "[RN05] Status 'NOK' normalizado para 'REPROVADO'."
        )
        return resultado

    if isinstance(status, MutableMapping):
        return _normalizar_registro(status)

    raise TypeError("[RN05] 'status' deve ser um DataFrame ou um registro.")


def _validar_registro(registro: MutableMapping[str, Any]) -> MutableMapping[str, Any]:
    """Aplica RN04 a um registro e separa status não reconhecidos."""
    if COLUNA_STATUS not in registro:
        raise ValueError("[RN04] O registro não possui a coluna 'status'.")

    valor = registro[COLUNA_STATUS]
    status = _status_canonico(valor)
    if status not in DOMINIO_STATUS:
        registro["divergencia_rn04"] = (
            f"[RN04] Status '{valor}' fora do domínio permitido."
        )
        registro["status_ambiguo"] = True
        registro["fila_destino"] = "revisao_humana"
    else:
        registro["divergencia_rn04"] = None
        registro["status_ambiguo"] = False
    return registro


def validar_dominio_status(
    status: pd.DataFrame | MutableMapping[str, Any],
) -> pd.DataFrame | MutableMapping[str, Any]:
    """Valida se o status final pertence ao domínio permitido.

    Regra aplicada: RN04 - Validação de Domínio. Após a RN05, somente
    ``APROVADO``, ``REPROVADO`` e ``PENDENTE`` são válidos. As linhas fora do
    domínio são retornadas como divergências, marcadas em
    ``status_ambiguo`` e direcionadas para ``revisao_humana`` (RN06), sem
    decisão automática sobre o valor original.

    Parâmetros
    ----------
    status : pd.DataFrame ou MutableMapping
        DataFrame ou registro contendo a coluna/chave ``status``. A função
        deve ser executada depois de :func:`normalizar_status`.

    Retorna
    -------
    pd.DataFrame ou MutableMapping
        Registros ambíguos no caso de DataFrame, ou o registro atualizado no
        caso de mapeamento. Um DataFrame sem divergências é retornado vazio.
    """
    if isinstance(status, pd.DataFrame):
        if COLUNA_STATUS not in status.columns:
            raise ValueError("[RN04] DataFrame não possui a coluna 'status'.")

        status_canonicos = status[COLUNA_STATUS].map(_status_canonico)
        mascara_ambiguos = ~status_canonicos.isin(DOMINIO_STATUS)
        divergencias = status.loc[mascara_ambiguos].copy()

        if divergencias.empty:
            return divergencias

        divergencias["divergencia_rn04"] = divergencias[COLUNA_STATUS].map(
            lambda valor: f"[RN04] Status '{valor}' fora do domínio permitido."
        )
        divergencias["status_ambiguo"] = True
        divergencias["fila_destino"] = "revisao_humana"
        return divergencias.reset_index(drop=False)

    if isinstance(status, MutableMapping):
        return _validar_registro(status)

    raise TypeError("[RN04] 'status' deve ser um DataFrame ou um registro.")

