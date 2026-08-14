"""
Testes unitários para o módulo src/validacao.py.

Cobrem as regras de negócio:
- RN01: Validação de Estrutura (valida_estrutura)
- RN02: Validação de Campos Obrigatórios (valida_campos_obrigatorios)

Utiliza DataFrames simulados (mock) para isolamento completo dos testes,
sem dependência do arquivo real inspecao_lotes_dia.xlsx.
"""

import pandas as pd
import pytest

from src.validacao import (
    CAMPOS_OBRIGATORIOS,
    COLUNAS_ESPERADAS,
    ErroEstrutural,
    valida_campos_obrigatorios,
    valida_estrutura,
    validar_data_referencia,
    validar_observacao_reprovado,
)


pytestmark = pytest.mark.unit


# Fixtures reutilizáveis


@pytest.fixture
def df_valido() -> pd.DataFrame:
    """
    Retorna um DataFrame com estrutura completa e todos os campos obrigatórios
    preenchidos e sem divergências.
    """
    return pd.DataFrame(
        {
            "lote_id": ["LG-2026-00101", "LG-2026-00102", "LG-2026-00103"],
            "produto": ["TV55-4K-B", "MON27-QHD", "AC12-SPLIT"],
            "linha": ["L1", "L2", "L3"],
            "turno": ["A", "B", "A"],
            "status": ["APROVADO", "APROVADO", "REPROVADO"],
            "responsavel": ["Carlos Menezes", "Ana Ferreira", "Roberta Lima"],
            "data": ["14/06/2026", "14/06/2026", "14/06/2026"],
            "observacao": [None, None, "Defeito detectado"],
        }
    )


@pytest.fixture
def df_sem_coluna_status(df_valido: pd.DataFrame) -> pd.DataFrame:
    """DataFrame sem a coluna 'status'."""
    return df_valido.drop(columns=["status"])


@pytest.fixture
def df_sem_multiplas_colunas(df_valido: pd.DataFrame) -> pd.DataFrame:
    """DataFrame sem as colunas 'status' e 'responsavel'."""
    return df_valido.drop(columns=["status", "responsavel"])


@pytest.fixture
def df_com_responsavel_vazio(df_valido: pd.DataFrame) -> pd.DataFrame:
    """DataFrame com 'responsavel' nulo na segunda linha."""
    df = df_valido.copy()
    df.loc[1, "responsavel"] = None
    return df


@pytest.fixture
def df_com_lote_id_vazio(df_valido: pd.DataFrame) -> pd.DataFrame:
    """DataFrame com 'lote_id' nulo na primeira linha."""
    df = df_valido.copy()
    df.loc[0, "lote_id"] = None
    return df


@pytest.fixture
def df_com_status_vazio(df_valido: pd.DataFrame) -> pd.DataFrame:
    """DataFrame com 'status' nulo na terceira linha."""
    df = df_valido.copy()
    df.loc[2, "status"] = None
    return df


@pytest.fixture
def df_com_multiplos_vazios() -> pd.DataFrame:
    """
    DataFrame com múltiplos campos obrigatórios vazios em linhas diferentes,
    incluindo uma linha com dois campos ausentes simultaneamente.
    """
    return pd.DataFrame(
        {
            "lote_id": [None, "LG-2026-00202", "LG-2026-00203"],
            "produto": ["TV55-4K-B", "MON27-QHD", "AC12-SPLIT"],
            "linha": ["L1", "L2", "L3"],
            "turno": ["A", None, "C"],
            "status": ["APROVADO", "PENDENTE", "REPROVADO"],
            "responsavel": [None, "Ana Ferreira", "Roberta Lima"],
            "data": ["14/06/2026", "14/06/2026", None],
            "observacao": [None, None, "Defeito detectado"],
        }
    )


# RN01: valida_estrutura


