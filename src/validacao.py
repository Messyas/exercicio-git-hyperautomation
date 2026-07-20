"""
Módulo de validação primária da planilha de inspeção de lotes.

Responsável por aplicar as regras de negócio RN01 (Validação de Estrutura)
e RN02 (Validação de Campos Obrigatórios) sobre o DataFrame ingerido
a partir do arquivo inspecao_lotes_dia.xlsx.
"""

import pandas as pd


# ---------------------------------------------------------------------------
# Constantes de configuração
# ---------------------------------------------------------------------------

COLUNAS_ESPERADAS: list[str] = [
    "lote_id",
    "produto",
    "linha",
    "turno",
    "status",
    "responsavel",
    "data",
    "observacao",
]

CAMPOS_OBRIGATORIOS: list[str] = [
    "lote_id",
    "produto",
    "linha",
    "turno",
    "status",
    "responsavel",
    "data",
]

# Linha Excel onde o cabeçalho começa (base 0 para skiprows):
# Linha 1 e 2 são formatação → skiprows=2 pula para o cabeçalho na linha 3.
# nrows=25 captura exatamente os registros úteis (linhas 4–28 do Excel).
_LINHAS_CABECALHO_PULAR: int = 2
_TOTAL_REGISTROS_UTEIS: int = 25
DATA_REFERENCIA_PADRAO: str = "14/06/2026"


# ---------------------------------------------------------------------------
# Exceções personalizadas
# ---------------------------------------------------------------------------


class ErroEstrutural(Exception):
    """Exceção levantada quando a planilha não possui a estrutura esperada (RN01)."""


# ---------------------------------------------------------------------------
# Ingestão da planilha
# ---------------------------------------------------------------------------


def carregar_planilha(caminho_arquivo: str) -> pd.DataFrame:
    """
    Carrega a planilha de inspeção de lotes aplicando o fatiamento correto.

    A planilha possui 2 linhas de cabeçalho de formatação antes dos nomes
    reais das colunas. O fatiamento garante que apenas os registros úteis
    (linhas 4 a 28 do Excel, ou seja, 25 registros) sejam lidos.

    Parâmetros
    ----------
    caminho_arquivo : str
        Caminho absoluto ou relativo para o arquivo .xlsx.

    Retorna
    -------
    pd.DataFrame
        DataFrame com os 25 registros da planilha, utilizando os nomes
        de coluna definidos na linha 3 do Excel.
    """
    arquivo_excel = pd.ExcelFile(caminho_arquivo)
    try:
        return pd.read_excel(
            arquivo_excel,
            sheet_name=0,
            skiprows=_LINHAS_CABECALHO_PULAR,
            nrows=_TOTAL_REGISTROS_UTEIS,
        )
    finally:
        arquivo_excel.close()


# ---------------------------------------------------------------------------
# RN01 — Validação de Estrutura
# ---------------------------------------------------------------------------


def valida_estrutura(df: pd.DataFrame) -> None:
    """
    Valida se o DataFrame possui exatamente as 8 colunas obrigatórias.

    Regra aplicada: **RN01 — Validação de Estrutura**
    SE a planilha não possuir exatamente 8 colunas (lote_id, produto, linha,
    turno, status, responsavel, data, observacao), ENTÃO interromper execução
    e levantar ErroEstrutural com descrição das colunas ausentes.

    Parâmetros
    ----------
    df : pd.DataFrame
        DataFrame carregado da planilha de inspeção.

    Levanta
    -------
    ErroEstrutural
        Quando uma ou mais colunas obrigatórias estiverem ausentes.
    """
    colunas_presentes: set[str] = set(df.columns)
    colunas_obrigatorias: set[str] = set(COLUNAS_ESPERADAS)

    colunas_ausentes: set[str] = colunas_obrigatorias - colunas_presentes
    colunas_extras: set[str] = colunas_presentes - colunas_obrigatorias

    if colunas_ausentes or colunas_extras:
        detalhes: list[str] = []
        if colunas_ausentes:
            detalhes.append(
                "Colunas ausentes: " + ", ".join(sorted(colunas_ausentes))
            )
        if colunas_extras:
            detalhes.append(
                "Colunas extras: " + ", ".join(sorted(colunas_extras))
            )
        raise ErroEstrutural(f"[RN01] Estrutura inválida. {'; '.join(detalhes)}")


