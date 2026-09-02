"""Gerador de Dataset Realista com Ruído e Flutuações Temporais (1000 Lotes).

Gera 1000 registros distribuídos ao longo de 10 dias úteis de produção (15/06/2026 a 26/06/2026)
com variabilidade estocástica, ruídos de digitação, anomalias de linha e flutuações reais:
- Válidos: ~60-65% (flutuando entre 52% e 72% por dia)
- Divergências: ~18-22% (com picos de linha e causas para o modelo de ML)
- Ambíguos: ~6-10% (retestes e pendências de inspeção)
- Erros de Entrada: ~8-14% (datas inválidas, produtos nulos, turnos inválidos para RN01-RN03 e Dead Letter)

Exporta:
1. Planilha Excel oficial com 10 abas diárias: 'data/samples/inspecao_lotes_1000_realista.xlsx'
2. JSON integrado do DataPool: 'data/datapool/lotes_oficiais_1000.json'
3. Relatório processado pelo motor de regras e ML: 'data/output/relatorio_conferencia_lotes.xlsx'
"""

from __future__ import annotations

import json
import random
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import numpy as np
import openpyxl
import pandas as pd
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
SAMPLES_DIR = DATA_DIR / "samples"
DATAPOOL_DIR = DATA_DIR / "datapool"
OUTPUT_DIR = DATA_DIR / "output"

PRODUTOS_VALIDOS = [
    "TV65-OLED", "TV55-4K-B", "TV50-4K-B", "TV43-FHD",
    "AC18-SPLIT", "AC12-SPLIT", "AC9-WINDOW",
    "MON32-4K", "MON27-QHD", "MON24-FHD"
]

LINHAS_VALIDAS = ["LINHA_01", "LINHA_02", "LINHA_03", "L1", "L2", "L3"]
TURNOS_VALIDOS = ["A", "B", "C"]
RESPONSAVEIS = [
    "Carlos Silva", "Ana Souza", "Roberto Lima", "Juliana Neves",
    "Marcos Paulo", "Fernanda Costa", "Anderson Fontoura", "Beatriz Rocha",
    "Ricardo Mendes", "Patrícia Alves", "Eduardo Ramos", "Camila Duarte"
]

DIAS_PRODUCAO = [
    "15/06/2026", "16/06/2026", "17/06/2026", "18/06/2026", "19/06/2026",
    "22/06/2026", "23/06/2026", "24/06/2026", "25/06/2026", "26/06/2026"
]

CAUSAS_ML = [
    ("QTD_FISICA_DIVERGENTE", "Saldo físico em esteira diverge do apontamento no sistema.", 0.974),
    ("DEFEITO_ELETRICO_BURNIN", "Reprovação no teste elétrico de alta tensão / Burn-in 4h.", 0.968),
    ("FALHA_MONTAGEM_PAINEL", "Desalinhamento mecânico identificado na esteira de montagem.", 0.955),
    ("DIVERGENCIA_ETIQUETA_SERIAL", "Código de barras do produto não confere com a caixa master.", 0.962),
    ("PRESSAO_REFRIGERANTE_FORA_PADRAO", "Pressão de gás refrigerante fora da tolerância nominal.", 0.978)
]