class TestValidaEstrutura:
    """Testes para a função valida_estrutura (RN01)."""

    def test_caminho_feliz_estrutura_completa(self, df_valido: pd.DataFrame) -> None:
        """
        [RN01] Caminho feliz: DataFrame com todas as 8 colunas obrigatórias
        não deve levantar exceção.
        """
        # Não deve lançar nenhuma exceção
        valida_estrutura(df_valido)

    def test_erro_quando_coluna_status_ausente(
        self, df_sem_coluna_status: pd.DataFrame
    ) -> None:
        """
        [RN01] Deve levantar ErroEstrutural quando a coluna 'status' estiver
        ausente.
        """
        with pytest.raises(ErroEstrutural) as info_excecao:
            valida_estrutura(df_sem_coluna_status)

        mensagem = str(info_excecao.value)
        assert "RN01" in mensagem
        assert "status" in mensagem

    def test_erro_quando_multiplas_colunas_ausentes(
        self, df_sem_multiplas_colunas: pd.DataFrame
    ) -> None:
        """
        [RN01] Deve levantar ErroEstrutural e listar todas as colunas ausentes
        quando mais de uma coluna obrigatória estiver faltando.
        """
        with pytest.raises(ErroEstrutural) as info_excecao:
            valida_estrutura(df_sem_multiplas_colunas)

        mensagem = str(info_excecao.value)
        assert "RN01" in mensagem
        assert "status" in mensagem
        assert "responsavel" in mensagem

    def test_erro_dataframe_vazio_sem_colunas(self) -> None:
        """
        [RN01] Deve levantar ErroEstrutural para um DataFrame completamente
        vazio (sem nenhuma coluna).
        """
        df_vazio = pd.DataFrame()
        with pytest.raises(ErroEstrutural):
            valida_estrutura(df_vazio)

    def test_colunas_esperadas_constante_contem_8_itens(self) -> None:
        """
        [RN01] A constante COLUNAS_ESPERADAS deve possuir exatamente 8 itens,
        conforme especificado no PDD.
        """
        assert len(COLUNAS_ESPERADAS) == 8

    def test_rejeita_coluna_extra(self, df_valido: pd.DataFrame) -> None:
        """RN01 deve aceitar exatamente as oito colunas previstas."""
        df_com_extra = df_valido.assign(coluna_extra="valor")

        with pytest.raises(ErroEstrutural, match="Colunas extras"):
            valida_estrutura(df_com_extra)


# RN02: valida_campos_obrigatorios


