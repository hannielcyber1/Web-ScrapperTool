"""
Content Type Classifier for Scraped Websites
Determines whether scraped information is primarily Tabular/Structured Data (Excel)
or Document/Editorial Prose (PDF).
"""

from typing import Dict, Any, Tuple


class ContentClassifier:
    """Classifies scraped site data into 'tabular', 'document', or 'mixed'."""

    @classmethod
    def classify(cls, data: Dict[str, Any]) -> Tuple[str, str, str]:
        """
        Returns (content_type, recommended_format, reason)
        content_type: 'tabular' | 'document' | 'mixed'
        recommended_format: 'excel' | 'pdf' | 'both'
        """
        stats = data.get("stats", {})
        tables = data.get("tables", [])
        custom_matches = data.get("custom_matches", [])
        words_count = stats.get("words_count", 0)
        headings_count = stats.get("headings_count", 0)
        links_count = stats.get("links_count", 0)

        # Count total rows across all detected HTML tables
        total_table_rows = sum(len(tbl) for tbl in tables) if tables else 0
        custom_matches_count = len(custom_matches)

        # Calculate scores
        # Tabular signals:
        # - HTML tables with rows
        # - Extracted repetitive items from custom CSS/XPath
        # - High link-to-word ratio (e.g. directory, listings)
        tabular_score = 0
        if total_table_rows > 0:
            tabular_score += total_table_rows * 4
        if custom_matches_count > 0:
            tabular_score += custom_matches_count * 3
        if links_count > 25 and words_count < 600:
            tabular_score += 30

        # Document / Article signals:
        # - Significant word count (reading material, blog, article, documentation)
        # - Multiple headings (h1, h2, h3 structure)
        # - Low table count relative to text
        document_score = 0
        if words_count > 300:
            document_score += (words_count // 50) * 2
        if headings_count >= 3:
            document_score += headings_count * 3

        # Decision logic
        if tabular_score > 0 and total_table_rows >= 3 and words_count < 1500:
            return (
                "tabular",
                "excel",
                f"Detected {len(tables)} data table(s) with {total_table_rows} structured rows. An Excel workbook (.xlsx) provides the best tabular analysis."
            )
        elif custom_matches_count >= 5 and words_count < 1000:
            return (
                "tabular",
                "excel",
                f"Detected {custom_matches_count} structured extracted records matching your selector. Formatted as an Excel table (.xlsx)."
            )
        elif document_score >= 25 and total_table_rows == 0:
            return (
                "document",
                "pdf",
                f"Detected editorial/article document with {words_count:,} words and {headings_count} headings. A formatted PDF document (.pdf) is best suited for reading and distribution."
            )
        elif total_table_rows > 0 and words_count > 800:
            return (
                "mixed",
                "both",
                f"Detected both substantial article text ({words_count:,} words) and structured data ({total_table_rows} table rows). Both PDF and Excel are recommended."
            )
        elif total_table_rows > 0 or custom_matches_count > 0:
            return (
                "tabular",
                "excel",
                "Structured data encountered. Formatted into an Excel workbook (.xlsx)."
            )
        else:
            return (
                "document",
                "pdf",
                f"Webpage content ({words_count:,} words). Formatted into a clean PDF document (.pdf)."
            )
