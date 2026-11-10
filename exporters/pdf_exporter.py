"""
PDF Exporter using ReportLab
Generates clean, beautifully styled PDF reports for article/document web content.
"""

import os
import re
from typing import Dict, Any, List

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable,
    KeepTogether,
)
from reportlab.pdfgen import canvas


class NumberedCanvas(canvas.Canvas):
    """Canvas that adds 'Page X of Y' footer and running header."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748B"))

        # Footer
        footer_text = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(612 - 40, 25, footer_text)
        self.drawString(40, 25, "Scrapling Web Scraping Studio — ReportLab Document")

        # Top line for page > 1
        if self._pageNumber > 1:
            self.setStrokeColor(colors.HexColor("#E2E8F0"))
            self.setLineWidth(0.5)
            self.line(40, 792 - 35, 612 - 40, 792 - 35)

        self.restoreState()


def clean_xml_text(text: str) -> str:
    """Escape XML characters for ReportLab Paragraphs."""
    if not text:
        return ""
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    # Convert markdown bold and italic back safely
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"\*(.+?)\*", r"<i>\1</i>", text)
    return text


def create_pdf_document(data: Dict[str, Any], output_path: str) -> str:
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        leftMargin=40,
        rightMargin=40,
        topMargin=45,
        bottomMargin=45
    )

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#0F172A"),
        spaceAfter=6
    )

    url_style = ParagraphStyle(
        "DocURL",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#2563EB"),
        spaceAfter=12
    )

    h1_style = ParagraphStyle(
        "DocH1",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=13,
        leading=17,
        textColor=colors.HexColor("#1E3A8A"),
        spaceBefore=14,
        spaceAfter=6,
        keepWithNext=True
    )

    h2_style = ParagraphStyle(
        "DocH2",
        parent=styles["Heading3"],
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=15,
        textColor=colors.HexColor("#1E293B"),
        spaceBefore=10,
        spaceAfter=4,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        "DocBody",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9.5,
        leading=14,
        textColor=colors.HexColor("#334155"),
        spaceAfter=6
    )

    meta_label_style = ParagraphStyle(
        "MetaLabel",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor("#475569")
    )

    meta_val_style = ParagraphStyle(
        "MetaVal",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor("#0F172A")
    )

    story = []

    meta = data.get("metadata", {})
    stats = data.get("stats", {})
    title = meta.get("title") or "Scraped Web Document"

    # Title & Target URL
    story.append(Paragraph(clean_xml_text(title), title_style))
    story.append(Paragraph(f"Source URL: {clean_xml_text(data.get('url', ''))}", url_style))

    # Metadata Summary Card Table
    meta_table_data = [
        [
            Paragraph("Status", meta_label_style),
            Paragraph(str(data.get("status_code", 200)), meta_val_style),
            Paragraph("Word Count", meta_label_style),
            Paragraph(f"{stats.get('words_count', 0):,}", meta_val_style),
            Paragraph("Mode", meta_label_style),
            Paragraph(data.get("mode_used", "fast"), meta_val_style),
        ],
        [
            Paragraph("Elapsed Time", meta_label_style),
            Paragraph(f"{data.get('elapsed_seconds', 0)}s", meta_val_style),
            Paragraph("Links Found", meta_label_style),
            Paragraph(str(stats.get("links_count", 0)), meta_val_style),
            Paragraph("Headings", meta_label_style),
            Paragraph(str(stats.get("headings_count", 0)), meta_val_style),
        ]
    ]

    desc = meta.get("description")
    if desc:
        meta_table_data.append([
            Paragraph("Description", meta_label_style),
            Paragraph(clean_xml_text(desc[:300]), meta_val_style),
            "", "", "", ""
        ])

    meta_table = Table(meta_table_data, colWidths=[70, 100, 75, 95, 60, 132])
    meta_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#F1F5F9")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("SPAN", (1, 2), (-1, 2)) if desc else ("VALIGN", (0, 0), (0, 0), "TOP")
    ]))

    story.append(meta_table)
    story.append(Spacer(1, 14))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#E2E8F0"), spaceAfter=14))

    # Extracted Markdown / Article Content
    raw_markdown = data.get("markdown", "").strip()
    if raw_markdown:
        story.append(Paragraph("Document Content", h1_style))

        lines = raw_markdown.split("\n")
        in_code_block = False
        code_lines = []

        for line in lines:
            trimmed = line.strip()
            if not trimmed:
                story.append(Spacer(1, 4))
                continue

            if trimmed.startswith("```"):
                if in_code_block:
                    # Flush code
                    code_text = "<br/>".join([clean_xml_text(c) for c in code_lines])
                    story.append(Paragraph(code_text, ParagraphStyle("Code", parent=body_style, fontName="Courier", fontSize=8, leading=10, textColor=colors.HexColor("#1E293B"))))
                    code_lines = []
                    in_code_block = False
                else:
                    in_code_block = True
                continue

            if in_code_block:
                code_lines.append(trimmed)
                continue

            # Heading checks
            if trimmed.startswith("# "):
                story.append(Paragraph(clean_xml_text(trimmed[2:]), h1_style))
            elif trimmed.startswith("## "):
                story.append(Paragraph(clean_xml_text(trimmed[3:]), h2_style))
            elif trimmed.startswith("### "):
                story.append(Paragraph(clean_xml_text(trimmed[4:]), h2_style))
            elif trimmed.startswith("- ") or trimmed.startswith("* "):
                bullet_text = f"• {clean_xml_text(trimmed[2:])}"
                story.append(Paragraph(bullet_text, ParagraphStyle("Bullet", parent=body_style, leftIndent=12)))
            else:
                story.append(Paragraph(clean_xml_text(trimmed), body_style))

    # Tables if present
    tables = data.get("tables", [])
    if tables:
        story.append(Spacer(1, 12))
        story.append(Paragraph("Extracted Tables", h1_style))
        for t_idx, tbl in enumerate(tables[:3], start=1):  # include up to first 3 tables in PDF
            story.append(Paragraph(f"Table #{t_idx}", h2_style))
            tbl_flowable_data = []
            for r_idx, row in enumerate(tbl[:25]):  # up to 25 rows in PDF table
                row_cells = [Paragraph(clean_xml_text(str(c)[:100]), meta_val_style if r_idx > 0 else meta_label_style) for c in row[:6]]
                tbl_flowable_data.append(row_cells)

            if tbl_flowable_data:
                col_width = (612 - 80) / len(tbl_flowable_data[0])
                r_table = Table(tbl_flowable_data, colWidths=[col_width] * len(tbl_flowable_data[0]))
                r_table.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1E3A8A")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
                    ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ]))
                story.append(r_table)
                story.append(Spacer(1, 10))

    # Build the document
    doc.build(story, canvasmaker=NumberedCanvas)
    return output_path
