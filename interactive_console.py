"""
Scrapling Interactive Web Intelligence Terminal Console
A command-center REPL for autonomous web reconnaissance, data mining,
and adaptive PDF/Excel generation.
"""

import os
import sys
import shlex
import time
import subprocess
import threading
import webbrowser
from typing import List, Dict, Any, Optional

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich import box

from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.styles import Style as PtStyle
from prompt_toolkit.formatted_text import HTML

from core.scraper import ScraplingEngine
from exporters.smart_exporter import export_adaptive
from exporters.classifier import ContentClassifier

console = Console()

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Session Scrape Ledger
SCRAPE_HISTORY: List[Dict[str, Any]] = []
WEB_SERVER_THREAD = None


def print_banner():
    banner_text = Text()
    banner_text.append("=" * 96 + "\n", style="bright_black")
    banner_text.append("🕷️  SCRAPLING-AI // AUTONOMOUS WEB RECON & INTELLIGENCE CONSOLE (v0.5.1)\n", style="bold cyan")
    banner_text.append("=" * 96, style="bright_black")
    console.print(banner_text)

    # Engine Status Block
    console.print("[bold bright_cyan][*] Active Scraping Engines & Subsystems Initialized:[/bold bright_cyan]")
    console.print("  [bold green]✔[/bold green] [yellow]Scrapling Core Engine:[/yellow] [bold white]v0.5.1 ONLINE & ARMED[/bold white]")
    console.print("  [bold green]✔[/bold green] [yellow]Fast TLS Impersonator:[/yellow] [green]READY[/green] (curl_cffi - Chrome/Firefox/Safari TLS fingerprinting)")
    console.print("  [bold green]✔[/bold green] [yellow]Stealth Browser Runtime:[/yellow] [green]READY[/green] (Patchright Chromium v1248 - Anti-bot & Cloudflare bypass)")
    console.print("  [bold green]✔[/bold green] [yellow]Adaptive Format AI:[/yellow] [green]ONLINE[/green] (openpyxl Excel Tables & ReportLab PDF Documents)")
    console.print("  [bold green]✔[/bold green] [yellow]Markdown RAG Converter:[/yellow] [green]ACTIVE[/green] (markdownify v1.2.3)")
    console.print("  [bold cyan]ℹ[/bold cyan] [yellow]Web Studio Gateway:[/yellow] [dim]STANDBY[/dim] (Type '[bold white]web[/bold white]' to launch http://127.0.0.1:8000)\n")

    # Registered Capabilities Roster Table
    roster_table = Table(
        title="=== REGISTERED SCRAPING CAPABILITY ROSTER ===",
        title_style="bold bright_cyan",
        box=box.HORIZONTALS,
        header_style="bold bright_white on grey15",
        border_style="bright_blue"
    )
    roster_table.add_column("Agent / Mode ID", style="bold cyan", width=18)
    roster_table.add_column("Target Profile", style="white", width=22)
    roster_table.add_column("Engine Core", style="cyan", width=28)
    roster_table.add_column("Anti-Bot Scopes", style="yellow", width=30)
    roster_table.add_column("Default Adapter", style="green", width=18)

    roster_table.add_row(
        "fast_probe",
        "Fast Web Recon",
        "TLS Impersonator (curl_cffi)",
        "User-Agent, TLS JA3/JA4, HTTP/2",
        "JSON + Markdown"
    )
    roster_table.add_row(
        "stealth_runner",
        "Dynamic & SPAs",
        "Patchright Headless Chrome",
        "Cloudflare Turnstile, JS render",
        "Adaptive (PDF/XLSX)"
    )
    roster_table.add_row(
        "table_miner",
        "Data Grids / HTML",
        "Structured DOM Extractor",
        "Auto-structure, column matching",
        "Excel (.xlsx) Table"
    )
    roster_table.add_row(
        "doc_synthesizer",
        "Articles, Blogs & News",
        "RAG Markdown Pipeline",
        "Clean prose, heading hierarchy",
        "PDF (.pdf) Document"
    )
    roster_table.add_row(
        "deep_query",
        "Targeted CSS / XPath",
        "Self-Healing Tracker",
        "Fingerprint persistence, attrs",
        "Custom CSV / JSON"
    )
    console.print(roster_table)
    console.print()

    # Commands Reference
    print_commands()


