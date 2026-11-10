"""
Excel Exporter using openpyxl
Creates professionally formatted .xlsx spreadsheets for tabular & structured web data.
"""

import os
from typing import Dict, Any, List
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter


HEADER_FILL = PatternFill(start_color="1E3A8A", end_color="1E3A8A", fill_type="solid")
HEADER_FONT = Font(name="Segoe UI", size=11, bold=True, color="FFFFFF")
ZEBRA_FILL = PatternFill(start_color="F8FAFC", end_color="F8FAFC", fill_type="solid")
WHITE_FILL = PatternFill(start_color="FFFFFF", end_color="FFFFFF", fill_type="solid")

SUB_HEADER_FILL = PatternFill(start_color="3B82F6", end_color="3B82F6", fill_type="solid")
SUB_HEADER_FONT = Font(name="Segoe UI", size=10, bold=True, color="FFFFFF")

REGULAR_FONT = Font(name="Segoe UI", size=10)
BOLD_FONT = Font(name="Segoe UI", size=10, bold=True)

THIN_BORDER = Border(
    left=Side(style="thin", color="E2E8F0"),
    right=Side(style="thin", color="E2E8F0"),
    top=Side(style="thin", color="E2E8F0"),
    bottom=Side(style="thin", color="E2E8F0")
)


def auto_fit_columns(ws, min_width=12, max_width=60):
    for col in ws.columns:
        max_len = 0
        col_letter = get_column_letter(col[0].column)
        for cell in col:
            val_str = str(cell.value or "")
            if "\n" in val_str:
                lines = val_str.split("\n")
                val_str = max(lines, key=len)
            max_len = max(max_len, len(val_str))
        ws.column_dimensions[col_letter].width = min(max(max_len + 3, min_width), max_width)


