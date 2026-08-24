"""Exportação do relatório de divergências do processo.

O arquivo segue o modelo de saída do PDD v0.2 (seções 9 e 15): uma planilha
``.xlsx`` para o Analista de Qualidade, contendo cada falha classificada pela
regra violada, sua descrição e a ação recomendada.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

import pandas as pd

from src.time_utils import now_local


COLUNAS_RELATORIO: tuple[str, ...] = (
    "lote_id",
    "regra_violada",
    "descricao_do_erro",
    "acao_recomendada",
    "severidade",
    "origem_decisao",
    "confianca_ml",
    "causa_provavel_ml",
)


COLUNAS_ERROS_FLUXO: tuple[str, ...] = (
    "item_id",
    "source_row",
    "lote_id",
    "produto",
    "linha",
    "turno",
    "status",
    "responsavel",
    "data",
    "observacao",
    "cadastro_status",
    "cadastro_error",
    "cadastro_error_type",
    "evidence_name",
    "evidence_path",
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
        "origem_decisao": erro.get("origem_decisao", "fallback"),
        "confianca_ml": erro.get("confianca_ml", 0.0),
        "causa_provavel_ml": erro.get("causa_provavel_ml", "nao_classificado"),
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


def gerar_relatorio_erros_fluxo(
    erros: Iterable[Mapping[str, Any]],
    diretorio_saida: str | Path,
) -> Path:
    """Registra itens que o Bot 1 não publicou no DataPool."""
    registros = [dict(erro) for erro in erros]
    if not registros:
        raise ValueError("O relatório de erros de fluxo exige ao menos um item.")

    diretorio = Path(diretorio_saida)
    diretorio.mkdir(parents=True, exist_ok=True)
    data_execucao = now_local().strftime("%d%m%Y")
    caminho = _caminho_disponivel(
        diretorio / f"relatorio_erros_fluxo_produtor_{data_execucao}.xlsx"
    )
    tabela = pd.DataFrame(registros).reindex(columns=COLUNAS_ERROS_FLUXO)
    resumo = pd.DataFrame(
        [
            {"metrica": "total_erros_fluxo", "valor": len(tabela)},
            {
                "metrica": "cadastros_rejeitados",
                "valor": int(
                    tabela["cadastro_status"].eq("REJEITADO_NEGOCIO").sum()
                ),
            },
            {
                "metrica": "falhas_tecnicas",
                "valor": int(
                    tabela["cadastro_status"].eq("FALHA_TECNICA").sum()
                ),
            },
        ]
    )
    with pd.ExcelWriter(caminho, engine="openpyxl") as escritor:
        resumo.to_excel(escritor, index=False, sheet_name="resumo")
        tabela.to_excel(escritor, index=False, sheet_name="erros_fluxo")
    return caminho


def gerar_relatorio_divergencias(
    erros: Iterable[Mapping[str, Any]],
    diretorio_saida: str | Path = ".",
    lotes_validados: pd.DataFrame | Iterable[Mapping[str, Any]] | None = None,
    revisao_humana: pd.DataFrame | Iterable[Mapping[str, Any]] | None = None,
    rejeicoes_cadastro: Iterable[Mapping[str, Any]] | None = None,
    falhas_tecnicas: Iterable[Mapping[str, Any]] | None = None,
    resumo: Mapping[str, Any] | None = None,
) -> Path:
    """Consolida as falhas RN02-RN07 e exporta o relatório em ``.xlsx``.

    O modelo de saída do PDD v0.2 (seções 9 e 15) exige as colunas
    ``lote_id``, ``regra_violada``, ``descricao_do_erro`` e recomenda incluir
    a ação para o Analista de Qualidade. O arquivo também contém as abas
    ``lotes_validados`` e ``revisao_humana``. A data no nome segue o formato
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

    data_execucao = now_local().strftime("%d%m%Y")
    caminho_base = diretorio / f"relatorio_divergencias_{data_execucao}.xlsx"
    caminho_saida = _caminho_disponivel(caminho_base)
    if lotes_validados is None:
        tabela_validos = pd.DataFrame(
            columns=["lote_id", "status", "data", "observacao"]
        )
    elif isinstance(lotes_validados, pd.DataFrame):
        tabela_validos = lotes_validados.copy()
    else:
        tabela_validos = pd.DataFrame(lotes_validados)

    if revisao_humana is None:
        tabela_revisao = pd.DataFrame(
            columns=[
                "lote_id",
                "status_original",
                "status",
                "data",
                "descricao_do_erro",
                "observacao_analista",
            ]
        )
    elif isinstance(revisao_humana, pd.DataFrame):
        tabela_revisao = revisao_humana.copy()
    else:
        tabela_revisao = pd.DataFrame(revisao_humana)

    tabela_rejeicoes = pd.DataFrame(
        list(rejeicoes_cadastro or []),
        columns=[
            "item_id",
            "source_row",
            "lote_id",
            "cadastro_status",
            "cadastro_error",
            "evidence_name",
            "evidence_path",
        ],
    )
    tabela_falhas = pd.DataFrame(
        list(falhas_tecnicas or []),
        columns=[
            "item_id",
            "source_row",
            "lote_id",
            "cadastro_status",
            "cadastro_error",
            "evidence_name",
            "evidence_path",
        ],
    )
    resumo_final = dict(resumo or {})
    resumo_final.setdefault("total_divergencias", len(tabela))
    resumo_final.setdefault("total_lotes_validados", len(tabela_validos))
    resumo_final.setdefault("total_revisao_humana", len(tabela_revisao))
    resumo_final.setdefault("total_rejeicoes_cadastro", len(tabela_rejeicoes))
    resumo_final.setdefault("total_falhas_tecnicas", len(tabela_falhas))
    tabela_resumo = pd.DataFrame(
        [
            {"metrica": chave, "valor": valor}
            for chave, valor in resumo_final.items()
        ],
        columns=["metrica", "valor"],
    )

    with pd.ExcelWriter(caminho_saida, engine="openpyxl") as escritor:
        tabela_resumo.to_excel(escritor, index=False, sheet_name="resumo")
        tabela.to_excel(escritor, index=False, sheet_name="divergencias")
        tabela_validos.to_excel(escritor, index=False, sheet_name="lotes_validados")
        tabela_rejeicoes.to_excel(
            escritor, index=False, sheet_name="rejeicoes_cadastro"
        )
        tabela_falhas.to_excel(
            escritor, index=False, sheet_name="falhas_tecnicas"
        )
        tabela_revisao.to_excel(escritor, index=False, sheet_name="revisao_humana")
    return caminho_saida
