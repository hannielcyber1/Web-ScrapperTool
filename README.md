# 🕷️ Scrapling-AI // Web Scraping & Intelligence Studio
### Autonomous Web Reconnaissance • Adaptive PDF & Excel Generation • Cyberpunk Interactive Console

An advanced web scraping and data intelligence tool built on top of **[D4Vinci/Scrapling](https://github.com/d4vinci/Scrapling)**.

Equipped with an **Interactive Command-Center Terminal Console**, automatic **Adaptive PDF & Excel Generation**, and a **Web Dashboard**.

---

## 🖥️ Interactive Terminal Console

Launch the terminal console:
```bash
python interactive_console.py
# or
python main.py
```

### Visual Layout
The terminal console is modeled after security and AI agent mission-control interfaces:
- **Status & Subsystems Inspection:** Real-time health checks on TLS impersonation, Patchright Chromium browser, PDF engine, and Excel engine.
- **Capability Roster Table:** Overview of all active modes (`fast_probe`, `stealth_runner`, `table_miner`, `doc_synthesizer`, `deep_query`).
- **Command Palette & REPL:** An interactive shell with autocomplete, history, and auto-detection.

```text
================================================================================================
🕷️  SCRAPLING-AI // AUTONOMOUS WEB RECON & INTELLIGENCE CONSOLE (v0.5.1)
================================================================================================
[*] Active Scraping Engines & Subsystems Initialized:
  ✔ Scrapling Core Engine: v0.5.1 ONLINE & ARMED
  ✔ Fast TLS Impersonator: READY (curl_cffi - Chrome/Firefox/Safari TLS fingerprinting)
  ✔ Stealth Browser Runtime: READY (Patchright Chromium v1248 - Anti-bot & Cloudflare bypass)
  ✔ Adaptive Format AI: ONLINE (openpyxl Excel Tables & ReportLab PDF Documents)
  ✔ Markdown RAG Converter: ACTIVE (markdownify v1.2.3)
  ℹ Web Studio Gateway: STANDBY (Type 'web' to launch http://127.0.0.1:8000)

                 === REGISTERED SCRAPING CAPABILITY ROSTER ===
 ─────────────────────────────────────────────────────────────────────────────
  Agent / Mode ID   Target Profile       Engine Core          Default Adapter
 ─────────────────────────────────────────────────────────────────────────────
  fast_probe        Fast Web Recon       TLS Impersonator     JSON + Markdown
  stealth_runner    Dynamic & SPAs       Patchright Chrome    Adaptive (PDF/XLSX)
  table_miner       Data Grids / HTML    DOM Extractor        Excel (.xlsx) Table
  doc_synthesizer   Articles & News      RAG Pipeline         PDF (.pdf) Document
  deep_query        CSS / XPath          Self-Healing Tracker Custom CSV / JSON
 ─────────────────────────────────────────────────────────────────────────────

scrapling> 
```

### Interactive Console Commands:

| Command | Action | Example |
| :--- | :--- | :--- |
| `<any url>` | **Direct scrape:** Type any raw URL to trigger auto-classification | `quotes.toscrape.com` |
| `scrape <url> [opts]` | Full autonomous scrape with custom options | `scrape https://quotes.toscrape.com --mode fast` |
| `inspect <url>` | Deep technical audit of headers, meta tags, and anti-bot setup | `inspect https://news.ycombinator.com` |
| `table <url>` | Extract all HTML tables and export directly to **Excel (.xlsx)** | `table https://www.w3schools.com/html/html_tables.asp` |
| `pdf <url>` | Synthesize article or text page into a formatted **PDF (.pdf)** | `pdf https://en.wikipedia.org/wiki/Web_scraping` |
| `query <url> <css>` | Target specific elements with CSS or XPath | `query https://quotes.toscrape.com .quote .text::text` |
| `links <url>` | Audit internal & external links | `links https://news.ycombinator.com --filter external` |
| `markdown <url>` | Output clean markdown content directly to the console | `markdown https://quotes.toscrape.com` |
| `history` | Display session scraping ledger and generated files | `history` |
| `open <file \| num>` | Open generated Excel/PDF in native OS viewer (Excel/Acrobat) | `open 1` or `open quotes.toscrape.com.xlsx` |
| `web` | Launch local Web Studio in background and open in browser | `web` |
| `status` | Run live health checks on scrapers and runtimes | `status` |
| `clear` | Clear the screen and refresh the banner | `clear` |
| `exit` | Quit the console | `exit` |

---

## ⚡ Adaptive PDF vs. Excel Intelligence

The scraper automatically inspects the structure of the target site:
- **Tabular Data Encountered** *(HTML tables, repetitive records, price grids)*:  
  👉 Auto-generates a multi-sheet **Excel Table (`.xlsx`)** with zebra row styling, borders, and auto-fitted columns.
- **Document / Article Prose Encountered** *(Blogs, news, wikis, essays)*:  
  👉 Auto-generates a formatted **PDF Document (`.pdf`)** with executive metadata, typography hierarchy, and page numbering.
- **Mixed Content**: Generates **both** formats!

---

## 🌐 Web Dashboard (Browser Studio)

You can launch the web interface anytime:
```bash
python main.py --web
# or inside the console:
scrapling> web
```
Navigate to **[http://127.0.0.1:8000](http://127.0.0.1:8000)** for:
- Live search & filter across links, tables, and images.
- 1-click downloads for `.xlsx`, `.pdf`, `.json`, `.md`, and `.csv`.
- Interactive custom CSS selector runner.

---

## 📁 File Structure

```text
├── core/
│   ├── __init__.py
│   └── scraper.py            # Scrapling Fetcher & StealthyFetcher engine
├── exporters/
│   ├── __init__.py
│   ├── classifier.py         # Content Classifier (Tabular vs. Document)
│   ├── excel_exporter.py     # Styled Excel workbook builder (openpyxl)
│   ├── pdf_exporter.py       # Styled PDF document builder (reportlab)
│   └── smart_exporter.py     # Adaptive exporter orchestrator
├── web/
│   └── templates/
│       └── index.html        # Modern web dashboard (Tailwind CSS)
├── interactive_console.py    # Cyberpunk command-center terminal REPL
├── cli.py                    # Direct CLI runner
├── server.py                 # FastAPI backend server with file downloads
├── main.py                   # Unified launcher (Console, Web, or CLI)
├── requirements.txt          # Python dependencies
└── README.md                 # Documentation
```
