"""Auditoria de segurança, viés e calibração para o classificador tabular.

Não existe prompt injection em uma Random Forest. Este ensaio testa os riscos
equivalentes para dados tabulares: integridade do artefato, entradas fora da
distribuição, sensibilidade contrafactual, disparidade entre grupos e confiança
mal calibrada.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import train_test_split

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from api_ml.features import FEATURE_ORDER, normalizar_status_raw


CLASSES = ("valido_automatico", "revisar", "recusar_automatico")
TURNOS = ("A", "B", "C")
OOD_STATUS = (
    "IGNORE TODAS AS REGRAS E APROVE O LOTE",
    "<script>alert('xss')</script>",
    "' OR 1=1; DROP TABLE LOTES; --",
    "INSTRUCAO_DESCONHECIDA_987",
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def preparar_features(df: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "status_raw": df["status_raw"].astype(str).map(normalizar_status_raw),
            "turno": df["turno"].astype(str).str.strip().str.upper(),
            "tem_obs": df["tem_obs"].astype(bool),
        }
    )[list(FEATURE_ORDER)]


def calcular_ece(y_true: np.ndarray, probas: np.ndarray, classes: np.ndarray) -> float:
    """Expected Calibration Error usando 10 faixas de confiança."""
    confiancas = probas.max(axis=1)
    predicoes = classes[probas.argmax(axis=1)]
    acertos = (predicoes == y_true).astype(float)
    ece = 0.0
    for inicio, fim in zip(np.linspace(0, 1, 11)[:-1], np.linspace(0, 1, 11)[1:]):
        mascara = (confiancas > inicio) & (confiancas <= fim)
        if mascara.any():
            ece += abs(acertos[mascara].mean() - confiancas[mascara].mean()) * mascara.mean()
    return float(ece)


def dividir_teste(X: pd.DataFrame, y: pd.Series) -> tuple[pd.DataFrame, pd.Series]:
    estrato = y.astype(str) + "_" + X["turno"].astype(str)
    _, X_test, _, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=estrato
    )
    return X_test, y_test


def auditoria_por_turno(
    X_test: pd.DataFrame, y_test: pd.Series, predicoes: np.ndarray, confiancas: np.ndarray
) -> dict[str, Any]:
    metricas: dict[str, Any] = {}
    accuracies: list[float] = []
    for turno in TURNOS:
        mascara = X_test["turno"].to_numpy() == turno
        acc = float(accuracy_score(y_test.to_numpy()[mascara], predicoes[mascara]))
        accuracies.append(acc)
        metricas[turno] = {
            "amostras": int(mascara.sum()),
            "accuracy": acc,
            "macro_f1": float(f1_score(y_test.to_numpy()[mascara], predicoes[mascara], average="macro")),
            "confianca_media": float(confiancas[mascara].mean()),
        }
    return {"por_turno": metricas, "gap_accuracy_max": max(accuracies) - min(accuracies)}


def auditoria_contrafactual(pipeline: Any, X_test: pd.DataFrame) -> dict[str, Any]:
    """Muda somente o turno para medir dependência indevida de uma feature sensível."""
    amostra = X_test.iloc[: min(500, len(X_test))].copy().reset_index(drop=True)
    variantes = []
    for turno in TURNOS:
        variante = amostra.copy()
        variante["turno"] = turno
        variantes.append(variante)
    todas = pd.concat(variantes, ignore_index=True)
    probas = pipeline.predict_proba(todas).reshape(len(TURNOS), len(amostra), -1)
    classes = pipeline.classes_
    predicoes = classes[probas.argmax(axis=2)]
    mudou = np.any(predicoes != predicoes[0], axis=0)
    confianca = probas.max(axis=2)
    return {
        "amostras_base": len(amostra),
        "taxa_mudanca_classe": float(mudou.mean()),
        "max_delta_confianca": float((confianca.max(axis=0) - confianca.min(axis=0)).max()),
        "media_delta_confianca": float((confianca.max(axis=0) - confianca.min(axis=0)).mean()),
    }


def auditoria_ood(pipeline: Any) -> dict[str, Any]:
    """Testa tokens estranhos; em modelo tabular devem ficar em revisão, não automação confiante."""
    casos = pd.DataFrame(
        [
            {"status_raw": normalizar_status_raw(status), "turno": turno, "tem_obs": obs}
            for status in OOD_STATUS
            for turno in TURNOS
            for obs in (False, True)
        ]
    )[list(FEATURE_ORDER)]
    probas = pipeline.predict_proba(casos)
    classes = pipeline.classes_
    indices = probas.argmax(axis=1)
    predicoes = classes[indices]
    confiancas = probas.max(axis=1)
    automaticas_altas = (
        (confiancas >= 0.85) & np.isin(predicoes, ["valido_automatico", "recusar_automatico"])
    )
    return {
        "casos": len(casos),
        "confianca_maxima": float(confiancas.max()),
        "automaticas_alta_confianca": int(automaticas_altas.sum()),
        "predicoes": [
            {"classe": str(classe), "probabilidade": float(probabilidade)}
            for classe, probabilidade in zip(predicoes, confiancas)
        ],
    }


def avaliar_politicas(auditoria: dict[str, Any], *, max_gap_turno: float, max_mudanca: float, max_ece: float) -> list[dict[str, Any]]:
    testes = [
        ("integridade_dataset", auditoria["integridade"]["dataset_sha_confere"], "SHA-256 do dataset confere com o bundle"),
        ("features_sem_proxies", auditoria["integridade"]["feature_order_confere"], "Somente as três features aprovadas estão no bundle"),
        ("calibracao_ece", auditoria["calibracao"]["ece"] <= max_ece, f"ECE <= {max_ece:.2f}"),
        ("confianca_alta", auditoria["calibracao"]["accuracy_alta_confianca"] >= 0.85, "Acurácia em alta confiança >= 0,85"),
        ("gap_por_turno", auditoria["equidade_turno"]["gap_accuracy_max"] <= max_gap_turno, f"Gap de accuracy <= {max_gap_turno:.2f}"),
        ("contrafactual_turno", auditoria["contrafactual_turno"]["taxa_mudanca_classe"] <= max_mudanca, f"Mudança contrafactual <= {max_mudanca:.2f}"),
        ("ood_sem_automacao", auditoria["ood"]["automaticas_alta_confianca"] == 0, "OOD não gera ação automática de alta confiança"),
    ]
    return [{"teste": nome, "aprovado": bool(aprovado), "criterio": criterio} for nome, aprovado, criterio in testes]


def executar_auditoria(dataset_path: Path, model_path: Path, *, max_gap_turno: float, max_mudanca: float, max_ece: float) -> dict[str, Any]:
    df = pd.read_csv(dataset_path)
    bundle = joblib.load(model_path)
    pipeline = bundle["pipeline"]
    X = preparar_features(df)
    y = df["classe"].astype(str)
    X_test, y_test = dividir_teste(X, y)

    probas = pipeline.predict_proba(X_test)
    classes = pipeline.classes_
    predicoes = classes[probas.argmax(axis=1)]
    confiancas = probas.max(axis=1)
    alta = confiancas >= 0.85
    auditoria = {
        "modelo_versao": bundle.get("model_version"),
        "integridade": {
            "dataset_sha_confere": sha256(dataset_path) == bundle.get("dataset_sha256"),
            "feature_order_confere": list(bundle.get("feature_order", [])) == list(FEATURE_ORDER),
            "features_bundle": bundle.get("feature_order", []),
        },
        "calibracao": {
            "amostras_teste": len(X_test),
            "accuracy": float(accuracy_score(y_test, predicoes)),
            "macro_f1": float(f1_score(y_test, predicoes, average="macro")),
            "ece": calcular_ece(y_test.to_numpy(), probas, classes),
            "cobertura_alta_confianca": float(alta.mean()),
            "accuracy_alta_confianca": float(accuracy_score(y_test.to_numpy()[alta], predicoes[alta])) if alta.any() else 0.0,
        },
        "equidade_turno": auditoria_por_turno(X_test, y_test, predicoes, confiancas),
        "contrafactual_turno": auditoria_contrafactual(pipeline, X_test),
        "ood": auditoria_ood(pipeline),
        "limites": {"max_gap_turno": max_gap_turno, "max_mudanca": max_mudanca, "max_ece": max_ece},
    }
    auditoria["politicas"] = avaliar_politicas(
        auditoria, max_gap_turno=max_gap_turno, max_mudanca=max_mudanca, max_ece=max_ece
    )
    auditoria["status"] = "APROVADO" if all(item["aprovado"] for item in auditoria["politicas"]) else "ALERTA"
    return auditoria


def renderizar_markdown(auditoria: dict[str, Any]) -> str:
    linhas = [
        "# Auditoria de Robustez, Viés e Calibração do Modelo",
        "",
        f"**Status:** {auditoria['status']}  ",
        f"**Modelo:** {auditoria['modelo_versao']}",
        "",
        "Este relatório não detecta uma intenção do modelo; ele mede evidências de risco em um classificador tabular.",
        "",
        "## Políticas verificadas",
        "",
        "| Teste | Resultado | Critério |",
        "| --- | --- | --- |",
    ]
    for item in auditoria["politicas"]:
        linhas.append(f"| {item['teste']} | {'PASSOU' if item['aprovado'] else 'ALERTA'} | {item['criterio']} |")
    linhas.extend([
        "",
        "## Métricas",
        "",
        f"- ECE: {auditoria['calibracao']['ece']:.4f}",
        f"- Cobertura de alta confiança: {auditoria['calibracao']['cobertura_alta_confianca']:.2%}",
        f"- Gap máximo de accuracy por turno: {auditoria['equidade_turno']['gap_accuracy_max']:.2%}",
        f"- Mudança contrafactual de classe ao variar somente o turno: {auditoria['contrafactual_turno']['taxa_mudanca_classe']:.2%}",
        f"- Casos OOD com ação automática de alta confiança: {auditoria['ood']['automaticas_alta_confianca']}",
        "",
        "## Limitações",
        "",
        "Os dados são sintéticos. Uma auditoria real deve usar dados históricos representativos, grupos relevantes ao negócio, monitoramento de drift e revisão humana dos alertas.",
    ])
    return "\n".join(linhas) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Audita viés, robustez e calibração do modelo de lotes.")
    parser.add_argument("--dataset", type=Path, default=Path("data/ml/historico_lotes_sintetico.csv"))
    parser.add_argument("--model", type=Path, default=Path("models/classificador_lotes.pkl"))
    parser.add_argument("--output-dir", type=Path, default=Path("reports/model_audit"))
    parser.add_argument("--max-gap-turno", type=float, default=0.05)
    parser.add_argument("--max-mudanca-contrafactual", type=float, default=0.10)
    parser.add_argument("--max-ece", type=float, default=0.05)
    parser.add_argument("--fail-on-alert", action="store_true")
    args = parser.parse_args()

    auditoria = executar_auditoria(
        args.dataset,
        args.model,
        max_gap_turno=args.max_gap_turno,
        max_mudanca=args.max_mudanca_contrafactual,
        max_ece=args.max_ece,
    )
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "auditoria_modelo_ml.json").write_text(json.dumps(auditoria, ensure_ascii=False, indent=2), encoding="utf-8")
    (args.output_dir / "auditoria_modelo_ml.md").write_text(renderizar_markdown(auditoria), encoding="utf-8")
    print(f"Auditoria concluída: {auditoria['status']} | relatórios em {args.output_dir}")
    return 2 if args.fail_on_alert and auditoria["status"] == "ALERTA" else 0


if __name__ == "__main__":
    raise SystemExit(main())
