"""Testes unitários do empacotamento para o Smart Office (Capítulo 4 e 10 do Manual)."""

from pathlib import Path
from zipfile import ZipFile

from src.scripts.build_smartoffice_packages import build_all_packages


def test_smartoffice_packages_arquivos_obrigatorios_na_raiz(tmp_path: Path):
    packages = build_all_packages(tmp_path)
    assert len(packages) == 6

    for pkg in packages:
        assert pkg.exists()
        assert pkg.suffix == ".zip"

        with ZipFile(pkg, "r") as archive:
            namelist = archive.namelist()
            # Validação rigorosa: bot.py e requirements.txt na RAIZ
            assert "bot.py" in namelist, f"bot.py ausente na raiz de {pkg.name}"
            assert "requirements.txt" in namelist, f"requirements.txt ausente na raiz de {pkg.name}"
            assert any(f.startswith("src/") for f in namelist), f"src/ ausente em {pkg.name}"