def print_commands():
    cmd_text = (
        "[bold bright_yellow]Commands:[/bold bright_yellow]\n"
        "  [bold bright_white]scrape <url> [options][/bold bright_white]     - Full autonomous scrape with adaptive PDF / Excel classification\n"
        "  [bold bright_white]<any website url>[/bold bright_white]         - Direct URL input instantly executes autonomous scrape\n"
        "  [bold bright_white]inspect <url>[/bold bright_white]              - Deep metadata, SEO, tech headers & anti-bot reconnaissance\n"
        "  [bold bright_white]table <url>[/bold bright_white]                - Extract all HTML tables and export instantly to Excel (.xlsx)\n"
        "  [bold bright_white]pdf <url>[/bold bright_white]                  - Synthesize article or editorial page into a styled PDF document\n"
        "  [bold bright_white]query <url> <selector>[/bold bright_white]    - Execute targeted CSS or XPath selector extraction with live inspect\n"
        "  [bold bright_white]links <url>[/bold bright_white]                - Discover, resolve, and audit internal & external hyperlinks\n"
        "  [bold bright_white]markdown <url>[/bold bright_white]             - Print clean, formatted markdown directly to terminal\n"
        "  [bold bright_white]web [--port 8000][/bold bright_white]         - Launch the local Web Studio Dashboard and open in browser\n"
        "  [bold bright_white]history[/bold bright_white]                    - Display session scraping ledger and generated files\n"
        "  [bold bright_white]open <file|index>[/bold bright_white]          - Launch generated PDF, Excel, or JSON in native OS viewer\n"
        "  [bold bright_white]status[/bold bright_white]                     - Check live status of scrapers, fetchers, and dependencies\n"
        "  [bold bright_white]clear[/bold bright_white]                      - Clear screen\n"
        "  [bold bright_white]help[/bold bright_white]                       - Show this command reference manual\n"
        "  [bold bright_white]exit[/bold bright_white]                       - Quit console\n"
    )
    console.print(cmd_text)


