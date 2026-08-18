import sys
from pathlib import Path

# Garante que o diretório raiz do projeto esteja no sys.path
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

import hashlib
import json
import logging
import os
import random
import time
from typing import Any, Mapping, Sequence


import joblib
import numpy as np
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    log_loss,
    precision_score,
    recall_score,
)
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder
from sklearn.pipeline import Pipeline
import sklearn

from api_ml.features import FEATURE_ORDER, normalizar_status_raw
from api_ml.schemas import ClasseML

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

CLASSES_VALIDAS = {item.value for item in ClasseML}
TURNOS_VALIDOS = {"A", "B", "C"}

# Tabela de probabilidades condicionais por classe.
# Mantém 10-15% de sobreposição entre classes para que a probabilidade
# tenha significado real e o modelo não seja apenas uma tabela de decisão.
# Ref: Seção 6.3 do PLANO_IMPLEMENTACAO_EXERCICIO_24A.md
STATUS_POR_CLASSE = {
    ClasseML.VALIDO_AUTOMATICO.value: [
        ("APROVADO PARCIAL", 32),           # status primário desta classe
        ("AJUSTE CONCLUIDO", 32),           # status primário desta classe
        ("EM AJUSTE", 12),                  # compartilhado
        ("EM ANÁLISE", 8),                  # compartilhado com revisar
        ("PENDENTE", 5),                    # compartilhado com revisar/recusar
        ("ESPECIFICAÇÃO EM REVISÃO", 2),    # tipicamente revisar — overlap
        ("AGUARDANDO REINSPEÇÃO", 2),       # tipicamente revisar — overlap
        ("AJUSTE REPROVADO", 2),            # tipicamente recusar — overlap
    ],
    ClasseML.REVISAR.value: [
        ("PENDENTE", 22),                   # status primário desta classe
        ("EM ANALISE", 22),                 # status primário desta classe
        ("ESPECIFICAÇÃO EM REVISÃO", 20),   # status primário desta classe
        ("AGUARDANDO REINSPEÇÃO", 18),      # status primário desta classe
        ("EM AJUSTE", 5),                   # compartilhado
        ("APROVADO PARCIAL", 3),            # tipicamente valido — overlap
        ("AJUSTE CONCLUIDO", 3),            # tipicamente valido — overlap
        ("CANCELADO", 3),                   # tipicamente recusar — overlap
        ("AJUSTE REPROVADO", 2),            # tipicamente recusar — overlap
        ("REINSPECAO REPROVADA", 2),         # tipicamente recusar — overlap
    ],
    ClasseML.RECUSAR_AUTOMATICO.value: [
        ("CANCELADO", 27),                  # status primário desta classe
        ("AJUSTE REPROVADO", 22),           # status primário desta classe
        ("REINSPECAO REPROVADA", 22),       # status primário desta classe
        ("FORA DE ESPECIFICACAO", 18),      # status primário desta classe
        ("PENDENTE", 3),                    # tipicamente revisar — overlap
        ("EM AJUSTE", 3),                   # compartilhado
        ("ESPECIFICAÇÃO EM REVISÃO", 2),    # tipicamente revisar — overlap
        ("AGUARDANDO REINSPEÇÃO", 2),       # tipicamente revisar — overlap
        ("EM ANALISE", 1),                  # tipicamente revisar — overlap
    ],
}


