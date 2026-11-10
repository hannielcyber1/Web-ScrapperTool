"""
Smart Adaptive Exporter
Automatically determines and generates Excel tables or PDF documents
based on the structure and nature of scraped website information.
"""

import os
from typing import Dict, Any, List, Optional
from urllib.parse import urlparse

from .classifier import ContentClassifier
from .excel_exporter import create_excel_workbook
from .pdf_exporter import create_pdf_document


def get_file_slug(url: str) -> str:
    parsed = urlparse(url)
    slug = (parsed.netloc + parsed.path).replace("/", "_").replace(":", "_").strip("_")
    return slug or "scraped_data"


def export_adaptive(
    data: Dict[str, Any],
    output_dir: str = "output",
    preferred_format: str = "auto"
) -> Dict[str, Any]:
    """
    Classify scraped content and generate Excel and/or PDF files.
    :param data: The ScraplingEngine scrape result dictionary.
    :param output_dir: Directory where exported files will be placed.
    :param preferred_format: 'auto' | 'excel' | 'pdf' | 'both'
    """
    os.makedirs(output_dir, exist_ok=True)
    slug = get_file_slug(data.get("url", "website"))

    content_type, recommended_format, reason = ContentClassifier.classify(data)

    target_formats: List[str] = []
    if preferred_format == "auto":
        if recommended_format == "both":
            target_formats = ["excel", "pdf"]
        else:
            target_formats = [recommended_format]
    elif preferred_format in ("excel", "xlsx"):
        target_formats = ["excel"]
    elif preferred_format == "pdf":
        target_formats = ["pdf"]
    elif preferred_format in ("both", "all"):
        target_formats = ["excel", "pdf"]

    files_generated = []
    excel_path = None
    pdf_path = None

    if "excel" in target_formats:
        out_excel = os.path.join(output_dir, f"{slug}.xlsx")
        try:
            create_excel_workbook(data, out_excel)
            files_generated.append(out_excel)
            excel_path = out_excel
        except Exception as e:
            files_generated.append(f"Excel Error: {str(e)}")

    if "pdf" in target_formats:
        out_pdf = os.path.join(output_dir, f"{slug}.pdf")
        try:
            create_pdf_document(data, out_pdf)
            files_generated.append(out_pdf)
            pdf_path = out_pdf
        except Exception as e:
            files_generated.append(f"PDF Error: {str(e)}")

    return {
        "content_type": content_type,
        "recommended_format": recommended_format,
        "reason": reason,
        "formats_built": target_formats,
        "files_generated": files_generated,
        "excel_path": excel_path,
        "pdf_path": pdf_path,
    }
