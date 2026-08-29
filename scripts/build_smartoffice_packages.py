"""Gerador oficial de pacotes de deploy para o Smart Office (The DX Way).

Atende rigorosamente ao Capítulo 4 e 10 do Manual de Operação do Smart Office:
- O Smart Office só reconhece o RPA se `bot.py` e `requirements.txt` estiverem na RAIZ do .zip.
- Empacota os 6 bots do pipeline em `dist/smartoffice/`.
"""

from __future__ import annotations

import argparse
import logging
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("build_smartoffice_packages")

ROOT = Path(__file__).resolve().parents[1]


def _write_src_tree(archive: ZipFile, directory: Path) -> None:
    """Inclui os módulos puros de src/ preservando a estrutura."""
    for path in sorted(directory.rglob("*.py")):
        if "__pycache__" not in path.parts:
            relative = path.relative_to(ROOT).as_posix()
            archive.write(path, relative)


def _build_bot_package(bot_folder_name: str, destination: Path) -> Path:
    """Garante bot.py e requirements.txt na raiz do ZIP."""
    bot_dir = ROOT / "bots" / bot_folder_name
    bot_file = bot_dir / "bot.py"
    req_file = bot_dir / "requirements.txt"

    if not bot_file.exists() or not req_file.exists():
        raise FileNotFoundError(f"Arquivos obrigatórios não encontrados em {bot_dir}")

    zip_path = destination / f"{bot_folder_name}.zip"

    with ZipFile(zip_path, "w", compression=ZIP_DEFLATED) as archive:
        # 1. OBRIGATÓRIO NA RAIZ DO ZIP
        archive.write(bot_file, "bot.py")
        archive.write(req_file, "requirements.txt")

        # 2. Configurações e módulos compartilhados
        if (ROOT / "config.py").exists():
            archive.write(ROOT / "config.py", "config.py")
        if (ROOT / "bot.py").exists():
            archive.write(ROOT / "bot.py", "bot.py_core.py")

        _write_src_tree(archive, ROOT / "src")

        # 3. Recursos adicionais se aplicável (ex: sistema desktop)
        if (ROOT / "desktop_app").exists():
            for path in (ROOT / "desktop_app").rglob("*.py"):
                if "__pycache__" not in path.parts:
                    archive.write(path, path.relative_to(ROOT).as_posix())

    logger.info("Pacote gerado: %s (%d bytes)", zip_path.name, zip_path.stat().st_size)
    return zip_path


def build_all_packages(output_dir: Path) -> list[Path]:
    """Gera os 6 pacotes .zip oficiais do Capstone."""
    output_dir.mkdir(parents=True, exist_ok=True)

    bots = [
        "RPA01_ColetaEstoque_DESKTOP",
        "RPA02_ColetaPedidos_WEB",
        "RPA03_ConsolidacaoRegras_CORE",
        "RPA04_ClassificadorML_HYBRID",
        "RPA05_RelatorioAlertas_NOTIF",
        "RPA06_ReprocessadorDeadLetter_SCHED",
    ]

    packages = []
    for bot in bots:
        pkg = _build_bot_package(bot, output_dir)
        packages.append(pkg)

    return packages


def main() -> int:
    parser = argparse.ArgumentParser(description="Gera pacotes .zip para deploy no Smart Office.")
    parser.add_argument("--output", type=Path, default=ROOT / "dist/smartoffice")
    args = parser.parse_args()

    logger.info("Iniciando empacotamento dos 6 bots para o Smart Office...")
    build_all_packages(args.output)
    logger.info("Todos os pacotes foram gerados com sucesso na pasta: %s", args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