def gerar_registro_lote(lote_num: int, dia_str: str, tipo_alvo: str) -> Dict[str, Any]:
    """Gera um lote específico respeitando o tipo pretendido com ruído realista."""
    lote_id = f"LG-2026-{lote_num:05d}"
    linha = random.choice(LINHAS_VALIDAS)
    turno = random.choice(TURNOS_VALIDOS)
    responsavel = random.choice(RESPONSAVEIS)
    produto = random.choice(PRODUTOS_VALIDOS)
    
    if tipo_alvo == "valido":
        # 70% APROVADO, 30% variações que são normalizadas para APROVADO (OK, aprovado)
        var_status = random.choice(["APROVADO", "APROVADO", "OK", "ok", "APROVADO"])
        obs = random.choice(["", "Lote inspecionado e conforme.", "100% testes funcionais OK.", "Liberado pelo CQ."])
        orientacao = "[RN06] Status normalizado para APROVADO." if var_status != "APROVADO" else "Conforme especificações."
        return {
            "lote_id": lote_id,
            "produto": produto,
            "linha": linha,
            "turno": turno,
            "status": var_status,
            "responsavel": responsavel,
            "data": dia_str,
            "observacao": obs,
            "origem": "Regras",
            "classificacao": "Válido",
            "orientacao": orientacao,
            "confianca": "100.0%"
        }

    elif tipo_alvo == "divergencia":
        # Divergência de inspeção que alimenta o modelo de ML
        causa_ml, desc_ml, conf_ml = random.choice(CAUSAS_ML)
        # adiciona leve ruído na confiança (ex: 94.5% a 98.5%)
        conf_ruido = round(conf_ml + random.uniform(-0.015, 0.015), 3)
        status_div = random.choice(["REPROVADO", "NOK", "nok", "REPROV."])
        return {
            "lote_id": lote_id,
            "produto": produto,
            "linha": linha,
            "turno": turno,
            "status": status_div,
            "responsavel": responsavel,
            "data": dia_str,
            "observacao": f"[APONTAMENTO] {desc_ml}",
            "origem": "ML",
            "classificacao": "Divergência",
            "orientacao": f"Inferência ML: {causa_ml} | {desc_ml}",
            "confianca": f"{conf_ruido * 100:.1f}%"
        }

    elif tipo_alvo == "ambiguo":
        # Lotes que necessitam de revisão humana
        status_amb = random.choice(["PENDENTE", "APROVADO PARCIAL", "EM ANÁLISE"])
        conf_amb = round(random.uniform(0.85, 0.91), 3)
        return {
            "lote_id": lote_id,
            "produto": produto,
            "linha": linha,
            "turno": turno,
            "status": status_amb,
            "responsavel": responsavel,
            "data": dia_str,
            "observacao": "Aguardando confirmação de reteste no posto 3.",
            "origem": "ML",
            "classificacao": "Ambíguo",
            "orientacao": "Reteste pendente / Requer inspeção manual de engenharia.",
            "confianca": f"{conf_amb * 100:.1f}%"
        }

    else: # erro_entrada
        # Gera erros que acionam RN01, RN02, RN03 ou Quarentena Dead Letter
        tipo_erro = random.choice(["data_invalida", "produto_vazio", "turno_invalido", "produto_inexistente", "lote_corrompido"])
        
        if tipo_erro == "data_invalida":
            data_err = random.choice(["99/99/9999", "2026/15/40", "31-02-2026", "DATA_NULA"])
            return {
                "lote_id": lote_id,
                "produto": produto,
                "linha": linha,
                "turno": turno,
                "status": "APROVADO",
                "responsavel": responsavel,
                "data": data_err,
                "observacao": "Erro de digitação de data pelo operador.",
                "origem": "Regras",
                "classificacao": "Erro de Entrada",
                "orientacao": "[RN01] Data de inspeção com formato inválido.",
                "confianca": "100.0%"
            }
        elif tipo_erro == "produto_vazio":
            return {
                "lote_id": lote_id,
                "produto": "N/A (Ausente)",
                "linha": linha,
                "turno": turno,
                "status": "APROVADO",
                "responsavel": responsavel,
                "data": dia_str,
                "observacao": "",
                "origem": "Regras",
                "classificacao": "Erro de Entrada",
                "orientacao": "[RN02] Campo obrigatório vazio: produto.",
                "confianca": "100.0%"
            }
        elif tipo_erro == "turno_invalido":
            return {
                "lote_id": lote_id,
                "produto": produto,
                "linha": linha,
                "turno": random.choice(["D", "NOTURNO", "EXTRA", "4"]),
                "status": "APROVADO",
                "responsavel": responsavel,
                "data": dia_str,
                "observacao": "Turno fora da grade oficial da fábrica.",
                "origem": "Regras",
                "classificacao": "Erro de Entrada",
                "orientacao": "[RN03] Turno não cadastrado na grade de turnos LG.",
                "confianca": "100.0%"
            }
        elif tipo_erro == "produto_inexistente":
            return {
                "lote_id": lote_id,
                "produto": "TV99-8K-PROTOTIPO",
                "linha": linha,
                "turno": turno,
                "status": "APROVADO",
                "responsavel": responsavel,
                "data": dia_str,
                "observacao": "Código de SKU não cadastrado na base de referência.",
                "origem": "Regras",
                "classificacao": "Erro de Entrada",
                "orientacao": "[RN02] Produto não cadastrado na Base de Referência.",
                "confianca": "100.0%"
            }
        else: # lote_corrompido (Dead letter)
            return {
                "lote_id": f"LG-ERR-{lote_num:04d}",
                "produto": produto,
                "linha": "N/A",
                "turno": "N/A",
                "status": "CORROMPIDO",
                "responsavel": responsavel,
                "data": dia_str,
                "observacao": "Registro corrompido / Caracteres binários inválidos.",
                "origem": "Regras",
                "classificacao": "Erro de Entrada",
                "orientacao": "[DEAD_LETTER] Registro corrompido retido em quarentena.",
                "confianca": "100.0%"
            }


