"""Executa Playwright e Selenium em sequência e encerra o front-end."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
BOTS = (
    ("Playwright", BASE_DIR / "playwright" / "bot.py"),
    ("Selenium", BASE_DIR / "selenium" / "bot.py"),
)


def main() -> int:
    status_final = 0
    shutdown_file = Path(
        os.getenv("SHUTDOWN_FILE", "/run-status/tests-finished")
    )

    try:
        for ferramenta, bot_path in BOTS:
            print(f"\n{'=' * 20} {ferramenta} {'=' * 20}", flush=True)
            resultado = subprocess.run(
                [sys.executable, str(bot_path)],
                cwd=BASE_DIR,
                check=False,
            )
            if resultado.returncode:
                status_final = resultado.returncode
                print(
                    f"{ferramenta} terminou com código {resultado.returncode}; "
                    "a próxima automação ainda será executada.",
                    flush=True,
                )
    finally:
        shutdown_file.parent.mkdir(parents=True, exist_ok=True)
        shutdown_file.touch()
        print("\nSinal de encerramento do front-end enviado.", flush=True)

    return status_final


if __name__ == "__main__":
    raise SystemExit(main())