def create_excel_workbook(data: Dict[str, Any], output_path: str) -> str:
    wb = Workbook()
    # Remove default sheet
    wb.remove(wb.active)

    tables = data.get("tables", [])
    custom_matches = data.get("custom_matches", [])
    links = data.get("links", [])
    headings = data.get("headings", [])
    meta = data.get("metadata", {})
    stats = data.get("stats", {})

    # Sheet 1: Tabular / Structured Data
    if tables:
        ws_tables = wb.create_sheet(title="Extracted Tables")
        current_row = 1
        for t_idx, tbl in enumerate(tables, start=1):
            # Table Title Banner
            ws_tables.cell(row=current_row, column=1, value=f"Table #{t_idx} ({len(tbl)} rows)").font = BOLD_FONT
            current_row += 1

            for r_idx, row in enumerate(tbl):
                is_header = (r_idx == 0)
                for c_idx, cell_value in enumerate(row, start=1):
                    cell = ws_tables.cell(row=current_row, column=c_idx, value=cell_value)
                    cell.border = THIN_BORDER
                    if is_header:
                        cell.fill = HEADER_FILL
                        cell.font = HEADER_FONT
                        cell.alignment = Alignment(horizontal="center", vertical="center")
                    else:
                        cell.fill = ZEBRA_FILL if r_idx % 2 == 0 else WHITE_FILL
                        cell.font = REGULAR_FONT
                        cell.alignment = Alignment(horizontal="left", vertical="center")
                current_row += 1
            current_row += 2  # spacing between tables
        auto_fit_columns(ws_tables)

    # Sheet: Custom Matches (if present)
    if custom_matches:
        ws_custom = wb.create_sheet(title="Custom Extracted Records")
        headers = ["Record #", "Extracted Text", "Tag / Attributes", "Raw HTML Excerpt"]
        for c_idx, h in enumerate(headers, start=1):
            c = ws_custom.cell(row=1, column=c_idx, value=h)
            c.fill = HEADER_FILL
            c.font = HEADER_FONT
            c.alignment = Alignment(horizontal="center", vertical="center")

        for r_idx, m in enumerate(custom_matches, start=2):
            attrs = str(m.get("attributes", {})) if m.get("attributes") else "-"
            ws_custom.cell(row=r_idx, column=1, value=m.get("index", r_idx - 1)).alignment = Alignment(horizontal="center")
            ws_custom.cell(row=r_idx, column=2, value=m.get("text", "")).alignment = Alignment(horizontal="left", wrap_text=True)
            ws_custom.cell(row=r_idx, column=3, value=attrs).alignment = Alignment(horizontal="left")
            ws_custom.cell(row=r_idx, column=4, value=m.get("html", "")[:200]).alignment = Alignment(horizontal="left")

            fill = ZEBRA_FILL if r_idx % 2 == 0 else WHITE_FILL
            for c_idx in range(1, 5):
                cell = ws_custom.cell(row=r_idx, column=c_idx)
                cell.fill = fill
                cell.font = REGULAR_FONT
                cell.border = THIN_BORDER

        auto_fit_columns(ws_custom, min_width=12, max_width=70)

    # Sheet: Discovered Links
    if links:
        ws_links = wb.create_sheet(title="Discovered Links")
        headers = ["#", "Type", "Anchor Text", "Destination URL"]
        for c_idx, h in enumerate(headers, start=1):
            c = ws_links.cell(row=1, column=c_idx, value=h)
            c.fill = HEADER_FILL
            c.font = HEADER_FONT
            c.alignment = Alignment(horizontal="center", vertical="center")

        for r_idx, l in enumerate(links, start=2):
            l_type = "Internal" if l.get("is_internal") else "External"
            ws_links.cell(row=r_idx, column=1, value=r_idx - 1).alignment = Alignment(horizontal="center")
            ws_links.cell(row=r_idx, column=2, value=l_type).alignment = Alignment(horizontal="center")
            ws_links.cell(row=r_idx, column=3, value=l.get("text", "")).alignment = Alignment(horizontal="left")
            ws_links.cell(row=r_idx, column=4, value=l.get("url", "")).alignment = Alignment(horizontal="left")

            fill = ZEBRA_FILL if r_idx % 2 == 0 else WHITE_FILL
            for c_idx in range(1, 5):
                cell = ws_links.cell(row=r_idx, column=c_idx)
                cell.fill = fill
                cell.font = REGULAR_FONT
                cell.border = THIN_BORDER

        auto_fit_columns(ws_links, min_width=10, max_width=80)

    # Sheet: Page Overview & Metadata
    ws_meta = wb.create_sheet(title="Overview & Metadata")
    ws_meta.cell(row=1, column=1, value="Property").fill = HEADER_FILL
    ws_meta.cell(row=1, column=1).font = HEADER_FONT
    ws_meta.cell(row=1, column=2, value="Value").fill = HEADER_FILL
    ws_meta.cell(row=1, column=2).font = HEADER_FONT

    overview_rows = [
        ("Source URL", data.get("url", "")),
        ("Page Title", meta.get("title", "")),
        ("Meta Description", meta.get("description", "")),
        ("HTTP Status", str(data.get("status_code", ""))),
        ("Fetch Mode", data.get("mode_used", "")),
        ("Elapsed Seconds", str(data.get("elapsed_seconds", "")) + "s"),
        ("Word Count", f"{stats.get('words_count', 0):,}"),
        ("Headings Count", str(stats.get('headings_count', 0))),
        ("Links Count", str(stats.get('links_count', 0))),
        ("Images Count", str(stats.get('images_count', 0))),
        ("Tables Count", str(stats.get('tables_count', 0))),
        ("Canonical URL", meta.get("canonical", "")),
        ("Author", meta.get("author", "")),
        ("Keywords", meta.get("keywords", "")),
        ("OpenGraph Title", meta.get("og_title", "")),
        ("OpenGraph Image", meta.get("og_image", "")),
    ]

    for r_idx, (prop, val) in enumerate(overview_rows, start=2):
        c1 = ws_meta.cell(row=r_idx, column=1, value=prop)
        c2 = ws_meta.cell(row=r_idx, column=2, value=str(val or ""))
        c1.font = BOLD_FONT
        c2.font = REGULAR_FONT
        c1.border = THIN_BORDER
        c2.border = THIN_BORDER
        c1.fill = ZEBRA_FILL if r_idx % 2 == 0 else WHITE_FILL
        c2.fill = ZEBRA_FILL if r_idx % 2 == 0 else WHITE_FILL

    auto_fit_columns(ws_meta, min_width=18, max_width=90)

    # Sheet: Headings Hierarchy
    if headings:
        ws_headings = wb.create_sheet(title="Headings Outline")
        ws_headings.cell(row=1, column=1, value="Level").fill = HEADER_FILL
        ws_headings.cell(row=1, column=1).font = HEADER_FONT
        ws_headings.cell(row=1, column=2, value="Heading Text").fill = HEADER_FILL
        ws_headings.cell(row=1, column=2).font = HEADER_FONT

        for r_idx, h in enumerate(headings, start=2):
            c1 = ws_headings.cell(row=r_idx, column=1, value=h.get("tag", "").upper())
            c2 = ws_headings.cell(row=r_idx, column=2, value=h.get("text", ""))
            c1.font = BOLD_FONT
            c2.font = REGULAR_FONT
            c1.border = THIN_BORDER
            c2.border = THIN_BORDER
            c1.fill = ZEBRA_FILL if r_idx % 2 == 0 else WHITE_FILL
            c2.fill = ZEBRA_FILL if r_idx % 2 == 0 else WHITE_FILL

        auto_fit_columns(ws_headings, min_width=10, max_width=80)

    # Save to disk
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    wb.save(output_path)
    return output_path
