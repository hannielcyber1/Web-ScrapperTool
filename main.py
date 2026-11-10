"""
Unified Launcher for the Scrapling Web Scraping Studio
Launches the Cyberpunk Interactive Terminal Console or the Web UI Dashboard.
"""

import sys
import argparse
import webbrowser
import threading
import time


def launch_console():
    from interactive_console import main_loop
    main_loop()


def launch_web(host: str = "127.0.0.1", port: int = 8000, open_browser: bool = True):
    from server import start_server

    url = f"http://{host}:{port}"
    if open_browser:
        def _open():
            time.sleep(1.2)
            try:
                webbrowser.open(url)
            except Exception:
                pass
        threading.Thread(target=_open, daemon=True).start()

    start_server(host=host, port=port)


def main():
    parser = argparse.ArgumentParser(
        description="Scrapling Web Scraping Studio — Extract metadata, text, markdown, links, images, and custom data from any website."
    )
    parser.add_argument("--console", action="store_true", help="Launch the full-screen interactive Terminal Console")
    parser.add_argument("--web", action="store_true", help="Launch the Web UI Dashboard in browser")
    parser.add_argument("--cli", action="store_true", help="Launch standard CLI prompt")
    parser.add_argument("--host", default="127.0.0.1", help="Host address for Web UI (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8000, help="Port for Web UI (default: 8000)")
    parser.add_argument("--no-browser", action="store_true", help="Do not automatically open browser on web launch")
    parser.add_argument("url", nargs="?", help="Direct URL to scrape in CLI mode")
    parser.add_argument("--mode", choices=["fast", "stealth"], default="fast", help="Scraping mode (fast or stealth)")
    parser.add_argument("--css", help="Custom CSS selector")
    parser.add_argument("--xpath", help="Custom XPath")
    parser.add_argument("--format", default="auto", help="auto, excel, pdf, both")

    args = parser.parse_args()

    # Direct URL provided via CLI
    if args.url:
        from cli import main as cli_main
        cli_main()
        return

    # Flags specified
    if args.console:
        launch_console()
        return

    if args.web:
        launch_web(host=args.host, port=args.port, open_browser=not args.no_browser)
        return

    if args.cli:
        from cli import run_interactive
        run_interactive()
        return

    # Interactive choice or default to the Interactive Console
    print("=" * 70)
    print(" 🕷️  SCRAPLING-AI // AUTONOMOUS WEB RECON & INTELLIGENCE")
    print("=" * 70)
    print("  [1] 💻 Interactive Terminal Console [Command-Center REPL] (Default)")
    print("  [2] 🌐 Web Dashboard (Browser Studio on http://127.0.0.1:8000)")
    print("  [3] ❌ Exit\n")

    try:
        choice = input("Select an option [1/2/3] (Press Enter for [1]): ").strip()
    except (KeyboardInterrupt, EOFError):
        print("\nExiting.")
        return

    if choice in ("1", ""):
        launch_console()
    elif choice == "2":
        launch_web(host=args.host, port=args.port, open_browser=not args.no_browser)
    else:
        print("Goodbye!")


if __name__ == "__main__":
    main()
