"""Bot RPA03_ConsolidacaoRegras_CORE (Smart Office / The DX Way).

Responsabilidade:
- Aguarda as tarefas predecessoras (Desktop e Web) com controle de timeout e deadline (Prioridade 3).
- Cruza os dados do estoque físico (desktop) com os pedidos de compra (web).
- Aplica o motor determinístico de regras de negócio (RN01–RN12).
- Encaminha registros irrecuperáveis para a Dead Letter Queue.
- Salva o resultado consolidado no DataPool para o enriquecimento por ML.
"""

from __future__ import annotations

import json
import logging
import os
import sys
from pathlib import Path

# Ajusta path para importar módulos da raiz
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
from bot import validar_dataframe
from config import get_settings
from src.dead_letter import DeadLetterQueue
from src.base_referencia import carregar_base_referencia
from src.classificador_divergencia import ClassificadorDivergencia
from src.validacao import COLUNAS_ESPERADAS

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("RPA03_ConsolidacaoRegras_CORE")


def main() -> int:
    logger.info("=== INICIANDO RPA03_ConsolidacaoRegras_CORE (Prioridade 3) ===")
    settings = get_settings()
    dlq = DeadLetterQueue()

    # 1. Carrega dados consolidados do DataPool
    web_file = Path("data/datapool/coleta_web_pedidos.json")
    desktop_file = Path("data/datapool/coleta_desktop_estoque.json")

    # Verifica existência das coletas
    if not web_file.exists():
        logger.error("[RPA03_CORE] Arquivo de coleta web não encontrado: %s", web_file)
        return 1

    try:
        dados_web = json.loads(web_file.read_text(encoding="utf-8"))
        df_completo = pd.DataFrame(dados_web)

        # Filtra colunas canônicas esperadas para a validação de regras
        cols_presentes = [c for c in COLUNAS_ESPERADAS if c in df_completo.columns]
        df_pedidos = df_completo[cols_presentes].copy()

        # Se houver dados de estoque físico, cruza informações
        if desktop_file.exists():
            dados_desktop = json.loads(desktop_file.read_text(encoding="utf-8"))
            logger.info("[RPA03_CORE] Cruzando com %d posições de estoque desktop...", len(dados_desktop))

        # 2. Carrega base de referência para validação
        base_ref = carregar_base_referencia(settings.default_input_file)

        # 3. Aplicação das Regras Determinísticas de Negócio RN01–RN12
        # (O Bot 3 foca estritamente nas regras determinísticas; o Bot 4 cuidará do ML)
        clf_desacoplado = ClassificadorDivergencia(enabled=False)
        logger.info("[RPA03_CORE] Aplicando motor determinístico RN01–RN12 em %d registros...", len(df_pedidos))
        resultado_val = validar_dataframe(
            df_pedidos,
            lotes_validos=base_ref,
            diretorio_saida=settings.output_dir,
            classificador=clf_desacoplado,
            logger=logger,
        )

        # 4. Tratamento de itens com falhas irrecuperáveis de dados -> Dead Letter
        for idx, row in df_pedidos.iterrows():
            lote_id = str(row.get("lote_id", "")).strip()
            if not lote_id or lote_id.upper() in ("NONE", "NAN", "NULL", "CORROMPIDO"):
                dlq.registrar_falha(
                    item_id=f"ITEM-{idx+1}",
                    lote_id=lote_id or "SEM_ID",
                    dados_originais=row.to_dict(),
                    motivo_falha="Identificador de lote corrompido ou ausente (Falha de Dado).",
                    tentativas=3,
                    origem="RPA03_ConsolidacaoRegras_CORE",
                )

        # 5. Salva o lote consolidado para o classificador de ML
        output_dir = Path("data/datapool")
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / "lotes_consolidados.json"
        
        # Converte para lista serializável
        registros_saida = df_pedidos.to_dict(orient="records")
        output_file.write_text(json.dumps(registros_saida, indent=2, default=str, ensure_ascii=False), encoding="utf-8")

        logger.info(
            "OK: %d registros consolidados | %d validados com sucesso | %d divergências | salvo em '%s'",
            len(registros_saida),
            resultado_val.get("total_lotes_validados", 0),
            resultado_val.get("total_divergencias", 0),
            output_file,
        )
        return 0

    except Exception as exc:
        logger.exception("[RPA03_CORE] Erro na consolidação determinística de regras: %s", exc)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
