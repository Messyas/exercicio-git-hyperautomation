"""Testes unitários da Dead Letter Queue (The DX Way)."""

from pathlib import Path
from src.dead_letter import DeadLetterQueue


def test_dead_letter_queue_registro_e_leitura(tmp_path: Path):
    dlq = DeadLetterQueue(storage_dir=tmp_path)
    assert dlq.total_itens() == 0

    item = dlq.registrar_falha(
        item_id="ITEM-TESTE-01",
        lote_id="LOTE-CORROMPIDO",
        dados_originais={"lote_id": "LOTE-CORROMPIDO", "valor": "invalido"},
        motivo_falha="Falha estrutural de tipo",
        tentativas=3,
        origem="TEST_UNIT",
    )

    assert item.item_id == "ITEM-TESTE-01"
    assert dlq.total_itens() == 1

    itens = dlq.listar_itens(status="PENDENTE_REVISAO")
    assert len(itens) == 1
    assert itens[0].lote_id == "LOTE-CORROMPIDO"
    assert itens[0].tentativas_realizadas == 3

    dlq.limpar()
    assert dlq.total_itens() == 0
