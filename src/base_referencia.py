"""
Módulo responsável pelo carregamento da base de referência de lotes válidos
e pela aplicação da regra de cruzamento RN03.

Regra de Negócio:
    **RN03 — Verificar Lote na Base de Referência**
    SE o ``lote_id`` de um registro da inspeção diária NÃO existir na base de
    referência (aba ``Base_Referencia`` do arquivo .xlsx), ENTÃO o registro
    deve ser classificado como divergente e encaminhado para a fila de
    exceções do analista de qualidade.
"""

import pandas as pd


# ---------------------------------------------------------------------------
# Constantes de configuração — aba Base_Referencia
# ---------------------------------------------------------------------------

_ABA_BASE_REFERENCIA: str = "Base_Referencia"

# A aba possui 1 linha de formatação (título) antes do cabeçalho real na
# linha 2 do Excel. skiprows=1 posiciona o leitor exatamente no cabeçalho.
_LINHAS_FORMATACAO_PULAR: int = 1

# Os dados úteis vão da linha 3 até a linha 25 do Excel → 23 registros
# (o lote LG-2026-00103 está intencionalmente ausente como erro controlado).
_TOTAL_IDS_REFERENCIA: int = 23

_COLUNA_LOTE_ID: str = "lote_id"


# ---------------------------------------------------------------------------
# RN03 — Carregamento da base de referência
# ---------------------------------------------------------------------------


def carregar_base_referencia(caminho_arquivo: str) -> set[str]:
    """
    Carrega os IDs válidos da aba ``Base_Referencia`` do arquivo .xlsx.

    Regra aplicada: **RN03 — Verificar Lote na Base de Referência**
    Lê a aba ``Base_Referencia``, aplica o fatiamento correto para ignorar
    as linhas de formatação do cabeçalho e retorna um ``set`` com todos os
    valores únicos da coluna ``lote_id``.

    O retorno como ``set`` garante busca em O(1) durante o cruzamento,
    otimizando a performance para grandes volumes de dados.

    Parâmetros
    ----------
    caminho_arquivo : str
        Caminho absoluto ou relativo para o arquivo .xlsx que contém a
        aba ``Base_Referencia``.

    Retorna
    -------
    set[str]
        Conjunto de strings com os ``lote_id`` válidos presentes na base
        de referência. Valores nulos são automaticamente excluídos.

    Levanta
    -------
    ValueError
        Quando a coluna ``lote_id`` não for encontrada na aba após o
        fatiamento, indicando problema de layout no arquivo.
    """
    df_referencia: pd.DataFrame = pd.read_excel(
        caminho_arquivo,
        sheet_name=_ABA_BASE_REFERENCIA,
        skiprows=_LINHAS_FORMATACAO_PULAR,
        nrows=_TOTAL_IDS_REFERENCIA,
    )

    if _COLUNA_LOTE_ID not in df_referencia.columns:
        raise ValueError(
            f"[RN03] Coluna '{_COLUNA_LOTE_ID}' não encontrada na aba "
            f"'{_ABA_BASE_REFERENCIA}'. Verifique o layout do arquivo."
        )

    ids_validos: set[str] = set(
        df_referencia[_COLUNA_LOTE_ID].dropna().astype(str).str.strip()
    )
    return ids_validos


# ---------------------------------------------------------------------------
# RN03 — Cruzamento dos lotes da inspeção com a base de referência
# ---------------------------------------------------------------------------


def verificar_existencia_lote(
    df_inspecao: pd.DataFrame,
    lotes_validos: set[str],
) -> pd.DataFrame:
    """
    Cruza os lotes da inspeção diária com a base de referência e retorna
    as linhas cujo ``lote_id`` **não** está na base (divergências RN03).

    Regra aplicada: **RN03 — Verificar Lote na Base de Referência**
    Para cada registro do DataFrame de inspeção, verifica se o ``lote_id``
    pertence ao conjunto ``lotes_validos``. Registros com ``lote_id``
    preenchido e não encontrado na base são sinalizados como divergentes
    através da coluna auxiliar ``divergencia_rn03``. Valores vazios ficam
    sob responsabilidade da RN02 para evitar dupla contagem.

    Parâmetros
    ----------
    df_inspecao : pd.DataFrame
        DataFrame da planilha de inspeção diária, já validado pelas
        regras RN01 e RN02. Deve conter a coluna ``lote_id``.
    lotes_validos : set[str]
        Conjunto de ``lote_id`` válidos retornado por
        :func:`carregar_base_referencia`.

    Retorna
    -------
    pd.DataFrame
        Subconjunto do DataFrame de inspeção contendo apenas as linhas
        divergentes (``lote_id`` ausente na base de referência). Inclui
        a coluna extra ``divergencia_rn03`` com a mensagem descritiva da
        falha. Retorna DataFrame vazio se não houver divergências.
    """
    if _COLUNA_LOTE_ID not in df_inspecao.columns:
        raise ValueError(
            f"[RN03] Coluna '{_COLUNA_LOTE_ID}' não encontrada no DataFrame "
            "de inspeção. Execute as validações RN01 e RN02 antes de RN03."
        )

    # Normaliza os IDs da inspeção para comparação robusta (strip de espaços)
    ids_originais: pd.Series = df_inspecao[_COLUNA_LOTE_ID]
    ids_inspecao: pd.Series = ids_originais.astype(str).str.strip()

    # Lote ausente já é tratado pela RN02. RN03 deve apontar apenas IDs
    # preenchidos que não existem na base, evitando dupla contagem.
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
