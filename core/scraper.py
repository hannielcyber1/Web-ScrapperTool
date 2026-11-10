"""
Scrapling-powered Web Scraping Core Engine
Provides structured extraction, metadata collection, markdown generation,
and targeted CSS/XPath querying using Scrapling's Fetcher and StealthyFetcher.
"""

from typing import Dict, Any, List, Optional
import time
from urllib.parse import urlparse, urljoin
import re

import scrapling
from scrapling import Fetcher


class ScrapeResult:
    def __init__(self, raw_data: Dict[str, Any]):
        self.data = raw_data

    def to_dict(self) -> Dict[str, Any]:
        return self.data


class ScraplingEngine:
    """Wrapper around Scrapling fetchers and parsers."""

    @staticmethod
    def normalize_url(url: str) -> str:
        url = url.strip()
        if not url:
            raise ValueError("URL cannot be empty")
        if not (url.startswith("http://") or url.startswith("https://")):
            url = "https://" + url
        return url

    @classmethod
    def scrape(
        cls,
        url: str,
        mode: str = "fast",
        custom_css: Optional[str] = None,
        custom_xpath: Optional[str] = None,
        timeout: int = 30,
        impersonate: str = "chrome",
        solve_cloudflare: bool = True
    ) -> Dict[str, Any]:
        """
        Scrape a website using Scrapling.
        
        :param url: Target website URL
        :param mode: 'fast' (Fetcher with TLS impersonation) or 'stealth' (StealthyFetcher with headless browser)
        :param custom_css: Optional custom CSS selector to extract specific elements
        :param custom_xpath: Optional custom XPath expression
        :param timeout: Request timeout in seconds
        :param impersonate: Browser impersonation signature (chrome, safari, edge, firefox)
        :param solve_cloudflare: Whether to attempt automatic Cloudflare challenge solving (stealth mode)
        """
        target_url = cls.normalize_url(url)
        parsed_target = urlparse(target_url)
        base_domain = parsed_target.netloc

        start_time = time.time()
        error_msg = None
        response = None

        try:
            if mode == "stealth":
                try:
                    from scrapling import StealthyFetcher
                    response = StealthyFetcher.fetch(
                        target_url,
                        headless=True,
                        solve_cloudflare=solve_cloudflare,
                        timeout=timeout * 1000,
                        network_idle=True
                    )
                except Exception as e:
                    # Fallback to fast mode if headless browser fails or not ready
                    error_msg = f"Stealth fetch error ({e}), fell back to standard Fetcher."
                    response = Fetcher.get(target_url, impersonate=impersonate, timeout=timeout)
            else:
                response = Fetcher.get(target_url, impersonate=impersonate, timeout=timeout)
        except Exception as e:
            return {
                "success": False,
                "url": target_url,
                "error": str(e),
                "elapsed_seconds": round(time.time() - start_time, 2)
            }

        elapsed = round(time.time() - start_time, 2)

        # 1. Page Metadata
        title = ""
        try:
            title_el = response.css("title::text").get()
            title = title_el.strip() if title_el else ""
        except Exception:
            title = ""

        def get_meta(attr_name: str, attr_val: str) -> str:
            try:
                val = response.css(f'meta[{attr_name}="{attr_val}"]::attr(content)').get()
                return val.strip() if val else ""
            except Exception:
                return ""

        meta_description = (
            get_meta("name", "description")
            or get_meta("property", "og:description")
            or get_meta("name", "twitter:description")
        )
        meta_keywords = get_meta("name", "keywords")
        meta_author = get_meta("name", "author")
        og_title = get_meta("property", "og:title")
        og_image = get_meta("property", "og:image")
        og_type = get_meta("property", "og:type")
        canonical = ""
        try:
            canon = response.css('link[rel="canonical"]::attr(href)').get()
            canonical = canon.strip() if canon else ""
        except Exception:
            canonical = ""

        # 2. Markdown and Clean Text
        markdown_content = ""
        try:
            markdown_content = response.markdown()
        except Exception:
            # Fallback to simple text extraction if markdownify fails
            markdown_content = response.get_all_text() if hasattr(response, "get_all_text") else ""

        full_text = response.get_all_text() if hasattr(response, "get_all_text") else ""
        words = re.findall(r"\b\w+\b", full_text)
        word_count = len(words)

        # 3. Headings Hierarchy
        headings: List[Dict[str, Any]] = []
        try:
            for h in response.css("h1, h2, h3, h4, h5, h6"):
                tag = h.tag.lower() if hasattr(h, "tag") else "h"
                text = h.get_all_text().strip() if hasattr(h, "get_all_text") else ""
                if text:
                    headings.append({"tag": tag, "text": text})
        except Exception:
            pass

        # 4. Links Discovery
        links: List[Dict[str, Any]] = []
        seen_links = set()
        try:
            for a in response.css("a"):
                href = a.attrib.get("href", "").strip() if hasattr(a, "attrib") else ""
                text = a.get_all_text().strip() if hasattr(a, "get_all_text") else ""
                if not href or href.startswith("javascript:") or href.startswith("mailto:") or href.startswith("tel:"):
                    continue

                full_href = urljoin(target_url, href)
                if full_href in seen_links:
                    continue
                seen_links.add(full_href)

                link_netloc = urlparse(full_href).netloc
                is_internal = (link_netloc == base_domain) or (not link_netloc)

                links.append({
                    "text": text or "[No anchor text]",
                    "url": full_href,
                    "is_internal": is_internal
                })
        except Exception:
            pass

        # 5. Media & Images
        images: List[Dict[str, Any]] = []
        seen_images = set()
        try:
            for img in response.css("img"):
                src = (
                    img.attrib.get("src")
                    or img.attrib.get("data-src")
                    or img.attrib.get("srcset")
                    or ""
                ).strip()
                if not src:
                    continue
                full_src = urljoin(target_url, src.split()[0])
                if full_src in seen_images:
                    continue
                seen_images.add(full_src)

                images.append({
                    "src": full_src,
                    "alt": img.attrib.get("alt", "").strip(),
                    "title": img.attrib.get("title", "").strip()
                })
        except Exception:
            pass

        # 6. Tables Extraction
        tables_data: List[List[List[str]]] = []
        try:
            for table in response.css("table"):
                table_rows: List[List[str]] = []
                for row in table.css("tr"):
                    cols = [
                        col.get_all_text().strip()
                        for col in row.css("th, td")
                        if hasattr(col, "get_all_text")
                    ]
                    if cols:
                        table_rows.append(cols)
                if table_rows:
                    tables_data.append(table_rows)
        except Exception:
            pass

        # 7. Custom CSS / XPath Queries if specified
        custom_matches: List[Dict[str, Any]] = []
        if custom_css:
            try:
                selected = response.css(custom_css)
                for i, el in enumerate(selected):
                    text = el.get_all_text().strip() if hasattr(el, "get_all_text") else ""
                    html = el.html_content if hasattr(el, "html_content") else ""
                    raw_attrs = el.attrib if hasattr(el, "attrib") else {}
                    attrs = dict(raw_attrs) if raw_attrs else {}
                    custom_matches.append({
                        "index": i + 1,
                        "text": text,
                        "html": html[:500] + ("..." if len(html) > 500 else ""),
                        "attributes": attrs
                    })
            except Exception as e:
                custom_matches.append({"error": f"CSS selector error: {str(e)}"})

        if custom_xpath:
            try:
                selected = response.xpath(custom_xpath)
                for i, el in enumerate(selected):
                    text = el.get_all_text().strip() if hasattr(el, "get_all_text") else str(el)
                    html = el.html_content if hasattr(el, "html_content") else ""
                    raw_attrs = el.attrib if hasattr(el, "attrib") else {}
                    attrs = dict(raw_attrs) if raw_attrs else {}
                    custom_matches.append({
                        "index": i + 1,
                        "text": text,
                        "html": html[:500] + ("..." if len(html) > 500 else ""),
                        "attributes": attrs
                    })
            except Exception as e:
                custom_matches.append({"error": f"XPath error: {str(e)}"})

        return {
            "success": True,
            "url": target_url,
            "status_code": getattr(response, "status", 200),
            "mode_used": mode,
            "warning": error_msg,
            "elapsed_seconds": elapsed,
            "metadata": {
                "title": title,
                "description": meta_description,
                "keywords": meta_keywords,
                "author": meta_author,
                "canonical": canonical,
                "og_title": og_title,
                "og_image": og_image,
                "og_type": og_type,
                "word_count": word_count,
            },
            "markdown": markdown_content,
            "stats": {
                "headings_count": len(headings),
                "links_count": len(links),
                "images_count": len(images),
                "tables_count": len(tables_data),
                "words_count": word_count,
            },
            "headings": headings,
            "links": links,
            "images": images,
            "tables": tables_data,
            "custom_matches": custom_matches
        }
