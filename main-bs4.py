import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

import requests
from bs4 import BeautifulSoup


DEFAULT_URL = (
    "https://hckinfo.keralacourts.in/digicourt/Casedetailssearch/Statuscasenovoice"
)


def fetch_html(url: str, timeout_seconds: int = 20, max_attempts: int = 3) -> requests.Response:
    """
    Fetch raw HTML from the given URL using a session with a browser-like User-Agent.
    Retries a few times on transient network/server errors.
    Returns the full response object for access to headers, cookies, etc.
    """
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": (
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Connection": "keep-alive",
        }
    )

    last_error: Optional[Exception] = None
    for attempt in range(1, max_attempts + 1):
        try:
            response = session.get(url, timeout=timeout_seconds)
            response.raise_for_status()
            return response
        except Exception as exc:  # Only meaningful handling is retry with small backoff
            last_error = exc
            if attempt < max_attempts:
                time.sleep(1.0 * attempt)
            else:
                break
    assert last_error is not None  # for type-checkers
    raise RuntimeError(f"Failed to fetch URL after {max_attempts} attempts: {last_error}")


def write_html_to_file(html_content: str, filename: Optional[str] = None) -> str:
    """
    Write HTML content to a file with timestamp.
    Returns the filename that was written to.
    """
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"kerala_courts_page_{timestamp}.html"
    
    file_path = Path(filename)
    
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        print(f"HTML content written to: {file_path.absolute()}")
        return str(file_path.absolute())
    except Exception as e:
        print(f"Error writing HTML to file: {e}")
        raise


def print_response_info(response: requests.Response) -> None:
    """Print detailed information about the HTTP response including cookies and headers."""
    print("\n" + "="*60)
    print("RESPONSE INFORMATION")
    print("="*60)
    
    # Basic response info
    print(f"Status Code: {response.status_code}")
    print(f"Status Text: {response.reason}")
    print(f"URL: {response.url}")
    print(f"Content Length: {len(response.content)} bytes")
    print(f"Content Type: {response.headers.get('content-type', 'Unknown')}")
    print(f"Encoding: {response.encoding}")
    
    # Cookies
    print(f"\nCookies ({len(response.cookies)} total):")
    if response.cookies:
        for cookie in response.cookies:
            print(f"  - {cookie.name}: {cookie.value}")
            print(f"    Domain: {cookie.domain}")
            print(f"    Path: {cookie.path}")
            print(f"    Secure: {cookie.secure}")
            print(f"    HttpOnly: {getattr(cookie, 'has_nonstandard_attr', lambda x: False)('HttpOnly')}")
            if cookie.expires:
                print(f"    Expires: {cookie.expires}")
            print()
    else:
        print("  No cookies received")
    
    # Important headers
    important_headers = [
        'server', 'date', 'last-modified', 'etag', 'cache-control',
        'set-cookie', 'location', 'content-encoding', 'transfer-encoding'
    ]
    
    print("Important Headers:")
    for header in important_headers:
        value = response.headers.get(header)
        if value:
            print(f"  {header.title()}: {value}")
    
    # All headers (for debugging)
    print(f"\nAll Headers ({len(response.headers)} total):")
    for key, value in response.headers.items():
        print(f"  {key}: {value}")
    
    print("="*60)


def parse_with_beautifulsoup(html: str) -> BeautifulSoup:
    """Create a BeautifulSoup parser for the given HTML using the built-in parser."""
    return BeautifulSoup(html, "html.parser")


def describe_page(soup: BeautifulSoup) -> None:
    """Print a concise description of the page to stdout."""
    title_text = (soup.title.string.strip() if soup.title and soup.title.string else "")
    canonical = soup.find("link", rel=lambda v: v and "canonical" in v)
    canonical_href = canonical.get("href") if canonical else None

    forms = soup.find_all("form")
    anchors = soup.find_all("a")

    print("Page title:", title_text or "<no title>")
    if canonical_href:
        print("Canonical:", canonical_href)
    print("Forms:", len(forms))
    print("Links:", len(anchors))

    # Print the first form's inputs if present to confirm we reached the search page
    if forms:
        first_form = forms[0]
        inputs = first_form.find_all(["input", "select", "textarea", "button"])  # type: ignore[list-item]
        print("First form controls:")
        for el in inputs[:15]:  # Limit for brevity
            name = el.get("name")
            el_type = el.get("type") or el.name
            placeholder = el.get("placeholder")
            print(" -", el.name, {"name": name, "type": el_type, "placeholder": placeholder})


def main() -> None:
    url = DEFAULT_URL
    if len(sys.argv) > 1 and sys.argv[1].strip():
        url = sys.argv[1].strip()

    print(f"Fetching: {url}")
    
    # Fetch the response (now returns full response object)
    response = fetch_html(url)
    
    # Print detailed response information including cookies
    print_response_info(response)
    
    # Write HTML content to file
    html_content = response.text
    html_file = write_html_to_file(html_content)
    
    # Parse and describe the page
    soup = parse_with_beautifulsoup(html_content)
    describe_page(soup)
    
    print(f"\nSummary:")
    print(f"- HTML saved to: {html_file}")
    print(f"- Page title: {soup.title.string.strip() if soup.title and soup.title.string else 'No title'}")
    print(f"- Cookies received: {len(response.cookies)}")
    print(f"- Content size: {len(response.content)} bytes")


if __name__ == "__main__":
    main()