# ---------------------------------------------------------------------------
# RN02 — Validação de Campos Obrigatórios
# ---------------------------------------------------------------------------


def valida_campos_obrigatorios(df: pd.DataFrame) -> pd.DataFrame:
    """
    Detecta e retorna as linhas que possuem campos obrigatórios vazios.

    Regra aplicada: **RN02 — Validação de Campos Obrigatórios**
    SE qualquer campo obrigatório (lote_id, produto, linha, turno, status,
    responsavel, data) estiver vazio (NaN/Null), ENTÃO registrar a linha
    como divergência e incluí-la no resultado para encaminhamento à fila
    de exceções.

    Parâmetros
    ----------
    df : pd.DataFrame
        DataFrame com a estrutura validada por RN01.

    Retorna
    -------
    pd.DataFrame
        Subconjunto do DataFrame original contendo apenas as linhas com
        ao menos um campo obrigatório vazio. Inclui a coluna extra
        ``campos_vazios`` com os nomes dos campos ausentes em cada linha.
        Retorna DataFrame vazio se não houver divergências.
    """
    def _campo_vazio(valor: object) -> bool:
        if pd.isna(valor):
            return True
        return isinstance(valor, str) and not valor.strip()

    # RN02 trata tanto células nulas quanto strings vazias como ausentes.
    mascara_com_vazio: pd.Series = df[CAMPOS_OBRIGATORIOS].map(
        _campo_vazio
    ).any(axis=1)

    linhas_divergentes: pd.DataFrame = df[mascara_com_vazio].copy()

    if linhas_divergentes.empty:
        return linhas_divergentes

    # Adiciona coluna informativa com os campos específicos que estão vazios
    def _listar_campos_vazios(linha: pd.Series) -> str:
        campos: list[str] = [
            campo
            for campo in CAMPOS_OBRIGATORIOS
            if _campo_vazio(linha[campo])
        ]
        return ", ".join(campos)

    linhas_divergentes["campos_vazios"] = linhas_divergentes.apply(
        _listar_campos_vazios, axis=1
    )

    return linhas_divergentes.reset_index(drop=False)


def validar_data_referencia(
    df: pd.DataFrame,
    data_referencia: str = DATA_REFERENCIA_PADRAO,
) -> pd.DataFrame:
    """Detecta datas preenchidas fora da data de referência do processo.

    Regra complementar documentada no PDD como RN01: registros preenchidos
    com data diferente da data de referência devem ser encaminhados como
    divergência de dados. Datas vazias permanecem sob responsabilidade da
    RN02, evitando que o mesmo registro seja contado duas vezes por esse
    motivo.
    """
    if "data" not in df.columns:
        raise ValueError("[RN01] DataFrame não possui a coluna 'data'.")

    referencia = pd.to_datetime(data_referencia, dayfirst=True, errors="raise")
    datas = pd.to_datetime(df["data"], dayfirst=True, errors="coerce")
    preenchida = df["data"].notna() & df["data"].astype(str).str.strip().ne("")
    mascara_fora_referencia = preenchida & (datas.isna() | datas.ne(referencia))

    linhas_divergentes = df.loc[mascara_fora_referencia].copy()
    if linhas_divergentes.empty:
        return linhas_divergentes

    linhas_divergentes["divergencia_rn01"] = linhas_divergentes["data"].apply(
        lambda valor: (
            f"[RN01] Data '{valor}' fora da referência '{data_referencia}'."
        )
    )
    return linhas_divergentes.reset_index(drop=False)


def validar_observacao_reprovado(registro: dict) -> dict:
    """
    Valida a observação obrigatória para status REPROVADO (RN07).

    A função mantém o registro e acumula a divergência na chave
    ``divergencias``, permitindo que o resultado seja combinado com as
    demais regras de negócio.
    """
    status = str(registro.get("status", "")).strip().upper()
    observacao_original = registro.get("observacao", "")
    observacao_vazia = pd.isna(observacao_original) or (
        isinstance(observacao_original, str)
        and not observacao_original.strip()
    )

    registro.setdefault("divergencias", [])

    if status == "REPROVADO" and observacao_vazia:
        registro["divergencias"].append(
            {
                "regra_violada": "RN07",
                "descricao": "Status REPROVADO exige preenchimento da observação.",
                "acao_recomendada": "Encaminhar ao analista para preenchimento",
                "severidade": "Alta",
            }
        )

    return registro
