"""Gera o relatório executivo da conferência dos lotes de inspeção.

O arquivo de entrada possui duas linhas de apresentação; por isso os cabeçalhos
estão na linha 3 e os dados começam na linha 4. Cada aba diária declara a
quantidade de registros no texto de apresentação, evitando que o rodapé da
planilha seja interpretado como dado.
"""

from __future__ import annotations

import argparse
import logging
import re
import sys
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
from openpyxl import load_workbook
from openpyxl.chart import DoughnutChart, LineChart, Reference
from openpyxl.chart.label import DataLabelList
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.table import Table, TableStyleInfo

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.base_referencia import carregar_base_referencia
from src.regras_negocio import normalizar_status, validar_dominio_status
from src.validacao import CAMPOS_OBRIGATORIOS, valida_campos_obrigatorios, valida_estrutura, validar_observacao_reprovado


ARQUIVO_ENTRADA_PADRAO = ROOT / "data" / "samples" / "inspecao_lotes_10dias_sem gabarito.xlsx"
DIRETORIO_SAIDA_PADRAO = ROOT / "data" / "output"
CLASSIFICACOES = ("Válido", "Divergência", "Ambíguo", "Erro de Entrada")
ABAS_DIARIAS = re.compile(r"^Insp_(\d{2})_(\d{2})_(\d{4})$")


def _texto(valor: Any) -> str:
    """Converte valores da planilha sem transformar nulos no texto ``nan``."""
    return "" if pd.isna(valor) else str(valor).strip()


def _vazio(valor: Any) -> bool:
    return not _texto(valor)


def _data_da_aba(nome_aba: str) -> str:
    correspondencia = ABAS_DIARIAS.match(nome_aba)
    if not correspondencia:
        raise ValueError(f"Nome de aba diária inválido: {nome_aba}")
    dia, mes, ano = correspondencia.groups()
    return f"{dia}/{mes}/{ano}"


def _data_valida(valor: Any, referencia: str) -> bool:
    """RN12: exige o formato dd/mm/aaaa e a data da respectiva execução."""
    texto = _texto(valor)
    if not re.fullmatch(r"\d{2}/\d{2}/\d{4}", texto):
        return False
    try:
        return datetime.strptime(texto, "%d/%m/%Y").strftime("%d/%m/%Y") == referencia
    except ValueError:
        return False


@dataclass
class RegistroValidado:
    """Registro auditável, com classificação única e todas as regras acionadas."""

    valores: dict[str, Any]
    regras: list[str] = field(default_factory=list)
    descricao: list[str] = field(default_factory=list)
    classificacao: str = "Válido"

    def adicionar(self, regra: str, descricao: str) -> None:
        if regra not in self.regras:
            self.regras.append(regra)
            self.descricao.append(descricao)

    def para_dicionario(self) -> dict[str, Any]:
        return {**self.valores, "regras_violadas": "; ".join(self.regras), "descricao_validacao": " | ".join(self.descricao), "classificacao": self.classificacao}


def carregar_inspecoes(caminho: str | Path) -> pd.DataFrame:
    """Lê as dez abas diárias, respeitando a linha 3 como cabeçalho."""
    caminho = Path(caminho)
    frames: list[pd.DataFrame] = []
    with pd.ExcelFile(caminho) as arquivo:
        abas = [aba for aba in arquivo.sheet_names if ABAS_DIARIAS.match(aba)]
        if len(abas) != 10:
            raise ValueError(f"Esperadas 10 abas de inspeção; encontradas {len(abas)}.")
        for aba in abas:
            apresentacao = pd.read_excel(arquivo, sheet_name=aba, header=None, nrows=2)
            texto_apresentacao = " ".join(apresentacao.fillna("").astype(str).to_numpy().ravel())
            encontrado = re.search(r"Registros:\s*(\d+)", texto_apresentacao, flags=re.I)
            if not encontrado:
                raise ValueError(f"Quantidade de registros não encontrada na aba {aba}.")
            quantidade = int(encontrado.group(1))
            diario = pd.read_excel(arquivo, sheet_name=aba, skiprows=2, nrows=quantidade)
            valida_estrutura(diario)
            diario["aba_origem"] = aba
            diario["linha_origem"] = range(4, 4 + len(diario))
            diario["data_referencia"] = _data_da_aba(aba)
            frames.append(diario)
    consolidado = pd.concat(frames, ignore_index=True)
    if len(consolidado) != 250:
        raise ValueError(f"Foram lidos {len(consolidado)} registros; o esperado é 250.")
    return consolidado


