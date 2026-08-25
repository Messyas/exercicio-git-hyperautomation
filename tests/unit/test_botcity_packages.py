"""Testes do contrato de empacotamento BotCity."""

from zipfile import ZipFile

import pytest

from scripts.build_botcity_packages import build_packages


pytestmark = pytest.mark.unit


def test_pacotes_possuem_entrypoint_e_dependencias_na_raiz(tmp_path) -> None:
    coletor, cadastro, validacao = build_packages(tmp_path)

    assert coletor.name == "messyas-bot-coletor-v1.zip"
    assert cadastro.name == "messyas-bot-cadastro-v1.zip"
    assert validacao.name == "messyas-bot-conferencia-v1.zip"

    with ZipFile(coletor) as archive:
        coletor_files = set(archive.namelist())
    with ZipFile(cadastro) as archive:
        cadastro_files = set(archive.namelist())
    with ZipFile(validacao) as archive:
        validacao_files = set(archive.namelist())

    assert {"bot.py", "requirements.txt", "coletor.py", "config.py"} <= coletor_files
    assert "data/samples/inspecao_lotes_dia.xlsx" in coletor_files
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
