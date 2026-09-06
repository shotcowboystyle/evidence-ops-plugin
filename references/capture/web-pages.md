# Capturing Web Pages

This guide covers the preservation of web content as digital evidence. An operator needs these techniques when a webpage—which may be dynamic, authenticated, or subject to imminent alteration or deletion—must be recorded in a format that captures its exact state at a specific point in time, allowing its content to be verifiable in the future.

## Why it matters

Web content is inherently ephemeral. A simple visual screenshot lacks structural metadata, is easily manipulated using basic image editing tools, and fails to capture interactive elements, text data, or off-screen content. By saving the structural HTML, associated CSS/JS assets, and the HTTP response headers, operators ensure a significantly more robust and complete record of what the remote server delivered to the client at the precise time of capture. This allows for detailed forensic analysis of the DOM and network requests long after the target page has been modified or taken offline.

## Tools

| Tool | Platform | Notes |
| --- | --- | --- |
| `single-file` | both | Node CLI and browser extension; produces robust, self-contained HTML files |
| `curl` / `wget` | both | Essential for raw HTML and headers; `wget` natively supports WARC format |
| `wpull` | both | Python-based web crawler tailored for WARC generation |
| `browsertrix` | both | Containerized crawler suitable for complex sites and high-fidelity WARC |
| Browser Print | both | "Print to PDF" serves as a standard visual fallback for layout preservation |
| `mitmproxy` | both | TLS interception proxy for capturing raw API payloads and headers |

## Documenting the capture environment

Before initiating a web capture, the operator must record the operational context. Web servers respond differently based on IP geolocation, User-Agent strings, and session cookies. Without logging the exact parameters of the capture environment, the resulting evidence may lack the necessary foundation to explain why a specific version of a page was served. Always record whether a VPN was active, the browser profile used, and the precise URL structure including any query parameters.

## Advanced techniques

### TLS Interception and API Capture
For modern Single Page Applications (SPAs), the HTML alone often contains no actual data; the content is loaded dynamically via background JSON APIs. In these cases, using a TLS intercept proxy like `mitmproxy` allows the operator to capture the raw JSON payloads and authentication tokens that populate the view. This network capture (saved as a HAR or PCAP file) must be logged and hashed alongside the visual representation of the page.

### Programmatic Capture with Headless Browsers
For capturing large volumes of web evidence, tools like Playwright or Puppeteer can automate the extraction. However, automated browsers often reveal themselves via navigator attributes (e.g., `navigator.webdriver`). Target servers may block these requests or serve altered "bot" content. Operators must carefully strip these flags or rely on real browser profiles when automating evidence collection.

## Practical recipes

Capturing a accurate representation of a webpage requires rendering the DOM, inlining assets, and keeping a record of the network transaction.

```bash
# 1. Record the exact capture time in UTC
export CAPTURE_TIME=$(date -u +"%Y-%m-%dT%H%M%SZ")

# 2. Capture the response headers separately
# Headers contain the server date, content type, and critical caching or redirect directives
curl -sSI "https://example.com/article" > "logs/example-headers-${CAPTURE_TIME}.txt"

# 3. Capture the fully rendered page with SingleFile
# This inlines images, CSS, and web fonts into a single HTML document
single-file "https://example.com/article" "evidence/originals/example-page-${CAPTURE_TIME}.html"

# 4. Generate a Web ARChive (WARC) file using wget
# WARC is the archival standard for web captures, storing both requests and responses
wget --warc-file="evidence/originals/example-archive-${CAPTURE_TIME}" \
     --warc-cdx \
     --page-requisites \
     --html-extension \
     "https://example.com/article"

# 5. Immediately hash the resulting evidence on macOS
# Note: On GNU/Linux, replace `shasum -a 256` with `sha256sum`
shasum -a 256 "evidence/originals/example-page-${CAPTURE_TIME}.html" > "manifests/example-page-${CAPTURE_TIME}.sha256"
```

## Pitfalls

- **Dynamic Content Disconnect:** Capturing JavaScript-heavy single-page applications without a rendering engine (e.g., using raw `curl` or plain `wget`) results in empty DOMs or partial content. Use `single-file`, `browsertrix`, or a headless browser tool for these.
- **Login-Walled Context:** Capturing behind a login wall implies the captured state is heavily personalized to an authenticated session. This context must be recorded in the custody log, including the capturing operator's identity, the account used, and the precise retrieval timestamp. The page seen may not be the page served to the public.
- **Screenshots are Incomplete Evidence:** Relying solely on screenshots misses the underlying code and network context. If you must use screenshots as supplementary visual proof, capture a full-page scroll and immediately hash and timestamp the resulting image file.
- **Delayed Cryptographic Anchoring:** Failing to hash and timestamp the capture immediately leaves a window of doubt where the file could theoretically be altered without detection. Always run `shasum -a 256` (or `sha256sum`) the absolute moment the capture writes to disk, followed by an OpenTimestamps calendar submission.

## See also

- [OpenTimestamps](../timestamping/opentimestamps.md)
- [Hashing Algorithms](../hashing/algorithms-and-manifests.md)
- [macOS vs Linux Tooling](../hashing/macos-vs-linux-tooling.md)
- [Chain of Custody Principles](../custody/chain-of-custody-principles.md)