def validar_registros(df: pd.DataFrame, lotes_referencia: set[str]) -> pd.DataFrame:
    """Aplica RN01--RN12 e devolve uma classificação exclusiva por registro.

    A precedência mantém as abas isoladas: Erro de Entrada, Ambíguo,
    Divergência e Válido. RN11 usa Counter por aba e marca só a repetição.
    """
    obrigatorios = valida_campos_obrigatorios(df.drop(columns=["aba_origem", "linha_origem", "data_referencia"]))
    indices_obrigatorios = set(obrigatorios["index"].tolist())
    repetidos: set[int] = set()
    for _, diario in df.groupby("aba_origem", sort=False):
        ids = [_texto(valor) for valor in diario["lote_id"]]
        contador = Counter(lote_id for lote_id in ids if lote_id)
        vistos: Counter[str] = Counter()
        for indice, lote_id in zip(diario.index, ids):
            vistos[lote_id] += 1
            if lote_id and contador[lote_id] > 1 and vistos[lote_id] > 1:
                repetidos.add(indice)

    registros: list[dict[str, Any]] = []
    for indice, linha in df.iterrows():
        dados = {coluna: _texto(linha[coluna]) for coluna in df.columns}
        registro = RegistroValidado(dados)
        normalizado = normalizar_status({"status": linha["status"]})
        dados["status_original"] = _texto(normalizado.get("status_original"))
        dados["status_normalizado"] = _texto(normalizado.get("status"))
        status_final = dados["status_normalizado"]

        if indice in indices_obrigatorios:
            campos = [campo for campo in CAMPOS_OBRIGATORIOS if campo != "data" and _vazio(linha[campo])]
            if campos:
                registro.adicionar("RN01-RN04", f"Campos obrigatórios vazios: {', '.join(campos)}.")
        if not _data_valida(linha["data"], dados["data_referencia"]):
            registro.adicionar("RN12", f"Data deve ser {dados['data_referencia']} no formato dd/mm/aaaa.")
        lote_id = dados["lote_id"]
        if lote_id and lote_id not in lotes_referencia:
            registro.adicionar("RN05", "lote_id não encontrado na Base_Referencia.")
        if dados["status_original"] == "OK":
            registro.adicionar("RN06", "Status OK normalizado para APROVADO.")
        elif dados["status_original"] == "NOK":
            registro.adicionar("RN07", "Status NOK normalizado para REPROVADO.")
        dominio = validar_dominio_status({"status": status_final})
        if status_final and dominio.get("status_ambiguo", False):
            registro.adicionar("RN09", f"Status '{status_final}' desconhecido; encaminhar para revisão humana.")
        observacao = validar_observacao_reprovado({"status": status_final, "observacao": linha["observacao"]})
        if observacao.get("divergencias"):
            registro.adicionar("RN10", "Status REPROVADO exige observação preenchida.")
        if indice in repetidos:
            registro.adicionar("RN11", "lote_id duplicado na mesma execução diária.")

        regras = set(registro.regras)
        if regras.intersection({"RN01-RN04", "RN12"}):
            registro.classificacao = "Erro de Entrada"
        elif "RN09" in regras:
            registro.classificacao = "Ambíguo"
        elif regras.intersection({"RN05", "RN10", "RN11"}):
            registro.classificacao = "Divergência"
        registros.append(registro.para_dicionario())
    resultado = pd.DataFrame(registros)
    if len(resultado) != len(df) or not resultado["classificacao"].isin(CLASSIFICACOES).all():
        raise RuntimeError("Falha ao classificar os registros do relatório.")
    return resultado


def _ajustar_aba(ws) -> None:
    cabecalho = PatternFill("solid", fgColor="1F4E78")
    for celula in ws[1]:
        celula.fill = cabecalho
        celula.font = Font(color="FFFFFF", bold=True)
        celula.alignment = Alignment(horizontal="center")
    ws.freeze_panes = "A2"
    ws.auto_filter.ref = ws.dimensions
    for coluna in range(1, ws.max_column + 1):
        valores = [len(str(ws.cell(linha, coluna).value or "")) for linha in range(1, min(ws.max_row, 100) + 1)]
        ws.column_dimensions[get_column_letter(coluna)].width = min(max(valores, default=10) + 2, 45)
    if ws.max_row > 1 and ws.max_column:
        tabela = Table(displayName=f"Tabela{re.sub(r'[^A-Za-z0-9]', '', ws.title)}", ref=ws.dimensions)
        tabela.tableStyleInfo = TableStyleInfo(name="TableStyleMedium2", showRowStripes=True)
        ws.add_table(tabela)


