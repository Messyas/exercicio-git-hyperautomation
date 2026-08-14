"""
Testes unitários para o módulo src/base_referencia.py.

Cobrem a regra de negócio:
    - RN03: Verificar Lote na Base de Referência
          (carregar_base_referencia e verificar_existencia_lote)

Utiliza DataFrames simulados (mock) e conjuntos de lotes válidos mockados
para isolamento completo, sem dependência do arquivo real .xlsx.
"""

import pandas as pd
import pytest

from src.base_referencia import (
    carregar_base_referencia,
    verificar_existencia_lote,
)


pytestmark = pytest.mark.integration


# Fixtures reutilizáveis


@pytest.fixture
def lotes_validos_mock() -> set[str]:
    """
    Conjunto simulado de lotes válidos da base de referência (RN03).
    Contém lotes de 101 a 105, excluindo intencionalmente o 103
    para simular o cenário de divergência do arquivo real.
    """
    return {
        "LG-2026-00101",
        "LG-2026-00102",
        "LG-2026-00104",
        "LG-2026-00105",
    }


@pytest.fixture
def df_sem_divergencias(lotes_validos_mock: set[str]) -> pd.DataFrame:
    """
    DataFrame de inspeção cujos lote_id existem todos na base de referência
    e representa o caminho sem divergências da RN03.
    """
    return pd.DataFrame(
        {
            "lote_id": ["LG-2026-00101", "LG-2026-00102", "LG-2026-00104"],
            "produto": ["TV55-4K-B", "MON27-QHD", "TV65-OLED"],
            "status": ["APROVADO", "APROVADO", "REPROVADO"],
        }
    )


@pytest.fixture
def df_com_lote_inexistente() -> pd.DataFrame:
    """
    DataFrame com o lote 'LG-2026-00103' que NÃO existe na base de
    referência e deve ser detectado como divergência RN03.
    Este lote está intencionalmente ausente da base real (erro controlado).
    """
    return pd.DataFrame(
        {
            "lote_id": ["LG-2026-00101", "LG-2026-00103", "LG-2026-00102"],
            "produto": ["TV55-4K-B", "AC12-SPLIT", "MON27-QHD"],
            "status": ["APROVADO", "APROVADO", "APROVADO"],
        }
    )


@pytest.fixture
def df_com_multiplos_inexistentes() -> pd.DataFrame:
    """
    DataFrame com múltiplos lote_id que não existem na base de referência.
    Simula um lote de inspeção altamente divergente.
    """
    return pd.DataFrame(
        {
            "lote_id": [
                "LG-2026-00101",  # válido
                "LG-2026-00999",  # inexistente
                "LG-2026-00103",  # inexistente (erro intencional real)
                "LG-2026-00102",  # válido
                "LOTE-FANTASMA",  # inexistente
            ],
            "produto": ["TV55-4K-B", "MON27-QHD", "AC12-SPLIT", "MON27-QHD", "XX"],
            "status": ["APROVADO", "APROVADO", "APROVADO", "APROVADO", "PENDENTE"],
        }
    )


@pytest.fixture
def df_com_todos_inexistentes() -> pd.DataFrame:
    """
    DataFrame onde nenhum lote_id existe na base de referência.
    Representa o pior cenário de divergência total (RN03).
    """
    return pd.DataFrame(
        {
            "lote_id": ["LG-FAKE-001", "LG-FAKE-002", "LG-FAKE-003"],
            "produto": ["ProdutoA", "ProdutoB", "ProdutoC"],
            "status": ["APROVADO", "REPROVADO", "PENDENTE"],
        }
    )


# RN03: carregar_base_referencia


class TestCarregarBaseReferencia:
    """Testes de integração para carregar_base_referencia (RN03)."""

    CAMINHO_ARQUIVO = "data/samples/inspecao_lotes_dia.xlsx"

    def test_retorna_set(self) -> None:
        """
        [RN03] carregar_base_referencia deve retornar um objeto do tipo set.
        """
        resultado = carregar_base_referencia(self.CAMINHO_ARQUIVO)
        assert isinstance(resultado, set)

    def test_carrega_quantidade_correta_de_ids(self) -> None:
        """
        [RN03] A base de referência deve conter exatamente 23 lote_id válidos,
        conforme o arquivo Excel (a nota do revisor confirma que LG-2026-00103
        está ausente intencionalmente).
        """
        resultado = carregar_base_referencia(self.CAMINHO_ARQUIVO)
        assert len(resultado) == 23

    def test_lote_valido_presente_na_base(self) -> None:
        """
        [RN03] Um lote_id sabidamente cadastrado (LG-2026-00101) deve estar
        no conjunto retornado.
        """
        resultado = carregar_base_referencia(self.CAMINHO_ARQUIVO)
        assert "LG-2026-00101" in resultado

    def test_lote_intencional_ausente_da_base(self) -> None:
        """
        [RN03] O lote LG-2026-00103, ausente intencionalmente da base real
        (erro controlado do arquivo de exercício), NÃO deve estar no conjunto.
        """
        resultado = carregar_base_referencia(self.CAMINHO_ARQUIVO)
        assert "LG-2026-00103" not in resultado

    def test_retorno_sem_valores_nulos(self) -> None:
        """
        [RN03] O conjunto retornado não deve conter a string 'nan'
        (resultado de valores nulos convertidos para string).
        """
        resultado = carregar_base_referencia(self.CAMINHO_ARQUIVO)
        assert "nan" not in resultado

    def test_arquivo_inexistente_levanta_excecao(self) -> None:
        """
        [RN03] Deve levantar exceção ao tentar carregar um arquivo que não
        existe no caminho informado.
        """
        with pytest.raises(Exception):
            carregar_base_referencia("caminho/invalido/arquivo.xlsx")