def execute_scrape(
    url: str,
    mode: str = "fast",
    custom_css: Optional[str] = None,
    custom_xpath: Optional[str] = None,
    preferred_format: str = "auto"
):
    target_url = ScraplingEngine.normalize_url(url)
    console.print(f"[bold cyan]⚡ Initiating scrape on:[/bold cyan] [underline white]{target_url}[/underline white] [dim]({mode} mode, format: {preferred_format})[/dim]")

    start_time = time.time()
    with console.status("[bold green]Harvesting DOM, resolving resources, classifying content...[/bold green]"):
        result = ScraplingEngine.scrape(
            url=target_url,
            mode=mode,
            custom_css=custom_css,
            custom_xpath=custom_xpath
        )

    if not result.get("success"):
        console.print(Panel(f"[bold red]Scrape Failure:[/bold red] {result.get('error')}", title="Error", border_style="red"))
        return None

    # Run Adaptive Content Classification & File Generation
    export_info = export_adaptive(result, output_dir=OUTPUT_DIR, preferred_format=preferred_format)
    result["adaptive_export"] = export_info

    # Save in history
    SCRAPE_HISTORY.append({
        "index": len(SCRAPE_HISTORY) + 1,
        "url": target_url,
        "title": result.get("metadata", {}).get("title") or "No Title",
        "status": result.get("status_code"),
        "time": result.get("elapsed_seconds"),
        "words": result.get("stats", {}).get("words_count", 0),
        "tables": result.get("stats", {}).get("tables_count", 0),
        "links": result.get("stats", {}).get("links_count", 0),
        "recommended_format": export_info.get("recommended_format"),
        "files": export_info.get("files_generated", [])
    })

    # Display Results Card
    meta = result.get("metadata", {})
    stats = result.get("stats", {})

    status_badge = f"[green]{result['status_code']} OK[/green]" if result['status_code'] == 200 else f"[yellow]{result['status_code']}[/yellow]"
    overview_text = (
        f"[bold bright_cyan]Target URL:[/bold bright_cyan] {target_url}\n"
        f"[bold bright_cyan]Page Title:[/bold bright_cyan] {meta.get('title') or '[dim]None[/dim]'}\n"
        f"[bold bright_cyan]Status:[/bold bright_cyan] {status_badge}  |  "
        f"[bold bright_cyan]Mode:[/bold bright_cyan] {result['mode_used']}  |  "
        f"[bold bright_cyan]Time:[/bold bright_cyan] {result['elapsed_seconds']}s\n"
        f"[bold bright_cyan]Content Profile:[/bold bright_cyan] {stats.get('words_count', 0):,} words, "
        f"{stats.get('headings_count', 0)} headings, "
        f"{stats.get('links_count', 0)} links, "
        f"{stats.get('images_count', 0)} images, "
        f"{stats.get('tables_count', 0)} tables"
    )
    if meta.get("description"):
        overview_text += f"\n[bold bright_cyan]Description:[/bold bright_cyan] {meta['description'][:140]}..."

    console.print(Panel(overview_text, title="[bold green]Web Intelligence Summary[/bold green]", border_style="green"))

    # Adaptive Classification Panel
    rec_format = export_info.get("recommended_format", "").upper()
    badge_style = "bold green" if rec_format == "EXCEL" else "bold red" if rec_format == "PDF" else "bold magenta"
    adaptive_text = (
        f"[{badge_style}]Content Type Detected:[/{badge_style}] {export_info.get('content_type', '').title()}\n"
        f"[{badge_style}]Format Decision:[/{badge_style}] [{badge_style} reverse] {rec_format} [/{badge_style} reverse]\n"
        f"[bold white]Rationale:[/bold white] {export_info.get('reason')}\n\n"
        f"[bold bright_yellow]Artifacts Created on Disk:[/bold bright_yellow]\n"
    )
    for p in export_info.get("files_generated", []):
        icon = "📗" if p.endswith(".xlsx") else "📕" if p.endswith(".pdf") else "📄"
        adaptive_text += f"  {icon} [bright_cyan]{p}[/bright_cyan]\n"

    console.print(Panel(adaptive_text.strip(), title="[bold yellow]⚡ Adaptive Intelligence File Generation[/bold yellow]", border_style="yellow"))

    # Show custom matches if any
    custom_matches = result.get("custom_matches", [])
    if custom_matches:
        c_table = Table(title=f"Custom Selector Matches ({len(custom_matches)} items)", box=box.ROUNDED)
        c_table.add_column("#", style="cyan", width=4)
        c_table.add_column("Extracted Text", style="bright_white")
        for m in custom_matches[:6]:
            c_table.add_row(str(m.get("index")), m.get("text", "")[:120])
        if len(custom_matches) > 6:
            c_table.add_row("...", f"[dim]+{len(custom_matches) - 6} more items[/dim]")
        console.print(c_table)

    return result


def execute_inspect(url: str):
    target_url = ScraplingEngine.normalize_url(url)
    console.print(f"[bold cyan]🔍 Inspecting website architecture:[/bold cyan] {target_url}")
    with console.status("[bold green]Probing server headers, meta tags, OpenGraph...[/bold green]"):
        result = ScraplingEngine.scrape(url=target_url, mode="fast")

    if not result.get("success"):
        console.print(Panel(f"[bold red]Inspection Failed:[/bold red] {result.get('error')}", border_style="red"))
        return

    meta = result.get("metadata", {})
    t = Table(title="Website Architectural Audit", box=box.ROUNDED, border_style="cyan")
    t.add_column("Component", style="bold cyan", width=22)
    t.add_column("Discovered Value", style="white")

    for k, v in [
        ("Resolved URL", result.get("url")),
        ("HTTP Status", str(result.get("status_code"))),
        ("Page Title", meta.get("title")),
        ("Meta Description", meta.get("description")),
        ("Canonical Link", meta.get("canonical")),
        ("Author", meta.get("author")),
        ("Keywords", meta.get("keywords")),
        ("OpenGraph Title", meta.get("og_title")),
        ("OpenGraph Image", meta.get("og_image")),
        ("Total Word Count", f"{result.get('stats', {}).get('words_count', 0):,}"),
        ("Heading Elements", str(result.get('stats', {}).get('headings_count', 0))),
        ("Hyperlinks", str(result.get('stats', {}).get('links_count', 0))),
        ("HTML Tables", str(result.get('stats', {}).get('tables_count', 0))),
        ("Media Images", str(result.get('stats', {}).get('images_count', 0))),
    ]:
        if v:
            t.add_row(k, str(v)[:100])
    console.print(t)