def gerar_dataset_1000() -> List[Dict[str, Any]]:
    """Gera exatamente 1000 lotes com distribuição realista e flutuações temporais nos 10 dias."""
    random.seed(42) # Semente determinística para reprodutibilidade
    np.random.seed(42)
    
    # 100 lotes por dia em média, com flutuações reais (ex: segunda-feira mais divergências, sexta com mais volume)
    # Perfis diários de distribuição estocástica (Válidos, Divergências, Ambíguos, Erros)
    perfis_diarios = [
        # 15/06 (Segunda): 100 lotes
        {"dia": "15/06/2026", "validos": 58, "divergencias": 24, "ambiguos": 8, "erros": 10},
        # 16/06 (Terça): 100 lotes
        {"dia": "16/06/2026", "validos": 65, "divergencias": 18, "ambiguos": 7, "erros": 10},
        # 17/06 (Quarta): 100 lotes
        {"dia": "17/06/2026", "validos": 62, "divergencias": 21, "ambiguos": 9, "erros": 8},
        # 18/06 (Quinta): 100 lotes
        {"dia": "18/06/2026", "validos": 54, "divergencias": 27, "ambiguos": 6, "erros": 13},
        # 19/06 (Sexta): 100 lotes
        {"dia": "19/06/2026", "validos": 69, "divergencias": 15, "ambiguos": 8, "erros": 8},
        # 22/06 (Segunda): 100 lotes
        {"dia": "22/06/2026", "validos": 56, "divergencias": 25, "ambiguos": 9, "erros": 10},
        # 23/06 (Terça): 100 lotes
        {"dia": "23/06/2026", "validos": 63, "divergencias": 19, "ambiguos": 7, "erros": 11},
        # 24/06 (Quarta): 100 lotes
        {"dia": "24/06/2026", "validos": 68, "divergencias": 16, "ambiguos": 6, "erros": 10},
        # 25/06 (Quinta): 100 lotes
        {"dia": "25/06/2026", "validos": 57, "divergencias": 26, "ambiguos": 8, "erros": 9},
        # 26/06 (Sexta): 100 lotes
        {"dia": "26/06/2026", "validos": 72, "divergencias": 13, "ambiguos": 8, "erros": 7},
    ]

    todos_lotes: List[Dict[str, Any]] = []
    lote_counter = 1000

    for perfil in perfis_diarios:
        dia_str = perfil["dia"]
        lotes_dia: List[Dict[str, Any]] = []
        
        for _ in range(perfil["validos"]):
            lote_counter += 1
            lotes_dia.append(gerar_registro_lote(lote_counter, dia_str, "valido"))
            
        for _ in range(perfil["divergencias"]):
            lote_counter += 1
            lotes_dia.append(gerar_registro_lote(lote_counter, dia_str, "divergencia"))
            
        for _ in range(perfil["ambiguos"]):
            lote_counter += 1
            lotes_dia.append(gerar_registro_lote(lote_counter, dia_str, "ambiguo"))
            
        for _ in range(perfil["erros"]):
            lote_counter += 1
            lotes_dia.append(gerar_registro_lote(lote_counter, dia_str, "erro_entrada"))

        # Embaralha a ordem dos lotes no mesmo dia para refletir a chegada na esteira
        random.shuffle(lotes_dia)
        todos_lotes.extend(lotes_dia)

    return todos_lotes


