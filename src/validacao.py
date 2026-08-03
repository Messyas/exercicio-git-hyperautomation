"""Validação da estrutura e dos campos da planilha de lotes."""

import re

import pandas as pd


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

# As duas primeiras linhas da planilha são usadas para formatação.
_LINHAS_CABECALHO_PULAR: int = 2
DATA_REFERENCIA_PADRAO: str = "14/06/2026"


class ErroEstrutural(Exception):
    """Exceção levantada quando a planilha não possui a estrutura esperada (RN01)."""


def carregar_planilha(caminho_arquivo: str) -> pd.DataFrame:
    """Carrega os registros úteis da planilha de inspeção."""
    arquivo_excel = pd.ExcelFile(caminho_arquivo)
    try:
        apresentacao = pd.read_excel(
            arquivo_excel,
            sheet_name=0,
            header=None,
            nrows=2,
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
        registros = pd.read_excel(
            arquivo_excel,
            sheet_name=0,
            skiprows=_LINHAS_CABECALHO_PULAR,
            nrows=total_declarado,
        )
        return registros.dropna(how="all").reset_index(drop=True)
    finally:
        arquivo_excel.close()


def valida_estrutura(df: pd.DataFrame) -> None:
    """Valida se o DataFrame possui exatamente as colunas esperadas."""
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


def valida_campos_obrigatorios(df: pd.DataFrame) -> pd.DataFrame:
    """Retorna as linhas que possuem campos obrigatórios vazios."""
    def _campo_vazio(valor: object) -> bool:
        if pd.isna(valor):
            return True
        return isinstance(valor, str) and not valor.strip()

    mascara_com_vazio: pd.Series = df[CAMPOS_OBRIGATORIOS].map(
        _campo_vazio
    ).any(axis=1)

    linhas_divergentes: pd.DataFrame = df[mascara_com_vazio].copy()

    if linhas_divergentes.empty:
        return linhas_divergentes

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
    """Retorna registros preenchidos fora da data de referência."""
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
    """Registra a RN07 quando um lote reprovado não tem observação."""
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