def _montar_resumo(writer: pd.ExcelWriter, resultado: pd.DataFrame) -> None:
    totais = resultado["classificacao"].value_counts().reindex(CLASSIFICACOES, fill_value=0)
    total = len(resultado)
    pd.DataFrame({"Classificação": CLASSIFICACOES, "Quantidade": totais.tolist(), "Percentual": [valor / total for valor in totais.tolist()]}).to_excel(writer, sheet_name="Resumo", startrow=4, index=False)
    evolucao = (resultado.assign(alerta=resultado["classificacao"].isin(["Divergência", "Ambíguo"]).astype(int)).groupby("data_referencia", sort=False)["alerta"].sum().reset_index(name="Divergências + Ambíguos"))
    evolucao.to_excel(writer, sheet_name="Resumo", startrow=12, index=False)
    ws = writer.book["Resumo"]
    ws["A1"] = "Dashboard Executivo — Conferência de Lotes"
    ws["A1"].font = Font(size=16, bold=True, color="FFFFFF")
    ws["A1"].fill = PatternFill("solid", fgColor="1F4E78")
    ws.merge_cells("A1:D1")
    ws["A2"], ws["B2"] = "Processado em", datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    ws["A3"], ws["B3"] = "Total de registros processados", total
    ws["B3"].font = Font(size=14, bold=True, color="1F4E78")
    for linha in range(6, 10):
        ws.cell(linha, 3).number_format = "0.0%"
    donut = DoughnutChart()
    donut.title = "Distribuição por classificação"
    donut.add_data(Reference(ws, min_col=2, min_row=5, max_row=9), titles_from_data=True)
    donut.set_categories(Reference(ws, min_col=1, min_row=6, max_row=9))
    donut.holeSize = 55
    donut.dataLabels = DataLabelList()
    donut.dataLabels.showPercent = True
    ws.add_chart(donut, "F2")
    linhas = LineChart()
    linhas.title = "Evolução diária de alertas"
    linhas.y_axis.title, linhas.x_axis.title = "Registros", "Data de referência"
    linhas.add_data(Reference(ws, min_col=2, min_row=13, max_row=23), titles_from_data=True)
    linhas.set_categories(Reference(ws, min_col=1, min_row=14, max_row=23))
    linhas.height, linhas.width = 7, 15
    ws.add_chart(linhas, "F18")
    ws.column_dimensions["A"].width, ws.column_dimensions["B"].width, ws.column_dimensions["C"].width = 28, 18, 14


def _exportar_pdf(resumo: dict[str, int], destino: Path) -> Path | None:
    """Gera um PDF simples do resumo quando reportlab estiver disponível."""
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen.canvas import Canvas
    except ImportError:
        return None
    pdf = Canvas(str(destino), pagesize=A4)
    pdf.setTitle("Resumo Executivo — Conferência de Lotes")
    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawString(48, 790, "Resumo Executivo — Conferência de Lotes")
    pdf.setFont("Helvetica", 11)
    pdf.drawString(48, 765, f"Gerado em {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    y = 720
    for rotulo, quantidade in resumo.items():
        pdf.drawString(60, y, f"{rotulo}: {quantidade}")
        y -= 28
    pdf.save()
    return destino


def gerar_relatorio(caminho_entrada: str | Path = ARQUIVO_ENTRADA_PADRAO, diretorio_saida: str | Path = DIRETORIO_SAIDA_PADRAO) -> Path:
    """Processa a planilha e grava as 6 abas e os artefatos de execução."""
    caminho_entrada, diretorio_saida = Path(caminho_entrada), Path(diretorio_saida)
    diretorio_saida.mkdir(parents=True, exist_ok=True)
    registros = carregar_inspecoes(caminho_entrada)
    resultado = validar_registros(registros, carregar_base_referencia(caminho_entrada))
    totais = resultado["classificacao"].value_counts().reindex(CLASSIFICACOES, fill_value=0)
    if int(totais.sum()) != 250 or int(totais["Divergência"] + totais["Ambíguo"] + totais["Erro de Entrada"]) != 100:
        raise RuntimeError(f"Totais inesperados: {totais.to_dict()}")
    destino = diretorio_saida / "relatorio_conferencia_lotes.xlsx"
    with pd.ExcelWriter(destino, engine="openpyxl") as writer:
        _montar_resumo(writer, resultado)
        resultado.to_excel(writer, sheet_name="Todos", index=False)
        resultado.loc[resultado["classificacao"] == "Válido"].to_excel(writer, sheet_name="Válidos", index=False)
        resultado.loc[resultado["classificacao"] == "Divergência"].to_excel(writer, sheet_name="Divergências", index=False)
        resultado.loc[resultado["classificacao"] == "Ambíguo"].to_excel(writer, sheet_name="Ambiguos", index=False)
        resultado.loc[resultado["classificacao"] == "Erro de Entrada"].to_excel(writer, sheet_name="Erros de Entrada", index=False)
        for nome in ("Todos", "Válidos", "Divergências", "Ambiguos", "Erros de Entrada"):
            _ajustar_aba(writer.book[nome])
    load_workbook(destino).save(destino)
    resumo_log = {"total": int(len(resultado)), **{classe: int(totais[classe]) for classe in CLASSIFICACOES}}
    logging.basicConfig(filename=diretorio_saida / "execucao_dashboard.log", level=logging.INFO, encoding="utf-8", force=True)
    logging.info("Relatório gerado | entrada=%s | totais=%s", caminho_entrada.name, resumo_log)
    logging.shutdown()
    _exportar_pdf(resumo_log, diretorio_saida / "resumo_conferencia_lotes.pdf")
    return destino


def main() -> None:
    parser = argparse.ArgumentParser(description="Gera o relatório executivo de conferência de lotes.")
    parser.add_argument("--entrada", type=Path, default=ARQUIVO_ENTRADA_PADRAO)
    parser.add_argument("--saida", type=Path, default=DIRETORIO_SAIDA_PADRAO)
    args = parser.parse_args()
    print(gerar_relatorio(args.entrada, args.saida))


if __name__ == "__main__":
    main()