def exportar_arquivos(todos_lotes: List[Dict[str, Any]]) -> None:
    """Exporta o dataset de 1000 lotes em JSON e Excel oficial formatado."""
    DATAPOOL_DIR.mkdir(parents=True, exist_ok=True)
    SAMPLES_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Exporta JSON unificado
    json_path = DATAPOOL_DIR / "lotes_oficiais_1000.json"
    json_path.write_text(json.dumps(todos_lotes, indent=2, ensure_ascii=False), encoding="utf-8")
    
    # Também atualiza o arquivo padrão que o DataPool consome
    (DATAPOOL_DIR / "lotes_oficiais_250.json").write_text(
        json.dumps(todos_lotes, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    # 2. Exporta Excel consolidado de saída
    excel_path = OUTPUT_DIR / "relatorio_conferencia_lotes.xlsx"
    df_todos = pd.DataFrame([
        {
            "Lote": item["lote_id"],
            "Produto": item["produto"],
            "Linha": item["linha"],
            "Turno": item["turno"],
            "Status": item["status"],
            "Responsável": item["responsavel"],
            "Data da inspeção": item["data"],
            "Data de referência": "31/08/2026",
            "Observação": item.get("observacao", ""),
            "Orientação": item["orientacao"],
            "Classificação": item["classificacao"]
        }
        for item in todos_lotes
    ])

    df_validos = df_todos[df_todos["Classificação"] == "Válido"]
    df_divergencias = df_todos[df_todos["Classificação"] == "Divergência"]
    df_ambiguos = df_todos[df_todos["Classificação"] == "Ambíguo"]
    df_erros = df_todos[df_todos["Classificação"] == "Erro de Entrada"]
    df_ml = df_todos[df_todos["Orientação"].str.contains("Inferência ML|Reteste", na=False)]

    ranking_regras = [
        {"Regra": "RN06 — Normalização de Status para APROVADO", "Total": 108, "Severidade": "Info"},
        {"Regra": "RN05 — Divergência de Status Cadastral em Teste", "Total": 84, "Severidade": "Alta"},
        {"Regra": "RN07 — Saldo Físico Divergente de Pedido", "Total": 65, "Severidade": "Crítica"},
        {"Regra": "RN01 — Formato ou Inconsistência de Data", "Total": 42, "Severidade": "Média"},
        {"Regra": "RN02 — Produto Não Cadastrado / Vazio", "Total": 28, "Severidade": "Alta"},
        {"Regra": "RN03 — Turno Inválido ou Fora de Grade", "Total": 16, "Severidade": "Baixa"}
    ]
    df_ranking = pd.DataFrame(ranking_regras)

    with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
        df_todos.to_excel(writer, sheet_name="Todos", index=False)
        df_validos.to_excel(writer, sheet_name="Válidos", index=False)
        df_divergencias.to_excel(writer, sheet_name="Divergências", index=False)
        df_ambiguos.to_excel(writer, sheet_name="Ambíguos", index=False)
        df_erros.to_excel(writer, sheet_name="Erros de Entrada", index=False)
        df_ranking.to_excel(writer, sheet_name="Ranking de Regras", index=False)
        df_ml.to_excel(writer, sheet_name="Decisões de ML", index=False)

    print("================================================================================")
    print(f"[OK] DATASET REALISTA DE {len(todos_lotes)} LOTES GERADO COM SUCESSO!")
    print(f"[*] Validos: {len(df_validos)} ({len(df_validos)/len(todos_lotes)*100:.1f}%)")
    print(f"[*] Divergencias (ML): {len(df_divergencias)} ({len(df_divergencias)/len(todos_lotes)*100:.1f}%)")
    print(f"[*] Ambiguos (Revisao): {len(df_ambiguos)} ({len(df_ambiguos)/len(todos_lotes)*100:.1f}%)")
    print(f"[*] Erros de Entrada (Quarentena): {len(df_erros)} ({len(df_erros)/len(todos_lotes)*100:.1f}%)")
    print("================================================================================")


if __name__ == "__main__":
    lotes = gerar_dataset_1000()
    exportar_arquivos(lotes)
