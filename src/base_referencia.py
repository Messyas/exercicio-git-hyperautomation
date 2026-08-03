"""Carregamento da base de lotes e validação da RN03."""

import re

import pandas as pd


_ABA_BASE_REFERENCIA: str = "Base_Referencia"

# A primeira linha da aba contém o título, antes do cabeçalho da tabela.
_LINHAS_FORMATACAO_PULAR: int = 1

_COLUNA_LOTE_ID: str = "lote_id"


def carregar_base_referencia(caminho_arquivo: str) -> set[str]:
    """Retorna os IDs válidos da aba ``Base_Referencia``."""
    arquivo_excel = pd.ExcelFile(caminho_arquivo)
    try:
        apresentacao = pd.read_excel(
            arquivo_excel,
            sheet_name=_ABA_BASE_REFERENCIA,
            header=None,
            nrows=1,
        )
        texto_apresentacao = " ".join(
            apresentacao.fillna("").astype(str).to_numpy().ravel()
        )
        match_total = re.search(
            r"Registros:\s*(\d+)",
            texto_apresentacao,
            flags=re.IGNORECASE,
        )
        total_declarado = int(match_total.group(1)) if match_total else None
        df_referencia: pd.DataFrame = pd.read_excel(
            arquivo_excel,
            sheet_name=_ABA_BASE_REFERENCIA,
            skiprows=_LINHAS_FORMATACAO_PULAR,
            nrows=total_declarado,
        )
    finally:
        arquivo_excel.close()

    if _COLUNA_LOTE_ID not in df_referencia.columns:
        raise ValueError(
            f"[RN03] Coluna '{_COLUNA_LOTE_ID}' não encontrada na aba "
            f"'{_ABA_BASE_REFERENCIA}'. Verifique o layout do arquivo."
        )

    ids_validos: set[str] = set(
        df_referencia[_COLUNA_LOTE_ID].dropna().astype(str).str.strip()
    )
    return ids_validos


def verificar_existencia_lote(
    df_inspecao: pd.DataFrame,
    lotes_validos: set[str],
) -> pd.DataFrame:
    """Retorna os lotes preenchidos que não existem na base de referência."""
    if _COLUNA_LOTE_ID not in df_inspecao.columns:
        raise ValueError(
            f"[RN03] Coluna '{_COLUNA_LOTE_ID}' não encontrada no DataFrame "
            "de inspeção. Execute as validações RN01 e RN02 antes de RN03."
        )

    ids_originais: pd.Series = df_inspecao[_COLUNA_LOTE_ID]
    ids_inspecao: pd.Series = ids_originais.astype(str).str.strip()

    # Valores vazios são tratados pela RN02.
    lote_preenchido: pd.Series = ids_originais.notna() & ids_inspecao.ne("")
    mascara_ausente: pd.Series = lote_preenchido & ~ids_inspecao.isin(
        lotes_validos
    )

    linhas_divergentes: pd.DataFrame = df_inspecao[mascara_ausente].copy()

    if linhas_divergentes.empty:
        return linhas_divergentes

    linhas_divergentes["divergencia_rn03"] = linhas_divergentes[
        _COLUNA_LOTE_ID
    ].apply(
        lambda lote_id: (
            f"[RN03] lote_id '{lote_id}' não encontrado na base de referência."
        )
    )

    return linhas_divergentes.reset_index(drop=False)
