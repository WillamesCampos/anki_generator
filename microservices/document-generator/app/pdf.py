"""
Geração de PDF genérico (Sprint 11). O contrato é um conjunto FECHADO de seções
tipadas — nada de HTML, CSS ou layout livre: um serviço com a porta exposta
recebe dados, não marcação, e o schema valida tudo antes de renderizar. A
renderização é do `reportlab` (Python puro, sem libs de sistema extras); o
`bar_chart` é desenhado por ele mesmo, vetorial, então o cliente manda só os
números — nenhuma imagem precisa ser renderizada antes (os gráficos do projeto
são Chart.js, no navegador, e o relatório semanal roda no servidor).

Fora do contrato por ora (entram quando a Sprint 15 provar que precisam):
`image` e `line_chart`.
"""

import io
from typing import Annotated, Literal, Union
from xml.sax.saxutils import escape

from pydantic import BaseModel, Field, model_validator
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.charts.legends import Legend
from reportlab.graphics.shapes import Drawing
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    ListFlowable,
    ListItem,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

MAX_SECTIONS = 500
MAX_TABLE_ROWS = 2000

SERIES_COLORS = [
    colors.HexColor("#F5821F"),
    colors.HexColor("#1F2937"),
    colors.HexColor("#2E7D32"),
    colors.HexColor("#1565C0"),
    colors.HexColor("#8E24AA"),
    colors.HexColor("#C62828"),
]


class Heading(BaseModel):
    type: Literal["heading"]
    text: str = Field(min_length=1, max_length=300)
    level: int = Field(default=1, ge=1, le=3)


class Paragraph_(BaseModel):
    type: Literal["paragraph"]
    text: str = Field(min_length=1, max_length=10_000)


class BulletList(BaseModel):
    type: Literal["bullet_list"]
    items: list[Annotated[str, Field(min_length=1, max_length=1000)]] = Field(
        min_length=1, max_length=100
    )


class Table_(BaseModel):
    type: Literal["table"]
    columns: list[Annotated[str, Field(max_length=200)]] = Field(min_length=1, max_length=10)
    rows: list[list[Annotated[str, Field(max_length=1000)]]] = Field(max_length=MAX_TABLE_ROWS)

    @model_validator(mode="after")
    def _rows_match_columns(self):
        for index, row in enumerate(self.rows):
            if len(row) != len(self.columns):
                raise ValueError(
                    f"row {index} has {len(row)} cells but there are {len(self.columns)} columns"
                )
        return self


class Series(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    values: list[float] = Field(min_length=1, max_length=50)


class BarChart(BaseModel):
    type: Literal["bar_chart"]
    title: str | None = Field(default=None, max_length=200)
    categories: list[Annotated[str, Field(min_length=1, max_length=100)]] = Field(
        min_length=1, max_length=50
    )
    series: list[Series] = Field(min_length=1, max_length=len(SERIES_COLORS))

    @model_validator(mode="after")
    def _values_match_categories(self):
        for serie in self.series:
            if len(serie.values) != len(self.categories):
                raise ValueError(
                    f"series '{serie.name}' has {len(serie.values)} values "
                    f"for {len(self.categories)} categories"
                )
        return self


Section = Annotated[
    Union[Heading, Paragraph_, BulletList, Table_, BarChart], Field(discriminator="type")
]


class PdfDocument(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    subtitle: str | None = Field(default=None, max_length=200)
    sections: list[Section] = Field(max_length=MAX_SECTIONS)


def _text(value: str) -> str:
    """Texto do usuário vira texto literal: o `Paragraph` do reportlab
    interpreta marcação (`<b>`, `&amp;`), então tudo é escapado."""
    return escape(value)


def _chart(section: BarChart, width: float) -> Drawing:
    height = 200
    drawing = Drawing(width, height)
    chart = VerticalBarChart()
    chart.x, chart.y = 40, 40
    chart.width, chart.height = width - 60, height - 70
    chart.data = [serie.values for serie in section.series]
    chart.categoryAxis.categoryNames = section.categories
    for axis in (chart.categoryAxis, chart.valueAxis):
        axis.labels.fontName = "Helvetica"  # mesma família do texto do documento
        axis.labels.fontSize = 8
    chart.valueAxis.valueMin = min(0, min(min(s.values) for s in section.series))
    chart.bars.strokeColor = None
    for index in range(len(section.series)):
        chart.bars[index].fillColor = SERIES_COLORS[index]
    drawing.add(chart)

    if len(section.series) > 1:
        legend = Legend()
        legend.x, legend.y = 40, height - 5
        legend.alignment = "right"
        legend.fontName = "Helvetica"
        legend.fontSize = 8
        legend.columnMaximum = 1
        legend.deltax = 70
        legend.colorNamePairs = [
            (SERIES_COLORS[index], serie.name) for index, serie in enumerate(section.series)
        ]
        drawing.add(legend)
    return drawing


def render_pdf(document: PdfDocument) -> bytes:
    """Renderiza o documento em memória (nada é gravado em disco)."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        title=document.title,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )
    styles = getSampleStyleSheet()
    subtitle_style = ParagraphStyle("Subtitle", parent=styles["Normal"], textColor=colors.grey)
    heading_styles = {1: styles["Heading1"], 2: styles["Heading2"], 3: styles["Heading3"]}
    cell_style = ParagraphStyle("Cell", parent=styles["Normal"], fontSize=9)
    header_style = ParagraphStyle("CellHeader", parent=cell_style, fontName="Helvetica-Bold")

    story = [Paragraph(_text(document.title), styles["Title"])]
    if document.subtitle:
        story.append(Paragraph(_text(document.subtitle), subtitle_style))
    story.append(Spacer(1, 0.5 * cm))

    for section in document.sections:
        if isinstance(section, Heading):
            story.append(Paragraph(_text(section.text), heading_styles[section.level]))
        elif isinstance(section, Paragraph_):
            story.append(Paragraph(_text(section.text), styles["BodyText"]))
        elif isinstance(section, BulletList):
            story.append(
                ListFlowable(
                    [ListItem(Paragraph(_text(item), styles["BodyText"])) for item in section.items],
                    bulletType="bullet",
                )
            )
        elif isinstance(section, Table_):
            data = [[Paragraph(_text(c), header_style) for c in section.columns]] + [
                [Paragraph(_text(cell), cell_style) for cell in row] for row in section.rows
            ]
            table = Table(data, repeatRows=1, colWidths=[doc.width / len(section.columns)] * len(section.columns))
            table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#FCE3C8")),
                        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#999999")),
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ]
                )
            )
            story.append(table)
        elif isinstance(section, BarChart):
            if section.title:
                story.append(Paragraph(_text(section.title), heading_styles[3]))
            story.append(_chart(section, doc.width))
        story.append(Spacer(1, 0.3 * cm))

    doc.build(story)
    return buffer.getvalue()