# RN03: verificar_existencia_lote


class TestVerificarExistenciaLote:
    """Testes para a função verificar_existencia_lote (RN03)."""

    def test_caminho_feliz_sem_divergencias(
        self,
        df_sem_divergencias: pd.DataFrame,
        lotes_validos_mock: set[str],
    ) -> None:
        """
        [RN03] Caminho feliz: DataFrame com todos os lote_id presentes na
        base de referência deve retornar um DataFrame vazio (sem divergências).
        """
        resultado = verificar_existencia_lote(df_sem_divergencias, lotes_validos_mock)
        assert resultado.empty, "Não deveria haver divergências RN03."

    def test_detecta_lote_inexistente(
        self,
        df_com_lote_inexistente: pd.DataFrame,
        lotes_validos_mock: set[str],
    ) -> None:
        """
        [RN03] Deve detectar e retornar a linha com lote_id 'LG-2026-00103'
        que não existe na base de referência.
        """
        resultado = verificar_existencia_lote(
            df_com_lote_inexistente, lotes_validos_mock
        )

        assert not resultado.empty, "Deveria detectar 1 divergência RN03."
        assert len(resultado) == 1
        assert resultado["lote_id"].iloc[0] == "LG-2026-00103"

    def test_detecta_multiplos_lotes_inexistentes(
        self,
        df_com_multiplos_inexistentes: pd.DataFrame,
        lotes_validos_mock: set[str],
    ) -> None:
        """
        [RN03] Deve detectar corretamente múltiplos lotes inexistentes
        (LG-2026-00999, LG-2026-00103 e LOTE-FANTASMA) em um mesmo DataFrame.
        """
        resultado = verificar_existencia_lote(
            df_com_multiplos_inexistentes, lotes_validos_mock
        )

        assert len(resultado) == 3

        lotes_divergentes = set(resultado["lote_id"].tolist())
        assert "LG-2026-00999" in lotes_divergentes
        assert "LG-2026-00103" in lotes_divergentes
        assert "LOTE-FANTASMA" in lotes_divergentes

    def test_todos_lotes_inexistentes(
        self,
        df_com_todos_inexistentes: pd.DataFrame,
        lotes_validos_mock: set[str],
    ) -> None:
        """
        [RN03] Quando nenhum lote_id do DataFrame de inspeção existir na base
        de referência, todas as linhas devem ser retornadas como divergentes.
        """
        resultado = verificar_existencia_lote(
            df_com_todos_inexistentes, lotes_validos_mock
        )

        assert len(resultado) == len(df_com_todos_inexistentes)

    def test_coluna_divergencia_rn03_esta_presente(
        self,
        df_com_lote_inexistente: pd.DataFrame,
        lotes_validos_mock: set[str],
    ) -> None:
        """
        [RN03] O DataFrame retornado deve conter a coluna auxiliar
        'divergencia_rn03' com a mensagem descritiva da falha.
        """
        resultado = verificar_existencia_lote(
            df_com_lote_inexistente, lotes_validos_mock
        )

        assert "divergencia_rn03" in resultado.columns

    def test_mensagem_divergencia_referencia_rn03(
        self,
        df_com_lote_inexistente: pd.DataFrame,
        lotes_validos_mock: set[str],
    ) -> None:
        """
        [RN03] A mensagem na coluna 'divergencia_rn03' deve mencionar
        o código '[RN03]' e o lote_id problemático.
        """
        resultado = verificar_existencia_lote(
            df_com_lote_inexistente, lotes_validos_mock
        )

        mensagem = resultado["divergencia_rn03"].iloc[0]
        assert "RN03" in mensagem
        assert "LG-2026-00103" in mensagem

    def test_coluna_index_preservada_no_retorno(
        self,
        df_com_lote_inexistente: pd.DataFrame,
        lotes_validos_mock: set[str],
    ) -> None:
        """
        [RN03] O DataFrame retornado deve preservar a coluna 'index' com a
        posição original do registro no DataFrame de inspeção, facilitando
        o rastreamento da divergência pelo analista.
        """
        resultado = verificar_existencia_lote(
            df_com_lote_inexistente, lotes_validos_mock
        )

        assert "index" in resultado.columns
        assert resultado["index"].iloc[0] == 1  # LG-2026-00103 era a linha 1

    def test_retorno_e_dataframe(
        self,
        df_sem_divergencias: pd.DataFrame,
        lotes_validos_mock: set[str],
    ) -> None:
        """
        [RN03] A função deve sempre retornar um pd.DataFrame, mesmo quando
        não há divergências.
        """
        resultado = verificar_existencia_lote(df_sem_divergencias, lotes_validos_mock)
        assert isinstance(resultado, pd.DataFrame)

    def test_df_sem_coluna_lote_id_levanta_excecao(
        self,
        lotes_validos_mock: set[str],
    ) -> None:
        """
        [RN03] Deve levantar ValueError ao receber um DataFrame que não
        possui a coluna 'lote_id', sinalizando uso incorreto da função.
        """
        df_sem_lote_id = pd.DataFrame({"produto": ["TV55-4K-B"], "status": ["OK"]})

        with pytest.raises(ValueError) as info_excecao:
            verificar_existencia_lote(df_sem_lote_id, lotes_validos_mock)

        assert "RN03" in str(info_excecao.value)

    def test_base_vazia_marca_todos_como_divergentes(
        self,
        df_sem_divergencias: pd.DataFrame,
    ) -> None:
        """
        [RN03] Com uma base de referência vazia (set vazio), todos os registros
        do DataFrame de inspeção devem ser marcados como divergentes.
        """
        base_vazia: set[str] = set()
        resultado = verificar_existencia_lote(df_sem_divergencias, base_vazia)

        assert len(resultado) == len(df_sem_divergencias)