def gerar_dataset(*, total: int = 12_000, seed: int = 42) -> list[dict[str, Any]]:
    """Gera um dataset sintético de lotes com no mínimo 10.000 linhas de forma determinística."""
    if total < 10_000:
        raise ValueError("O dataset deve conter no mínimo 10.000 linhas.")

    rng = random.Random(seed)
    classes = list(CLASSES_VALIDAS)
    classes.sort()
    
    qtd_por_classe = total // len(classes)
    linhas: list[dict[str, Any]] = []
    sample_counter = 1

    for classe in classes:
        turnos = ["A", "B", "C"]
        qtd_por_turno = [qtd_por_classe // 3] * 3
        # Distribui o resto se houver
        for i in range(qtd_por_classe % 3):
            qtd_por_turno[i] += 1

        opcoes_status, pesos_status = zip(*STATUS_POR_CLASSE[classe])

        for turno_idx, turno in enumerate(turnos):
            count = qtd_por_turno[turno_idx]
            for _ in range(count):
                tem_obs = rng.choice([True, False])
                # Ajusta peso se tiver observação para simular tendência
                if tem_obs and classe == ClasseML.VALIDO_AUTOMATICO.value:
                    pesos_ajustados = [w * 1.2 if s in ("APROVADO PARCIAL", "AJUSTE CONCLUIDO") else w for s, w in zip(opcoes_status, pesos_status)]
                else:
                    pesos_ajustados = list(pesos_status)

                status_raw = rng.choices(opcoes_status, weights=pesos_ajustados, k=1)[0]
                
                linhas.append({
                    "sample_id": f"SMP-{sample_counter:06d}",
                    "status_raw": status_raw,
                    "turno": turno,
                    "tem_obs": tem_obs,
                    "classe": classe,
                })
                sample_counter += 1

    rng.shuffle(linhas)
    return linhas


def validar_dataset(rows: Sequence[Mapping[str, Any]]) -> None:
    """Valida a integridade, esquema e balanceamento do dataset."""
    total = len(rows)
    if total < 10_000:
        raise ValueError(f"Dataset possui apenas {total} linhas, mínimo exigido: 10.000")

    classes_encontradas: dict[str, int] = {}
    turnos_encontrados: dict[str, int] = {}
    
    colunas_proibidas = {"lote_id", "produto", "linha", "responsavel", "data", "observacao"}

    for idx, row in enumerate(rows):
        # Verifica colunas proibidas
        chaves = set(row.keys())
        if chaves & colunas_proibidas:
            raise ValueError(f"Linha {idx} possui coluna proibida: {chaves & colunas_proibidas}")

        # Valida nulos nas features e no alvo
        for feat in ["status_raw", "turno", "tem_obs", "classe"]:
            if row.get(feat) is None:
                raise ValueError(f"Linha {idx} possui valor nulo no campo '{feat}'")

        turno = str(row["turno"]).strip().upper()
        if turno not in TURNOS_VALIDOS:
            raise ValueError(f"Linha {idx} possui turno inválido: {turno}")

        classe = str(row["classe"])
        if classe not in CLASSES_VALIDAS:
            raise ValueError(f"Linha {idx} possui classe inválida: {classe}")

        classes_encontradas[classe] = classes_encontradas.get(classe, 0) + 1
        turnos_encontrados[turno] = turnos_encontrados.get(turno, 0) + 1

    if set(classes_encontradas.keys()) != CLASSES_VALIDAS:
        raise ValueError(f"Classes no dataset ({set(classes_encontradas.keys())}) diferentes das esperadas ({CLASSES_VALIDAS})")

    # Tolerância de balanceamento por classe (máx 5% de desvio da média)
    media_esperada = total / len(CLASSES_VALIDAS)
    for c, cnt in classes_encontradas.items():
        if abs(cnt - media_esperada) / media_esperada > 0.05:
            raise ValueError(f"Classe {c} desbalanceada: {cnt} (esperado ~{media_esperada})")


def salvar_dataset(rows: list[dict[str, Any]], csv_path: Path, manifest_path: Path) -> None:
    """Salva o CSV e o arquivo de manifesto com métricas de validação."""
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)

    df = pd.DataFrame(rows)
    df.to_csv(csv_path, index=False, encoding="utf-8")

    # Calcula SHA256 do CSV
    hasher = hashlib.sha256()
    with open(csv_path, "rb") as f:
        hasher.update(f.read())
    sha256_hex = hasher.hexdigest()

    contagem_classe = df["classe"].value_counts().to_dict()
    contagem_turno = df["turno"].value_counts().to_dict()
    contagem_tem_obs = df["tem_obs"].value_counts().to_dict()
    contagem_status = df["status_raw"].value_counts().to_dict()
    
    comb_df = df.groupby(["classe", "turno"]).size().reset_index(name="count")
    combinacoes = comb_df.to_dict(orient="records")

    manifest = {
        "dataset_name": csv_path.name,
        "total_rows": len(rows),
        "sha256": sha256_hex,
        "seed": 42,
        "columns": list(df.columns),
        "features": list(FEATURE_ORDER),
        "class_distribution": contagem_classe,
        "turno_distribution": contagem_turno,
        "tem_obs_distribution": {str(k): v for k, v in contagem_tem_obs.items()},
        "status_raw_distribution": contagem_status,
        "classe_turno_combinations": combinacoes,
    }

    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    logger.info(f"Dataset salvo em {csv_path} (SHA256: {sha256_hex[:10]}...)")
    logger.info(f"Manifesto salvo em {manifest_path}")


