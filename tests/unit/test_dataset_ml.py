import json
from pathlib import Path
import pytest

from api_ml.features import FEATURE_ORDER
from src.scripts.train_model import (
    gerar_dataset,
    validar_dataset,
)


def test_dataset_reprodutivel():
    """Garantir que a mesma seed gera exatamente as mesmas linhas."""
    dataset1 = gerar_dataset(total=10_000, seed=42)
    dataset2 = gerar_dataset(total=10_000, seed=42)
    assert dataset1 == dataset2


def test_dataset_requisitos_minimos():
    """Valida que o dataset possui no mínimo 10.000 linhas, 3 classes e as features esperadas."""
    dataset = gerar_dataset(total=12_000, seed=42)
    assert len(dataset) == 12_000
    validar_dataset(dataset)

    classes_encontradas = {row["classe"] for row in dataset}
    assert classes_encontradas == {"valido_automatico", "revisar", "recusar_automatico"}

    features = set(dataset[0].keys()) - {"sample_id", "classe"}
    assert features == set(FEATURE_ORDER)


def test_balanceamento_classe_e_turno():
    """Valida o balanceamento exato/aproximado das classes e turnos."""
    dataset = gerar_dataset(total=12_000, seed=42)
    contagem_classe = {}
    contagem_turno = {}
    for row in dataset:
        c = row["classe"]
        t = row["turno"]
        contagem_classe[c] = contagem_classe.get(c, 0) + 1
        contagem_turno[t] = contagem_turno.get(t, 0) + 1

    for c, count in contagem_classe.items():
        assert count == 4000

    for t, count in contagem_turno.items():
        assert abs(count - 4000) <= 5



def test_colunas_proibidas_nao_estao_no_dataset():
    """Valida que identificadores de produção (ex: lote_id, produto, etc) foram excluídos."""
    dataset = gerar_dataset(total=10_000, seed=42)
    colunas_proibidas = {"lote_id", "produto", "linha", "responsavel", "data", "observacao"}
    for row in dataset:
        chaves = set(row.keys())
        assert not (chaves & colunas_proibidas)


def test_validar_dataset_falha_com_menos_linhas():
    """validar_dataset deve falhar se o total for inferior a 10.000."""
    com_poucas = gerar_dataset(total=12_000, seed=42)[:5000]
    with pytest.raises(ValueError, match="mínimo exigido: 10.000"):
        validar_dataset(com_poucas)


def test_manifesto_e_csv_existem():
    """Verifica se os arquivos gerados em data/ml/ realmente existem."""
    csv_path = Path("data/ml/historico_lotes_sintetico.csv")
    manifest_path = Path("data/ml/dataset_manifest.json")
    assert csv_path.exists()
    assert manifest_path.exists()

    with open(manifest_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["total_rows"] >= 10_000
    assert "sha256" in data