class TestValidaCamposObrigatorios:
    """Testes para a função valida_campos_obrigatorios (RN02)."""

    def test_caminho_feliz_sem_campos_vazios(self, df_valido: pd.DataFrame) -> None:
        """
        [RN02] Caminho feliz: DataFrame sem campos obrigatórios vazios deve
        retornar um DataFrame vazio (sem divergências).
        """
        resultado = valida_campos_obrigatorios(df_valido)
        assert resultado.empty, "Não deveria haver linhas com campos vazios."

    def test_detecta_responsavel_vazio(
        self, df_com_responsavel_vazio: pd.DataFrame
    ) -> None:
        """
        [RN02] Deve detectar e retornar a linha com campo 'responsavel' nulo.
        Caso de teste baseado em EX-2026-00109 do PDD.
        """
        resultado = valida_campos_obrigatorios(df_com_responsavel_vazio)

        assert not resultado.empty, "Deveria detectar ao menos 1 linha com campo vazio."
        assert len(resultado) == 1
        assert "responsavel" in resultado["campos_vazios"].iloc[0]

    def test_detecta_lote_id_vazio(
        self, df_com_lote_id_vazio: pd.DataFrame
    ) -> None:
        """
        [RN02] Deve detectar e retornar a linha com campo 'lote_id' nulo.
        Caso de teste baseado na linha 27 (idx 26) do arquivo real (lote_id ausente).
        """
        resultado = valida_campos_obrigatorios(df_com_lote_id_vazio)

        assert not resultado.empty, "Deveria detectar ao menos 1 linha com campo vazio."
        assert len(resultado) == 1
        assert "lote_id" in resultado["campos_vazios"].iloc[0]

    def test_detecta_status_vazio(
        self, df_com_status_vazio: pd.DataFrame
    ) -> None:
        """
        [RN02] Deve detectar e retornar a linha com campo 'status' nulo.
        """
        resultado = valida_campos_obrigatorios(df_com_status_vazio)

        assert not resultado.empty, "Deveria detectar ao menos 1 linha com campo vazio."
        assert len(resultado) == 1
        assert "status" in resultado["campos_vazios"].iloc[0]

    def test_detecta_multiplos_campos_vazios_em_linhas_diferentes(
        self, df_com_multiplos_vazios: pd.DataFrame
    ) -> None:
        """
        [RN02] Deve detectar todas as linhas com campos obrigatórios vazios,
        incluindo linhas com mais de um campo ausente simultaneamente.
        """
        resultado = valida_campos_obrigatorios(df_com_multiplos_vazios)

        # 3 linhas têm campos vazios: linha 0 (lote_id e responsavel),
        # linha 1 (turno) e linha 2 (data)
        assert len(resultado) == 3

    def test_coluna_campos_vazios_lista_campos_corretos(
        self, df_com_multiplos_vazios: pd.DataFrame
    ) -> None:
        """
        [RN02] A coluna auxiliar 'campos_vazios' deve listar corretamente os
        campos ausentes de cada linha divergente.
        """
        resultado = valida_campos_obrigatorios(df_com_multiplos_vazios)

        linha_0 = resultado[resultado["index"] == 0].iloc[0]
        assert "lote_id" in linha_0["campos_vazios"]
        assert "responsavel" in linha_0["campos_vazios"]

        linha_1 = resultado[resultado["index"] == 1].iloc[0]
        assert "turno" in linha_1["campos_vazios"]

        linha_2 = resultado[resultado["index"] == 2].iloc[0]
        assert "data" in linha_2["campos_vazios"]

    def test_observacao_vazia_nao_e_divergencia_rn02(
        self, df_valido: pd.DataFrame
    ) -> None:
        """
        [RN02] O campo 'observacao' não é obrigatório por RN02. Um DataFrame
        com 'observacao' vazia mas com todos os campos obrigatórios preenchidos
        não deve gerar divergências.
        """
        # Observação não faz parte dos campos obrigatórios da RN02.
        assert "observacao" not in CAMPOS_OBRIGATORIOS
        resultado = valida_campos_obrigatorios(df_valido)
        assert resultado.empty

    def test_retorno_e_dataframe(self, df_valido: pd.DataFrame) -> None:
        """
        [RN02] A função deve sempre retornar um pd.DataFrame, mesmo quando
        não há divergências.
        """
        resultado = valida_campos_obrigatorios(df_valido)
        assert isinstance(resultado, pd.DataFrame)


def test_reprovado_sem_observacao_registra_rn07() -> None:
    """RN07 deve registrar divergência para reprovado sem observação."""
    registro = {
        "lote_id": "LG-2026-00102",
        "status": "REPROVADO",
        "observacao": "",
    }

    resultado = validar_observacao_reprovado(registro)

    assert resultado["divergencias"][0]["regra_violada"] == "RN07"


def test_aprovado_sem_observacao_nao_registra_rn07() -> None:
    """RN07 não exige observação para status que não sejam REPROVADO."""
    registro = {
        "lote_id": "LG-2026-00103",
        "status": "APROVADO",
        "observacao": "",
    }

    resultado = validar_observacao_reprovado(registro)

    assert resultado["divergencias"] == []


def test_reprovado_com_observacao_nula_registra_rn07() -> None:
    """RN07 deve tratar NaN/None como observação vazia."""
    registro = {"status": "REPROVADO", "observacao": None}

    resultado = validar_observacao_reprovado(registro)

    assert resultado["divergencias"][0]["regra_violada"] == "RN07"


def test_data_fora_da_referencia_registra_rn01(df_valido: pd.DataFrame) -> None:
    """O caso de 15/06 do PDD deve ser encaminhado como divergência."""
    df_valido.loc[0, "data"] = "15/06/2026"

    resultado = validar_data_referencia(df_valido)

    assert len(resultado) == 1
    assert resultado.loc[0, "index"] == 0
    assert "RN01" in resultado.loc[0, "divergencia_rn01"]
