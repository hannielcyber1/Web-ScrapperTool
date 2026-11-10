"""
Interactive & Command-Line Scraper using Scrapling and Rich
Supports automatic content classification and PDF/Excel generation.
"""

import sys
import os
import json
import csv
import argparse
from typing import Optional

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich import box

from core.scraper import ScraplingEngine
from exporters.smart_exporter import export_adaptive
from exporters.classifier import ContentClassifier

console = Console()


def save_legacy_exports(data: dict, export_types: list[str], output_dir: str = "output"):
    os.makedirs(output_dir, exist_ok=True)
    slug = (
        data.get("url", "scraped_data")
        .replace("https://", "")
        .replace("http://", "")
        .replace("/", "_")
        .replace(":", "_")
        .strip("_")
    )
    saved_files = []

    if "json" in export_types:
        json_path = os.path.join(output_dir, f"{slug}.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        saved_files.append(json_path)

    if "md" in export_types or "markdown" in export_types:
        md_path = os.path.join(output_dir, f"{slug}.md")
        with open(md_path, "w", encoding="utf-8") as f:
            title = data.get("metadata", {}).get("title", "Scraped Content")
            f.write(f"# {title}\n\n")
            f.write(f"- **Source URL:** {data.get('url')}\n")
            f.write(f"- **Scraped At:** {data.get('elapsed_seconds')}s\n\n")
            f.write("---\n\n")
            f.write(data.get("markdown", ""))
        saved_files.append(md_path)

    if "csv" in export_types:
        if data.get("links"):
            links_csv = os.path.join(output_dir, f"{slug}_links.csv")
            with open(links_csv, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=["text", "url", "is_internal"])
                writer.writeheader()
                for item in data["links"]:
                    writer.writerow(item)
            saved_files.append(links_csv)

        if data.get("custom_matches"):
            custom_csv = os.path.join(output_dir, f"{slug}_custom.csv")
            with open(custom_csv, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["Index", "Text", "Attributes"])
                for m in data["custom_matches"]:
                    writer.writerow([m.get("index"), m.get("text"), json.dumps(m.get("attributes", {}))])
            saved_files.append(custom_csv)

    return saved_files


def display_results(data: dict, export_info: Optional[dict] = None):
    if not data.get("success"):
        console.print(Panel(f"[bold red]Scraping Failed:[/bold red] {data.get('error')}", title="Error", border_style="red"))
        return

    meta = data.get("metadata", {})
    stats = data.get("stats", {})

    # Overview Panel
    summary_text = (
        f"[bold cyan]URL:[/bold cyan] {data['url']}\n"
        f"[bold cyan]Title:[/bold cyan] {meta.get('title') or '[dim]None[/dim]'}\n"
        f"[bold cyan]Description:[/bold cyan] {meta.get('description') or '[dim]None[/dim]'}\n"
        f"[bold cyan]Status:[/bold cyan] [green]{data['status_code']}[/green] | "
        f"[bold cyan]Mode:[/bold cyan] {data['mode_used']} | "
        f"[bold cyan]Time:[/bold cyan] {data['elapsed_seconds']}s\n"
        f"[bold cyan]Content Stats:[/bold cyan] {stats.get('words_count', 0):,} words, "
        f"{stats.get('headings_count', 0)} headings, "
        f"{stats.get('links_count', 0)} links, "
        f"{stats.get('images_count', 0)} images, "
        f"{stats.get('tables_count', 0)} tables"
    )
    if data.get("warning"):
        summary_text += f"\n[bold yellow]Notice:[/bold yellow] {data['warning']}"

    console.print(Panel(summary_text, title="[bold green]Website Metadata & Stats[/bold green]", border_style="green"))

    # Content Classifier & Adaptive Export Panel
    if export_info:
        rec_format = export_info.get("recommended_format", "").upper()
        badge_color = "green" if rec_format == "EXCEL" else "blue" if rec_format == "PDF" else "magenta"
        adapt_text = (
            f"[bold {badge_color}]Detected Content Type:[/bold {badge_color}] {export_info.get('content_type', '').title()}\n"
            f"[bold {badge_color}]Recommended Format:[/bold {badge_color}] [{badge_color} reverse] {rec_format} [/{badge_color} reverse]\n"
            f"[bold cyan]Reason:[/bold cyan] {export_info.get('reason')}\n\n"
            f"[bold green]Auto-Generated Files:[/bold green]\n"
        )
        for f in export_info.get("files_generated", []):
            icon = "📗" if f.endswith(".xlsx") else "📕" if f.endswith(".pdf") else "📄"
            adapt_text += f"  {icon} [cyan]{f}[/cyan]\n"

        console.print(Panel(adapt_text.strip(), title="[bold yellow]⚡ Adaptive Intelligence — PDF / Excel Detection[/bold yellow]", border_style="yellow"))

    # Headings Table
    headings = data.get("headings", [])
    if headings:
        table = Table(title="Headings Structure (Preview)", box=box.ROUNDED)
        table.add_column("Level", style="magenta", width=8)
        table.add_column("Heading Text", style="white")
        for h in headings[:8]:
            table.add_row(h["tag"].upper(), h["text"])
        if len(headings) > 8:
            table.add_row("...", f"[dim]and {len(headings) - 8} more headings[/dim]")
        console.print(table)

    # Custom Matches Table
    custom_matches = data.get("custom_matches", [])
    if custom_matches:
        c_table = Table(title=f"Custom Query Matches ({len(custom_matches)} items)", box=box.ROUNDED)
        c_table.add_column("#", style="cyan", width=4)
        c_table.add_column("Extracted Text", style="green")
        for m in custom_matches[:8]:
            if "error" in m:
                c_table.add_row("!", f"[red]{m['error']}[/red]")
            else:
                c_table.add_row(str(m.get("index")), m.get("text", "")[:120])
        if len(custom_matches) > 8:
            c_table.add_row("...", f"[dim]and {len(custom_matches) - 8} more matches...[/dim]")
        console.print(c_table)

    # Tables Info
    tables = data.get("tables", [])
    if tables:
        t_table = Table(title=f"Extracted Data Tables ({len(tables)} tables)", box=box.ROUNDED)
        t_table.add_column("Table #", style="cyan", width=10)
        t_table.add_column("Rows", style="green", width=8)
        t_table.add_column("Columns", style="yellow", width=10)
        t_table.add_column("Header Sample", style="white")
        for idx, tbl in enumerate(tables, 1):
            rows_num = len(tbl)
            cols_num = len(tbl[0]) if rows_num > 0 else 0
            header_sample = ", ".join(tbl[0][:4]) if rows_num > 0 else "-"
            t_table.add_row(f"Table #{idx}", str(rows_num), str(cols_num), header_sample[:50])
        console.print(t_table)


def run_interactive():
    console.print(Panel.fit(
        "[bold magenta]⚡ Scrapling Intelligent Web Scraper[/bold magenta]\n"
        "[dim]Adaptive PDF & Excel Generation based on Content Type[/dim]",
        border_style="magenta"
    ))

    url = Prompt.ask("\n[bold cyan]Enter Website URL[/bold cyan]")
    if not url:
        console.print("[red]No URL provided. Exiting.[/red]")
        return

    mode_choice = Prompt.ask(
        "[bold cyan]Select Fetcher Mode[/bold cyan]",
        choices=["fast", "stealth"],
        default="fast"
    )

    custom_css = Prompt.ask("[bold cyan]Custom CSS selector (optional, e.g. .quote, .product)[/bold cyan]", default="")
    custom_xpath = Prompt.ask("[bold cyan]Custom XPath selector (optional)[/bold cyan]", default="")

    console.print(f"\n[bold yellow]Scraping {url} with Scrapling ({mode_choice} mode)...[/bold yellow]")
    with console.status("[bold green]Fetching, parsing, and classifying content...[/bold green]"):
        result = ScraplingEngine.scrape(
            url=url,
            mode=mode_choice,
            custom_css=custom_css if custom_css else None,
            custom_xpath=custom_xpath if custom_xpath else None
        )
        export_info = export_adaptive(result, preferred_format="auto") if result.get("success") else None

    display_results(result, export_info)

    if result.get("success"):
        console.print("\n[bold green]Export options:[/bold green]")
        export_choice = Prompt.ask(
            "[bold cyan]Would you also like to generate a specific format?[/bold cyan]",
            choices=["none", "excel", "pdf", "both", "json,md"],
            default="none"
        )
        if export_choice != "none":
            if export_choice in ("excel", "pdf", "both"):
                extra = export_adaptive(result, preferred_format=export_choice)
                console.print(f"[bold green]Saved files:[/bold green]")
                for p in extra.get("files_generated", []):
                    console.print(f"  • [cyan]{p}[/cyan]")
            elif "json" in export_choice or "md" in export_choice:
                fmts = [f.strip() for f in export_choice.split(",")]
                saved = save_legacy_exports(result, fmts)
                for p in saved:
                    console.print(f"  • [cyan]{p}[/cyan]")


def main():
    parser = argparse.ArgumentParser(description="Scrapling Web Scraping Tool with Adaptive PDF/Excel Generation")
    parser.add_argument("url", nargs="?", help="Website URL to scrape")
    parser.add_argument("--mode", choices=["fast", "stealth"], default="fast", help="Fetcher mode (default: fast)")
    parser.add_argument("--css", help="Custom CSS selector to extract")
    parser.add_argument("--xpath", help="Custom XPath to extract")
    parser.add_argument("--format", choices=["auto", "excel", "pdf", "both", "none"], default="auto",
                        help="Export format based on content type: auto (default), excel, pdf, both")
    parser.add_argument("--export", help="Comma-separated legacy formats (e.g., json,md,csv)")
    parser.add_argument("--outdir", default="output", help="Directory for exported files")
    args = parser.parse_args()

    if not args.url:
        run_interactive()
    else:
        console.print(f"[bold yellow]Scraping {args.url}...[/bold yellow]")
        result = ScraplingEngine.scrape(
            url=args.url,
            mode=args.mode,
            custom_css=args.css,
            custom_xpath=args.xpath
        )

        export_info = None
        if result.get("success") and args.format != "none":
            export_info = export_adaptive(result, output_dir=args.outdir, preferred_format=args.format)

        display_results(result, export_info)

        if args.export and result.get("success"):
            fmts = [f.strip().lower() for f in args.export.split(",") if f.strip()]
            saved = save_legacy_exports(result, fmts, output_dir=args.outdir)
            console.print("\n[bold green]Additional exported files:[/bold green]")
            for p in saved:
                console.print(f"  • [cyan]{p}[/cyan]")


if __name__ == "__main__":
    main()