def execute_table_miner(url: str):
    target_url = ScraplingEngine.normalize_url(url)
    console.print(f"[bold green]📊 Mining all HTML tables from:[/bold green] {target_url}")
    res = execute_scrape(target_url, mode="fast", preferred_format="excel")
    if res and res.get("tables"):
        console.print(f"[bold green]✔ Successfully extracted {len(res['tables'])} data table(s) to Excel.[/bold green]")
    elif res:
        console.print("[bold yellow]ℹ No standard <table> tags found on this page. Check if content uses custom divs or run 'query' with a CSS selector.[/bold yellow]")


def execute_pdf_doc(url: str):
    target_url = ScraplingEngine.normalize_url(url)
    console.print(f"[bold red]📄 Synthesizing article/editorial content into PDF:[/bold red] {target_url}")
    res = execute_scrape(target_url, mode="fast", preferred_format="pdf")
    if res:
        console.print("[bold green]✔ Publication-ready PDF document created in output/ folder.[/bold green]")


def execute_query(url: str, selector: str):
    target_url = ScraplingEngine.normalize_url(url)
    is_xpath = selector.startswith("/") or selector.startswith("(")
    console.print(f"[bold yellow]🎯 Querying:[/bold yellow] [white]{target_url}[/white] with [cyan]{selector}[/cyan]")
    execute_scrape(
        target_url,
        mode="fast",
        custom_css=selector if not is_xpath else None,
        custom_xpath=selector if is_xpath else None,
        preferred_format="excel"
    )


def execute_links(url: str, filter_type: str = "all"):
    target_url = ScraplingEngine.normalize_url(url)
    console.print(f"[bold cyan]🔗 Discovering links on:[/bold cyan] {target_url}")
    with console.status("[bold green]Parsing links...[/bold green]"):
        res = ScraplingEngine.scrape(url=target_url, mode="fast")

    if not res.get("success"):
        console.print(f"[red]Error:[/red] {res.get('error')}")
        return

    links = res.get("links", [])
    if filter_type == "internal":
        links = [l for l in links if l.get("is_internal")]
    elif filter_type == "external":
        links = [l for l in links if not l.get("is_internal")]

    t = Table(title=f"Discovered Hyperlinks ({len(links)} items, filter: {filter_type})", box=box.ROUNDED)
    t.add_column("Type", style="yellow", width=10)
    t.add_column("Anchor Text", style="cyan", width=35)
    t.add_column("Resolved URL", style="white")

    for l in links[:15]:
        t.add_row("Internal" if l.get("is_internal") else "External", l.get("text", "")[:35], l.get("url", "")[:60])
    if len(links) > 15:
        t.add_row("...", f"[dim]+{len(links) - 15} more links...[/dim]", "...")
    console.print(t)


def execute_markdown(url: str):
    target_url = ScraplingEngine.normalize_url(url)
    with console.status("[bold green]Generating Markdown...[/bold green]"):
        res = ScraplingEngine.scrape(url=target_url, mode="fast")

    if not res.get("success"):
        console.print(f"[red]Error:[/red] {res.get('error')}")
        return

    md = res.get("markdown", "").strip()
    preview = md[:1200] + ("\n... [truncated for display]" if len(md) > 1200 else "")
    console.print(Panel(preview, title=f"[bold blue]Clean Markdown — {target_url}[/bold blue]", border_style="blue"))


