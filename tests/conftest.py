from __future__ import annotations

import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import MagicMock

PROJECT_ROOT = Path(__file__).parents[1]
if str(PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "src"))
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
import pytest

from src.pages import PlaywrightFormularioLotesPage


def pytest_configure(config: pytest.Config) -> None:
    """Garante registro de todos os markers mesmo sem o pytest.ini na raiz."""
    config.addinivalue_line("markers", "unit: testes rapidos e isolados")
    config.addinivalue_line("markers", "integration: testes de integracao entre modulos")
    config.addinivalue_line("markers", "regression: testes que protegem contra regressao")
    config.addinivalue_line("markers", "e2e: testes do fluxo ponta a ponta")
    config.addinivalue_line("markers", "browser: testes com Chromium e interface web")
    config.addinivalue_line("markers", "slow: testes de execucao mais demorada")


@pytest.fixture
def registro_valido() -> dict[str, str]:
    """Registro minimo valido e reutilizavel para as regras RN01-RN12."""
    return {
        "lote_id": "LG-2026-00001",
        "produto": "TV",
        "linha": "L1",
        "turno": "A",
        "status": "APROVADO",
        "responsavel": "Ana",
        "data": "15/06/2026",
        "observacao": "",
        "data_referencia": "15/06/2026",
    }


@pytest.fixture
def lotes_referencia() -> set[str]:
    """Base de referencia pequena, deterministica e sem acesso a disco."""
    return {"LG-2026-00001", "LG-2026-00002"}


@pytest.fixture
def mock_base_referencia(lotes_referencia: set[str]) -> MagicMock:
    """Substitui a consulta externa a Base_Referencia."""
    return MagicMock(return_value=lotes_referencia)


@pytest.fixture
def instante_fixo_manaus() -> datetime:
    """Relogio fixo usado nas evidencias de arquivo e log."""
    return datetime(2026, 6, 30, 8, 15, 0, tzinfo=timezone(timedelta(hours=-4)))


@pytest.fixture
def planilha_10_dias_factory(tmp_path: Path):
    """Cria as dez abas e 250 registros do gabarito inteiramente em tmp_path."""

    def criar(nome: str = "inspecao_10_dias_sintetica.xlsx"):
        caminho = tmp_path / nome
        referencias: set[str] = set()
        indice_global = 0

        with pd.ExcelWriter(caminho, engine="openpyxl") as writer:
            for dia in range(15, 25):
                data = f"{dia:02d}/06/2026"
                aba = f"Insp_{dia:02d}_06_2026"
                registros: list[dict[str, str]] = []

                for _ in range(25):
                    lote_id = f"LG-2026-{indice_global + 1:05d}"
                    registro = {
                        "lote_id": lote_id,
                        "produto": "TV",
                        "linha": "L1",
                        "turno": "A",
                        "status": "APROVADO",
                        "responsavel": "Ana",
                        "data": data,
                        "observacao": "",
                    }

                    if indice_global < 150:
                        referencias.add(lote_id)
                        if indice_global % 10 == 0:
                            registro["status"] = "OK"
                    elif indice_global < 200:
                        # RN05: lote deliberadamente ausente da referencia.
                        pass
                    elif indice_global < 220:
                        referencias.add(lote_id)
                        registro["status"] = "EM AJUSTE"
                    else:
                        referencias.add(lote_id)
                        registro["produto"] = ""

                    registros.append(registro)
                    indice_global += 1

                pd.DataFrame([[f"Inspecoes de {data}", "Registros: 25"]]).to_excel(
                    writer,
                    sheet_name=aba,
                    index=False,
                    header=False,
                )
                pd.DataFrame(registros).to_excel(
                    writer,
                    sheet_name=aba,
                    index=False,
                    startrow=2,
                )

        esperado = {
            "Valido": 150,
            "Divergencia": 50,
            "Ambiguo": 20,
            "Erro de Entrada": 30,
        }
        return caminho, referencias, esperado

    return criar


@pytest.fixture
def pagina_web() -> str:
    """Retorna a URL usada nos testes E2E."""
    return os.getenv(
        "E2E_BASE_URL",
        (Path(__file__).parents[1] / "web" / "index.html").as_uri(),
    )


@pytest.fixture
def pagina_html() -> str:
    """Mantém o nome de fixture usado no exercício 19-X."""
    return (Path(__file__).parents[1] / "web" / "index.html").as_uri()


@pytest.fixture
def formulario_page(page, pagina_html: str) -> PlaywrightFormularioLotesPage:
    po = PlaywrightFormularioLotesPage(
        page=page,
        pagina_html=pagina_html,
        credenciais={"usuario": "automacao", "senha": "automacao"},
    )
    po.abrir()
    return po


@pytest.fixture
def e2e_screenshot_dir(tmp_path: Path) -> Path:
    """Mantem evidencias de teste fora da arvore do repositorio."""
    path = tmp_path / "screenshots"
    path.mkdir(parents=True, exist_ok=True)
    return path