def build_pipeline(*, random_state: int = 42) -> CalibratedClassifierCV:
    """Constrói o pipeline scikit-learn com ColumnTransformer, RandomForest e CalibratedClassifierCV."""
    preprocessor = ColumnTransformer(
        transformers=[
            (
                "categoricas",
                OneHotEncoder(
                    handle_unknown="infrequent_if_exist",
                    min_frequency=20,
                ),
                [0, 1],  # status_raw e turno
            ),
            ("booleano", "passthrough", [2]),  # tem_obs
        ]
    )

    forest = RandomForestClassifier(
        n_estimators=200,
        max_depth=8,
        min_samples_leaf=10,
        class_weight="balanced_subsample",
        random_state=random_state,
        n_jobs=-1,
    )

    base_pipeline = Pipeline([
        ("preprocessor", preprocessor),
        ("classifier", forest),
    ])

    calibrated_model = CalibratedClassifierCV(
        estimator=base_pipeline,
        method="sigmoid",
        cv=5,
        ensemble=False,
    )
    return calibrated_model


def split_estratificado(X: pd.DataFrame, y: pd.Series, grupos: pd.Series, *, random_state: int = 42):
    """Realiza o split 80/20 estratificado por classe + turno."""
    estrato = y.astype(str) + "_" + grupos.astype(str)
    return train_test_split(X, y, test_size=0.20, random_state=random_state, stratify=estrato)


def calcular_ece(y_true_onehot: np.ndarray, probas: np.ndarray, n_bins: int = 10) -> float:
    """Calcula o Expected Calibration Error (ECE) simplificado."""
    bin_boundaries = np.linspace(0, 1, n_bins + 1)
    ece = 0.0
    total_samples = len(probas)

    confidences = np.max(probas, axis=1)
    predictions = np.argmax(probas, axis=1)
    accuracies = (predictions == np.argmax(y_true_onehot, axis=1)).astype(float)

    for i in range(n_bins):
        bin_lower, bin_upper = bin_boundaries[i], bin_boundaries[i + 1]
        in_bin = (confidences > bin_lower) & (confidences <= bin_upper)
        prop_in_bin = np.mean(in_bin)

        if prop_in_bin > 0:
            accuracy_in_bin = np.mean(accuracies[in_bin])
            avg_confidence_in_bin = np.mean(confidences[in_bin])
            ece += np.abs(accuracy_in_bin - avg_confidence_in_bin) * prop_in_bin

    return float(ece)


def avaliar_modelo(model: Any, X_test: pd.DataFrame, y_test: pd.Series, turnos_test: pd.Series) -> dict[str, Any]:
    """Avalia o modelo de ML no conjunto de teste e retorna um dicionário detalhado de métricas."""
    classes = sorted([c.value for c in ClasseML])
    probas = model.predict_proba(X_test)
    preds = model.predict(X_test)


    acc = float(accuracy_score(y_test, preds))
    macro_prec = float(precision_score(y_test, preds, average="macro"))
    macro_rec = float(recall_score(y_test, preds, average="macro"))
    macro_f1 = float(f1_score(y_test, preds, average="macro"))

    cm = confusion_matrix(y_test, preds, labels=classes).tolist()
    loss = float(log_loss(y_test, probas, labels=classes))

    # Converte y_test para one-hot para Brier / ECE
    y_test_oh = pd.get_dummies(y_test).reindex(columns=classes, fill_value=0).values
    # Brier Score multiclasse: mean(sum((probas - onehot)^2, axis=1))
    brier_mean = float(np.mean(np.sum((probas - y_test_oh) ** 2, axis=1)))

    ece = calcular_ece(y_test_oh, probas)
    high_conf_coverage = float(np.mean(np.max(probas, axis=1) >= 0.85))

    # Métricas por turno
    df_eval = pd.DataFrame({"y_true": y_test, "y_pred": preds, "turno": turnos_test})
    metricas_turno: dict[str, dict[str, float]] = {}
    accuracies_turno = []

    for t in ["A", "B", "C"]:
        sub = df_eval[df_eval["turno"] == t]
        if len(sub) > 0:
            t_acc = float(accuracy_score(sub["y_true"], sub["y_pred"]))
            t_f1 = float(f1_score(sub["y_true"], sub["y_pred"], average="macro"))
            accuracies_turno.append(t_acc)
            metricas_turno[t] = {"accuracy": t_acc, "macro_f1": t_f1}

    max_diff_acc_turno = max(accuracies_turno) - min(accuracies_turno) if accuracies_turno else 0.0

    # Medição de latência unitária em ms (100 amostras)
    sample_df = X_test.iloc[:100]
    latencies = []
    for _ in range(5):
        for idx in range(len(sample_df)):
            single_row = sample_df.iloc[[idx]]
            t0 = time.perf_counter()
            _ = model.predict_proba(single_row)
            latencies.append((time.perf_counter() - t0) * 1000.0)

    lat_p50 = float(np.percentile(latencies, 50))
    lat_p95 = float(np.percentile(latencies, 95))
    lat_mean = float(np.mean(latencies))

    metrics = {
        "accuracy": acc,
        "macro_precision": macro_prec,
        "macro_recall": macro_rec,
        "macro_f1": macro_f1,
        "confusion_matrix": cm,
        "log_loss": loss,
        "brier_score_mean": brier_mean,
        "ece": ece,
        "high_confidence_coverage_085": high_conf_coverage,
        "metricas_por_turno": metricas_turno,
        "max_diff_accuracy_turno": max_diff_acc_turno,
        "latencia_ms": {
            "p50": round(lat_p50, 4),
            "p95": round(lat_p95, 4),
            "mean": round(lat_mean, 4),
        },
    }
    return metrics