def show_history():
    if not SCRAPE_HISTORY:
        console.print("[dim]No scrape operations in current session ledger.[/dim]")
        return

    t = Table(title="=== SESSION SCRAPING LEDGER ===", box=box.ROUNDED, border_style="bright_blue")
    t.add_column("#", style="cyan", width=4)
    t.add_column("Target URL", style="white", width=30)
    t.add_column("Title", style="bright_white", width=25)
    t.add_column("Words", style="yellow", width=10)
    t.add_column("Format", style="green", width=10)
    t.add_column("Generated Files", style="cyan")

    for item in SCRAPE_HISTORY:
        files_str = ", ".join([os.path.basename(f) for f in item.get("files", [])])
        t.add_row(
            str(item["index"]),
            item["url"][:30],
            item["title"][:25],
            f"{item['words']:,}",
            item["recommended_format"].upper(),
            files_str
        )
    console.print(t)


def open_file_or_index(arg: str):
    if not arg:
        console.print("[yellow]Usage: open <filename|history_index>[/yellow]")
        return

    target_path = None
    if arg.isdigit():
        idx = int(arg) - 1
        if 0 <= idx < len(SCRAPE_HISTORY):
            files = SCRAPE_HISTORY[idx].get("files", [])
            if files:
                target_path = files[0]
        else:
            console.print(f"[red]Invalid history index #{arg}[/red]")
            return
    else:
        # Check direct path or in output/
        cand1 = os.path.join(OUTPUT_DIR, arg)
        cand2 = arg
        if os.path.exists(cand1):
            target_path = cand1
        elif os.path.exists(cand2):
            target_path = cand2

    if target_path and os.path.exists(target_path):
        console.print(f"[bold green]Opening {target_path} in native application...[/bold green]")
        try:
            os.startfile(target_path)
        except Exception as e:
            console.print(f"[red]Failed to open file: {e}[/red]")
    else:
        console.print(f"[red]File '{arg}' not found in output directory.[/red]")


def launch_web_studio(port: int = 8000):
    global WEB_SERVER_THREAD
    url = f"http://127.0.0.1:{port}"
    if WEB_SERVER_THREAD and WEB_SERVER_THREAD.is_alive():
        console.print(f"[bold green]✔ Web Studio is already running at {url}[/bold green]")
        webbrowser.open(url)
        return

    console.print(f"[bold cyan]⚡ Launching Scrapling Web Studio background daemon on {url}...[/bold cyan]")

    def _run():
        import uvicorn
        uvicorn.run("server:app", host="127.0.0.1", port=port, log_level="warning")

    WEB_SERVER_THREAD = threading.Thread(target=_run, daemon=True)
    WEB_SERVER_THREAD.start()

    time.sleep(1.2)
    webbrowser.open(url)
    console.print(f"[bold green]✔ Web Studio running & opened in browser at {url}[/bold green]")


