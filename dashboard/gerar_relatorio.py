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
import unicodedata
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd
from openpyxl.chart import DoughnutChart, LineChart, Reference
from openpyxl.chart.label import DataLabelList
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.table import Table, TableStyleInfo

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.base_referencia import carregar_base_referencia
from dashboard.servico_validacao import (
    ABAS_DIARIAS,
    CLASSIFICACOES,
    data_da_aba,
    texto,
    validar_registro,
)
from src.validacao import valida_estrutura


ARQUIVO_ENTRADA_PADRAO = ROOT / "data" / "samples" / "inspecao_lotes_10dias_sem gabarito.xlsx"
DIRETORIO_SAIDA_PADRAO = ROOT / "data" / "output"
COLUNAS_RELATORIO = {
    "lote_id": "Lote",
    "produto": "Produto",
    "linha": "Linha",
    "turno": "Turno",
    "status_normalizado": "Status",
    "responsavel": "Responsável",
    "data": "Data da inspeção",
    "data_referencia": "Data de referência",
    "observacao": "Observação",
    "descricao_validacao": "Orientação",
    "classificacao": "Classificação",
}
FUSO_MANAUS = timezone(timedelta(hours=-4), name="America/Manaus")


def _agora_manaus() -> datetime:
    """Retorna um instante com fuso explícito, inclusive dentro do Docker."""
    return datetime.now(FUSO_MANAUS)


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
            diario["data_referencia"] = data_da_aba(aba)
            frames.append(diario)
    consolidado = pd.concat(frames, ignore_index=True)
    if len(consolidado) != 250:
        raise ValueError(f"Foram lidos {len(consolidado)} registros; o esperado é 250.")
    return consolidado


def validar_registros(df: pd.DataFrame, lotes_referencia: set[str]) -> pd.DataFrame:
    """Deduplica por dia e chama o Serviço de Validação para cada linha."""
    repetidos: set[int] = set()
    for _, diario in df.groupby("aba_origem", sort=False):
        ids = [texto(valor) for valor in diario["lote_id"]]
        contador = Counter(lote_id for lote_id in ids if lote_id)
        vistos: Counter[str] = Counter()
        for indice, lote_id in zip(diario.index, ids):
            vistos[lote_id] += 1
            if lote_id and contador[lote_id] > 1 and vistos[lote_id] > 1:
                repetidos.add(indice)

    registros: list[dict[str, object]] = []
    for indice, linha in df.iterrows():
        registro = validar_registro(
            linha.to_dict(),
            lotes_referencia,
            duplicado_no_dia=indice in repetidos,
        )
        registros.append(registro.to_dict())
    resultado = pd.DataFrame(registros)
    if len(resultado) != len(df) or not resultado["classificacao"].isin(CLASSIFICACOES).all():
        raise RuntimeError("Falha ao classificar os registros do relatório.")
    return resultado


def preparar_dados_relatorio(resultado: pd.DataFrame) -> pd.DataFrame:
    """Expõe no Excel somente campos compreensíveis ao público de negócio."""
    return resultado.loc[:, list(COLUNAS_RELATORIO)].rename(
        columns=COLUNAS_RELATORIO
    )


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
    evolucao = _calcular_evolucao_alertas(resultado)
    evolucao.to_excel(writer, sheet_name="Resumo", startrow=12, index=False)
    ws = writer.book["Resumo"]
    ws["A1"] = "Dashboard Executivo — Conferência de Lotes"
    ws["A1"].font = Font(size=16, bold=True, color="FFFFFF")
    ws["A1"].fill = PatternFill("solid", fgColor="1F4E78")
    ws.merge_cells("A1:D1")
    ws["A2"], ws["B2"] = "Processado em", _agora_manaus().strftime(
        "%d/%m/%Y %H:%M:%S"
    )
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
    linhas.title = "Evolução dos registros"
    linhas.y_axis.title, linhas.x_axis.title = "Registros", "Data de referência"
    linhas.add_data(Reference(ws, min_col=2, min_row=13, max_row=23), titles_from_data=True)
    linhas.set_categories(Reference(ws, min_col=1, min_row=14, max_row=23))
    linhas.height, linhas.width = 7, 15
    ws.add_chart(linhas, "F18")
    ws.column_dimensions["A"].width, ws.column_dimensions["B"].width, ws.column_dimensions["C"].width = 28, 18, 14


