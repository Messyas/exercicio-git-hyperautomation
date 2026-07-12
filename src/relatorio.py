"""Exportação do relatório de divergências do processo.

O arquivo segue o modelo de saída do PDD v0.2 (seções 9 e 15): uma planilha
``.xlsx`` para o Analista de Qualidade, contendo cada falha classificada pela
regra violada, sua descrição e a ação recomendada.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd


COLUNAS_RELATORIO: tuple[str, ...] = (
    "lote_id",
    "regra_violada",
    "descricao_do_erro",
    "acao_recomendada",
    "severidade",
)


def _valor_descricao(erro: Mapping[str, Any]) -> str:
    """Obtém a descrição em formatos usados pelas regras RN02 a RN07."""
    descricao = erro.get("descricao_do_erro") or erro.get("descricao")
    if descricao:
        return str(descricao)

    for coluna in (
        "divergencia_rn02",
        "divergencia_rn03",
        "divergencia_rn04",
        "divergencia_rn05",
        "divergencia_rn06",
        "divergencia_rn07",
    ):
        valor = erro.get(coluna)
        if valor:
            return str(valor)

    if erro.get("campos_vazios"):
        return f"Campos obrigatórios vazios: {erro['campos_vazios']}"

    return "Divergência sem descrição informada."


def _valor_regra(erro: Mapping[str, Any]) -> str:
    """Obtém o identificador da regra em formatos planos ou auxiliares."""
    regra = erro.get("regra_violada") or erro.get("regra")
    if regra:
        return str(regra)

    for coluna in (
        "divergencia_rn02",
        "divergencia_rn03",
        "divergencia_rn04",
        "divergencia_rn05",
        "divergencia_rn06",
        "divergencia_rn07",
    ):
        if erro.get(coluna):
            return coluna.removeprefix("divergencia_").upper()

    if erro.get("campos_vazios"):
        return "RN02"
    return "NÃO CLASSIFICADA"


def _iterar_erros(erros: Iterable[Mapping[str, Any]]) -> Iterable[dict[str, Any]]:
    """Achata erros planos e divergências acumuladas dentro de um registro."""
    for erro in erros:
        if not isinstance(erro, Mapping):
            raise TypeError("Cada divergência deve ser representada por um dicionário.")

        lote_id = erro.get("lote_id", "")
        divergencias = erro.get("divergencias")

        if divergencias:
            for divergencia in divergencias:
                if not isinstance(divergencia, Mapping):
                    raise TypeError("Cada item de 'divergencias' deve ser um dicionário.")
                yield {"lote_id": lote_id, **divergencia}
        else:
            yield dict(erro)


def _linha_relatorio(erro: Mapping[str, Any]) -> dict[str, Any]:
    """Converte uma divergência do motor para o modelo de saída do PDD."""
    return {
        "lote_id": erro.get("lote_id", ""),
        "regra_violada": _valor_regra(erro),
        "descricao_do_erro": _valor_descricao(erro),
        "acao_recomendada": erro.get("acao_recomendada", "Encaminhar ao analista"),
        "severidade": erro.get("severidade", "Média"),
    }


def _caminho_disponivel(caminho_base: Path) -> Path:
    """Evita sobrescrever um relatório já gerado no mesmo dia."""
    if not caminho_base.exists():
        return caminho_base

    contador = 2
    while True:
        candidato = caminho_base.with_name(
            f"{caminho_base.stem}_{contador}{caminho_base.suffix}"
        )
        if not candidato.exists():
            return candidato
        contador += 1


def gerar_relatorio_divergencias(
    erros: Iterable[Mapping[str, Any]],
    diretorio_saida: str | Path = ".",
) -> Path:
    """Consolida as falhas RN02–RN07 e exporta o relatório em ``.xlsx``.

    O modelo de saída do PDD v0.2 (seções 9 e 15) exige as colunas
    ``lote_id``, ``regra_violada``, ``descricao_do_erro`` e recomenda incluir
    a ação para o Analista de Qualidade. A data no nome segue o formato
    ``DDMMAAAA``; quando já existir um relatório do mesmo dia, um sufixo
    numérico é acrescentado para preservar o arquivo anterior.

    Parâmetros
    ----------
    erros : Iterable[Mapping[str, Any]]
        Lista de erros planos ou registros contendo a chave
        ``divergencias`` com os erros acumulados pelas regras.
    diretorio_saida : str ou Path, opcional
        Diretório onde o relatório será criado. Ele é criado caso não exista.

    Retorna
    -------
    Path
        Caminho do arquivo ``relatorio_divergencias_DDMMAAAA.xlsx`` gerado.
    """
    diretorio = Path(diretorio_saida)
    diretorio.mkdir(parents=True, exist_ok=True)

    linhas = [_linha_relatorio(erro) for erro in _iterar_erros(erros)]
    tabela = pd.DataFrame(linhas, columns=COLUNAS_RELATORIO)

    data_execucao = datetime.now().strftime("%d%m%Y")
    caminho_base = diretorio / f"relatorio_divergencias_{data_execucao}.xlsx"
    caminho_saida = _caminho_disponivel(caminho_base)
    tabela.to_excel(caminho_saida, index=False, sheet_name="divergencias")
    return caminho_saida