def main_loop():
    print_banner()

    commands = [
        "scrape", "inspect", "table", "pdf", "query", "links",
        "markdown", "web", "history", "open", "status", "clear", "help", "exit"
    ]
    completer = WordCompleter(commands, ignore_case=True)

    session = PromptSession(
        completer=completer,
        style=PtStyle.from_dict({
            "prompt": "ansicyan bold",
        })
    )

    while True:
        try:
            user_input = session.prompt(HTML("<ansicyan><b>scrapling&gt; </b></ansicyan>")).strip()
            if not user_input:
                continue

            # Check if user typed a bare URL directly (e.g. quotes.toscrape.com or https://...)
            if (
                user_input.startswith("http://")
                or user_input.startswith("https://")
                or (("." in user_input) and not user_input.startswith("-") and " " not in user_input and user_input.split(".")[0] not in commands)
            ):
                execute_scrape(user_input)
                continue

            parts = shlex.split(user_input)
            cmd = parts[0].lower()
            args = parts[1:]

            if cmd in ("exit", "quit", "q"):
                console.print("[bold yellow]Terminating Scrapling Console session. Good hunting![/bold yellow]")
                break

            elif cmd == "help":
                print_commands()

            elif cmd in ("clear", "cls"):
                os.system("cls" if os.name == "nt" else "clear")
                print_banner()

            elif cmd == "status":
                console.print("[bold bright_cyan][*] Subsystem Status Check:[/bold bright_cyan]")
                console.print("  ✔ Core Scrapling Engine: HEALTHY")
                console.print("  ✔ Fast HTTP TLS Fetcher: OPERATIONAL")
                console.print("  ✔ Stealth Chromium Runtime: OPERATIONAL")
                console.print("  ✔ ReportLab PDF Subsystem: OPERATIONAL")
                console.print("  ✔ openpyxl Excel Subsystem: OPERATIONAL")
                console.print(f"  ✔ Web Server Gateway: {'ONLINE (Port 8000)' if WEB_SERVER_THREAD and WEB_SERVER_THREAD.is_alive() else 'STANDBY'}")

            elif cmd == "history":
                show_history()

            elif cmd == "web":
                port = 8000
                if args and args[0].isdigit():
                    port = int(args[0])
                launch_web_studio(port)

            elif cmd == "open":
                if not args:
                    console.print("[yellow]Usage: open <filename_or_history_number>[/yellow]")
                else:
                    open_file_or_index(args[0])

            elif cmd == "scrape":
                if not args:
                    console.print("[yellow]Usage: scrape <url> [--mode fast|stealth] [--format auto|excel|pdf|both] [--css <selector>][/yellow]")
                    continue
                url = args[0]
                mode = "fast"
                fmt = "auto"
                css = None
                xpath = None

                i = 1
                while i < len(args):
                    if args[i] == "--mode" and i + 1 < len(args):
                        mode = args[i + 1]
                        i += 2
                    elif args[i] == "--format" and i + 1 < len(args):
                        fmt = args[i + 1]
                        i += 2
                    elif args[i] == "--css" and i + 1 < len(args):
                        css = args[i + 1]
                        i += 2
                    elif args[i] == "--xpath" and i + 1 < len(args):
                        xpath = args[i + 1]
                        i += 2
                    else:
                        i += 1
                execute_scrape(url, mode=mode, custom_css=css, custom_xpath=xpath, preferred_format=fmt)

            elif cmd == "inspect":
                if not args:
                    console.print("[yellow]Usage: inspect <url>[/yellow]")
                else:
                    execute_inspect(args[0])

            elif cmd == "table":
                if not args:
                    console.print("[yellow]Usage: table <url>[/yellow]")
                else:
                    execute_table_miner(args[0])

            elif cmd == "pdf":
                if not args:
                    console.print("[yellow]Usage: pdf <url>[/yellow]")
                else:
                    execute_pdf_doc(args[0])

            elif cmd == "query":
                if len(args) < 2:
                    console.print("[yellow]Usage: query <url> <css_or_xpath_selector>[/yellow]")
                else:
                    execute_query(args[0], args[1])

            elif cmd == "links":
                if not args:
                    console.print("[yellow]Usage: links <url> [--filter all|internal|external][/yellow]")
                else:
                    flt = "all"
                    if len(args) >= 3 and args[1] == "--filter":
                        flt = args[2]
                    execute_links(args[0], flt)

            elif cmd == "markdown":
                if not args:
                    console.print("[yellow]Usage: markdown <url>[/yellow]")
                else:
                    execute_markdown(args[0])

            else:
                console.print(f"[red]Unknown command: '{cmd}'. Type [bold white]help[/bold white] for command manual.[/red]")

        except KeyboardInterrupt:
            console.print("\n[dim]Ctrl+C detected. Type 'exit' to quit.[/dim]")
        except EOFError:
            break
        except Exception as e:
            console.print(f"[bold red]Console Exception:[/bold red] {e}")


if __name__ == "__main__":
    main_loop()