def treinar_modelo(dataset_path: Path, model_path: Path) -> dict[str, Any]:
    """Lê o dataset, treina e calibra o modelo, e grava o artefato .pkl e as métricas .json."""
    if not dataset_path.exists():
        raise FileNotFoundError(f"Dataset não encontrado em: {dataset_path}")

    df = pd.read_csv(dataset_path)

    # Normalização preventiva do status_raw
    df["status_raw_norm"] = df["status_raw"].astype(str).apply(normalizar_status_raw)

    X = pd.DataFrame({
        "status_raw": df["status_raw_norm"],
        "turno": df["turno"].astype(str).str.strip().str.upper(),
        "tem_obs": df["tem_obs"].astype(bool),
    })[list(FEATURE_ORDER)]

    y = df["classe"].astype(str)
    turnos = df["turno"].astype(str)

    X_train, X_test, y_train, y_test = split_estratificado(X, y, turnos, random_state=42)
    turnos_test = turnos.loc[X_test.index]

    logger.info(f"Treinando modelo em {len(X_train)} amostras e testando em {len(X_test)}...")

    pipeline = build_pipeline(random_state=42)
    pipeline.fit(X_train, y_train)

    metrics = avaliar_modelo(pipeline, X_test, y_test, turnos_test)

    # Calcula SHA256 do dataset para registrar no bundle
    hasher = hashlib.sha256()
    with open(dataset_path, "rb") as f:
        hasher.update(f.read())
    dataset_sha256 = hasher.hexdigest()

    bundle = {
        "pipeline": pipeline,
        "model_version": "rf-lotes-1.0.0",
        "feature_order": list(FEATURE_ORDER),
        "classes": [item.value for item in ClasseML],
        "thresholds": {"alta": 0.85, "media": 0.65},
        "dataset_sha256": dataset_sha256,
        "trained_at": pd.Timestamp.now().isoformat(),
        "sklearn_version": sklearn.__version__,
    }

    model_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(bundle, model_path)
    logger.info(f"Modelo treinado e salvo com sucesso em {model_path}")

    metrics_path = model_path.with_suffix(".metrics.json")
    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2, ensure_ascii=False)
    logger.info(f"Métricas salvas em {metrics_path}")

    return metrics


def main() -> int:
    dataset_path = Path("data/ml/historico_lotes_sintetico.csv")
    manifest_path = Path("data/ml/dataset_manifest.json")
    model_path = Path("models/classificador_lotes.pkl")

    logger.info("Etapa 1: Gerando dataset sintético de 12.000 linhas...")
    rows = gerar_dataset(total=12_000, seed=42)
    validar_dataset(rows)
    salvar_dataset(rows, dataset_path, manifest_path)

    logger.info("Etapa 2: Treinando modelo Random Forest com CalibratedClassifierCV...")
    metrics = treinar_modelo(dataset_path, model_path)

    logger.info(f"Treino concluído. Macro F1: {metrics['macro_f1']:.4f}, Accuracy: {metrics['accuracy']:.4f}")
    return 0


if __name__ == "__main__":
    main()
