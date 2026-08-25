"""Monta os três pacotes S10-B aceitos pelo BotCity Runner."""

from __future__ import annotations

import argparse
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


ROOT = Path(__file__).resolve().parents[1]


def _write_tree(archive: ZipFile, directory: Path, prefix: str) -> None:
    for path in sorted(directory.rglob("*.py")):
        if "__pycache__" not in path.parts:
            relative = path.relative_to(directory).as_posix()
            archive.write(path, f"{prefix}/{relative}")


def _build_cadastro(destination: Path) -> None:
    with ZipFile(destination, "w", compression=ZIP_DEFLATED) as archive:
        archive.write(ROOT / "bots/cadastro/bot.py", "bot.py")
        archive.write(
            ROOT / "bots/cadastro/requirements.txt", "requirements.txt"
        )
        archive.write(ROOT / "producer.py", "producer.py")
        archive.write(ROOT / "config.py", "config.py")
        archive.write(
            ROOT / "data/samples/inspecao_lotes_dia.xlsx",
            "data/samples/inspecao_lotes_dia.xlsx",
        )
        _write_tree(archive, ROOT / "src", "src")


def _build_coletor(destination: Path) -> None:
    with ZipFile(destination, "w", compression=ZIP_DEFLATED) as archive:
        archive.write(ROOT / "bots/coletor/bot.py", "bot.py")
        archive.write(ROOT / "bots/coletor/requirements.txt", "requirements.txt")
        archive.write(ROOT / "coletor.py", "coletor.py")
        archive.write(ROOT / "config.py", "config.py")
        archive.write(
            ROOT / "data/samples/inspecao_lotes_dia.xlsx",
            "data/samples/inspecao_lotes_dia.xlsx",
        )
        _write_tree(archive, ROOT / "src", "src")


def _build_validacao(destination: Path) -> None:
    with ZipFile(destination, "w", compression=ZIP_DEFLATED) as archive:
        archive.write(ROOT / "bots/validacao/bot.py", "bot.py")
        archive.write(
            ROOT / "bots/validacao/requirements.txt", "requirements.txt"
        )
        archive.write(ROOT / "consumer.py", "consumer.py")
        archive.write(ROOT / "bot.py", "validation_core.py")
        archive.write(ROOT / "config.py", "config.py")
        _write_tree(archive, ROOT / "src", "src")


def build_packages(output: Path) -> tuple[Path, Path, Path]:
    output.mkdir(parents=True, exist_ok=True)
    coletor = output / "messyas-bot-coletor-v1.zip"
    cadastro = output / "messyas-bot-cadastro-v1.zip"
    validacao = output / "messyas-bot-conferencia-v1.zip"
    _build_coletor(coletor)
    _build_cadastro(cadastro)
    _build_validacao(validacao)
    return coletor, cadastro, validacao


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Gera os pacotes de deploy do pipeline BotCity."
    )
    parser.add_argument("--output", type=Path, default=ROOT / "dist/botcity")
    arguments = parser.parse_args()
    for package in build_packages(arguments.output):
        print(package)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
