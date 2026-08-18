from pathlib import Path

from scripts.auditar_modelo_ml import executar_auditoria, renderizar_markdown


def test_auditoria_detecta_integridade_calibracao_e_ood_sem_automacao():
    """A auditoria produz evidências objetivas, inclusive para entradas fora do vocabulário."""
    auditoria = executar_auditoria(
        Path("data/ml/historico_lotes_sintetico.csv"),
        Path("models/classificador_lotes.pkl"),
        max_gap_turno=0.05,
        max_mudanca=0.10,
        max_ece=0.05,
    )

    assert auditoria["integridade"]["dataset_sha_confere"] is True
    assert auditoria["calibracao"]["ece"] <= 0.05
    assert auditoria["ood"]["casos"] == 24
    assert auditoria["ood"]["automaticas_alta_confianca"] == 0
    assert "Auditoria de Robustez" in renderizar_markdown(auditoria)
