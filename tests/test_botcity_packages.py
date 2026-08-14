"""Testes do contrato de empacotamento BotCity."""

from zipfile import ZipFile

import pytest

from scripts.build_botcity_packages import build_packages


pytestmark = pytest.mark.integration


def test_pacotes_possuem_entrypoint_e_dependencias_na_raiz(tmp_path) -> None:
    cadastro, validacao = build_packages(tmp_path)

    assert cadastro.name == "bot-lotes-cadastro-playwright-mk7.zip"
    assert validacao.name == "bot-lotes-validacao-mk7.zip"

    with ZipFile(cadastro) as archive:
        cadastro_files = set(archive.namelist())
    with ZipFile(validacao) as archive:
        validacao_files = set(archive.namelist())

    assert {"bot.py", "requirements.txt", "producer.py", "config.py"} <= cadastro_files
    assert "data/samples/inspecao_lotes_dia.xlsx" in cadastro_files
    assert "src/pages/playwright_pages.py" in cadastro_files
    assert {
        "bot.py",
        "requirements.txt",
        "consumer.py",
        "validation_core.py",
        "config.py",
    } <= validacao_files
    assert "producer.py" not in validacao_files
    assert "playwright" not in ZipFile(validacao).read("requirements.txt").decode()