def _calcular_evolucao_alertas(resultado: pd.DataFrame) -> pd.DataFrame:
    return (
        resultado.assign(
            alerta=resultado["classificacao"].isin(
                ["Divergência", "Ambíguo"]
            ).astype(int)
        )
        .groupby("data_referencia", sort=False)["alerta"]
        .sum()
        .reset_index(name="Divergências + Ambíguos")
    )


def _escapar_texto_pdf(texto: str) -> str:
    """Converte texto para o conjunto simples suportado pelo PDF de reserva."""
    texto_ascii = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore")
    return texto_ascii.decode("ascii").replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _exportar_pdf_basico(resumo: dict[str, int], destino: Path) -> Path:
    """Gera um PDF valido sem depender de bibliotecas opcionais."""
    linhas = [
        "BT",
        "/F1 18 Tf",
        "48 790 Td",
        "(Resumo Executivo - Conferencia de Lotes) Tj",
        "/F1 11 Tf",
        "0 -25 Td",
        f"(Gerado em {_escapar_texto_pdf(_agora_manaus().strftime('%d/%m/%Y %H:%M:%S'))}) Tj",
    ]
    for rotulo, quantidade in resumo.items():
        linhas.extend(("0 -28 Td", f"({_escapar_texto_pdf(rotulo)}: {quantidade}) Tj"))
    linhas.append("ET")
    conteudo = "\n".join(linhas).encode("ascii")
    objetos = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Length " + str(len(conteudo)).encode() + b" >>\nstream\n" + conteudo + b"\nendstream",
    ]
    partes = [b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n"]
    offsets = [0]
    for numero, objeto in enumerate(objetos, start=1):
        offsets.append(sum(len(parte) for parte in partes))
        partes.append(f"{numero} 0 obj\n".encode() + objeto + b"\nendobj\n")
    inicio_xref = sum(len(parte) for parte in partes)
    xref = [f"xref\n0 {len(objetos) + 1}\n", "0000000000 65535 f \n"]
    xref.extend(f"{offset:010d} 00000 n \n" for offset in offsets[1:])
    partes.append("".join(xref).encode())
    partes.append(
        f"trailer\n<< /Size {len(objetos) + 1} /Root 1 0 R >>\nstartxref\n{inicio_xref}\n%%EOF\n".encode()
    )
    destino.write_bytes(b"".join(partes))
    return destino


def _exportar_pdf(
    resumo: dict[str, int], evolucao: pd.DataFrame, destino: Path
) -> Path:
    """Exporta uma versão visual dos indicadores e gráficos da aba Resumo."""
    try:
        from reportlab.graphics import renderPDF
        from reportlab.graphics.charts.linecharts import HorizontalLineChart
        from reportlab.graphics.charts.piecharts import Pie
        from reportlab.graphics.shapes import Circle, Drawing
        from reportlab.lib.colors import HexColor
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen.canvas import Canvas
    except ImportError:
        return _exportar_pdf_basico(resumo, destino)

    pdf = Canvas(str(destino), pagesize=A4)
    pdf.setTitle("Resumo Executivo — Conferência de Lotes")
    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawString(48, 790, "Resumo Executivo — Conferência de Lotes")
    pdf.setFont("Helvetica", 11)
    pdf.drawString(
        48, 765, f"Gerado em {_agora_manaus().strftime('%d/%m/%Y %H:%M:%S')}"
    )

    pdf.setFont("Helvetica-Bold", 10)
    pdf.drawString(48, 730, "Total de registros")
    pdf.setFont("Helvetica", 20)
    pdf.drawString(48, 705, str(resumo["total"]))
    for x, rotulo in zip((48, 178, 308, 438), CLASSIFICACOES):
        pdf.setFont("Helvetica-Bold", 9)
        pdf.drawString(x, 665, rotulo)
        pdf.setFont("Helvetica", 18)
        pdf.drawString(x, 642, str(resumo[rotulo]))

    desenho = Drawing(500, 330)
    rosquinha = Pie()
    rosquinha.x, rosquinha.y = 10, 100
    rosquinha.width, rosquinha.height = 180, 180
    rosquinha.data = [resumo[classe] for classe in CLASSIFICACOES]
    rosquinha.labels = [
        f"{classe}: {resumo[classe] / resumo['total']:.0%}"
        for classe in CLASSIFICACOES
    ]
    rosquinha.slices.strokeWidth = 0
    for indice, cor in enumerate(("#5C0011", "#8A1024", "#B71C35", "#D94B62")):
        rosquinha.slices[indice].fillColor = HexColor(cor)
    desenho.add(rosquinha)
    desenho.add(
        Circle(
            rosquinha.x + rosquinha.width / 2,
            rosquinha.y + rosquinha.height / 2,
            42,
            fillColor=HexColor("#FFFFFF"),
            strokeColor=None,
        )
    )

    linha = HorizontalLineChart()
    linha.x, linha.y = 260, 115
    linha.width, linha.height = 210, 150
    linha.data = [evolucao["Divergências + Ambíguos"].tolist()]
    linha.categoryNames = [
        data[:5] for data in evolucao["data_referencia"].tolist()
    ]
    linha.lines[0].strokeColor = HexColor("#B71C35")
    linha.lines[0].strokeWidth = 2
    linha.valueAxis.valueMin = 0
    linha.valueAxis.valueMax = max(linha.data[0]) + 1
    linha.valueAxis.valueStep = 1
    linha.categoryAxis.labels.angle = 45
    linha.categoryAxis.labels.boxAnchor = "ne"
    linha.categoryAxis.labels.fontSize = 6
    linha.categoryAxis.labels.dy = -5
    desenho.add(linha)
    renderPDF.draw(desenho, pdf, 48, 300)

    # O renderizador do ReportLab não exibe os rótulos de categoria de
    # forma consistente. Desenhá-los no canvas garante os dez dias no PDF.
    pdf.setFont("Helvetica", 6)
    datas_reduzidas = [data[:5] for data in evolucao["data_referencia"]]
    for indice, data in enumerate(datas_reduzidas):
        x_rotulo = 48 + linha.x + (indice + 0.5) * linha.width / len(
            datas_reduzidas
        )
        pdf.saveState()
        pdf.translate(x_rotulo, 405)
        pdf.rotate(45)
        pdf.drawRightString(0, 0, data)
        pdf.restoreState()

    pdf.setFont("Helvetica-Bold", 11)
    pdf.drawString(48, 280, "Distribuição por classificação")
    pdf.drawString(308, 280, "Evolução dos registros")
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
    relatorio = preparar_dados_relatorio(resultado)
    with pd.ExcelWriter(destino, engine="openpyxl") as writer:
        _montar_resumo(writer, resultado)
        relatorio.to_excel(writer, sheet_name="Todos", index=False)
        relatorio.loc[relatorio["Classificação"] == "Válido"].to_excel(writer, sheet_name="Válidos", index=False)
        relatorio.loc[relatorio["Classificação"] == "Divergência"].to_excel(writer, sheet_name="Divergências", index=False)
        relatorio.loc[relatorio["Classificação"] == "Ambíguo"].to_excel(writer, sheet_name="Ambíguos", index=False)
        relatorio.loc[relatorio["Classificação"] == "Erro de Entrada"].to_excel(writer, sheet_name="Erros de Entrada", index=False)
        for nome in ("Todos", "Válidos", "Divergências", "Ambíguos", "Erros de Entrada"):
            _ajustar_aba(writer.book[nome])
    resumo_log = {"total": int(len(resultado)), **{classe: int(totais[classe]) for classe in CLASSIFICACOES}}
    logging.basicConfig(
        filename=diretorio_saida / "execucao_dashboard.log",
        filemode="w",
        level=logging.INFO,
        encoding="utf-8",
        format="%(levelname)s:%(name)s:%(message)s",
        force=True,
    )
    logging.info(
        "Executado em %s | Relatório gerado | entrada=%s | totais=%s",
        _agora_manaus().strftime("%d/%m/%Y %H:%M:%S %z"),
        caminho_entrada.name,
        resumo_log,
    )
    logging.shutdown()
    _exportar_pdf(
        resumo_log,
        _calcular_evolucao_alertas(resultado),
        diretorio_saida / "resumo_conferencia_lotes.pdf",
    )
    return destino


def main() -> None:
    parser = argparse.ArgumentParser(description="Gera o relatório executivo de conferência de lotes.")
    parser.add_argument("--entrada", type=Path, default=ARQUIVO_ENTRADA_PADRAO)
    parser.add_argument("--saida", type=Path, default=DIRETORIO_SAIDA_PADRAO)
    args = parser.parse_args()
    print(gerar_relatorio(args.entrada, args.saida))


if __name__ == "__main__":
    main()
