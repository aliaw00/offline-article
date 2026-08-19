# offline-article

`offline-article` is a Python-based CLI tool designed to capture and save full web pages for offline reading. The default output is a single, self-contained, offline-ready HTML file. It also supports exporting to ZIP archives, local directories, and MHTML files.

It is built for real-world usage, supporting normal static sites, JavaScript-heavy SPAs, and authenticated pages using Playwright.

---

## What's new in 1.1.0

- Concurrent asset downloads with a bounded worker pool.
- HTTPX connection pooling for better network reuse.
- Best-effort asset capture: a failed image/font/script no longer stalls or aborts the article save.
- Faster default retries: one retry after the initial asset request instead of three attempts with 1s/2s sleeps.
- Failed visual references are removed from the saved HTML, so offline reading does not try to fetch broken image URLs.
- `--concurrency` and `--asset-retries` controls for tuning performance.
- `--no-images` now prevents the browser from downloading images twice during rendering; image assets can still be fetched separately for the final archive.
- Updated engineering and file-by-file documentation.

## 🚀 Features
- Self-contained `.html` output with embedded CSS, JavaScript, images, fonts, and recursive iframe content when available.
- `html`, `zip`, `dir`, and `mhtml` archive formats.
- JavaScript-heavy page support through Playwright.
- Authenticated page capture through cookies or a persistent browser profile.
- Recursive CSS resource discovery including `@import`, background images, cursors, and fonts.
- Persistent disk cache for previously downloaded assets.
- Bounded concurrent downloads for fast pages with many independent resources.
- Graceful degradation when optional resources are unavailable.

---

## 🛠️ Installation & Setup

### Requirements
Requirements: Python 3.12+ and a Playwright-supported browser.

### Developer Installation
To set up a local development environment:

1. Clone the repository and navigate into it:
   ```bash
   git clone https://github.com/aliaw00/offline-article.git offline-article
   cd offline-article
   ```

2. Create and activate a virtual environment:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. Install the package in editable mode with development dependencies:
   ```bash
   pip install --no-build-isolation -e ".[dev]"
   ```

4. Install Playwright browser binaries:
   ```bash
   playwright install chromium
   ```

---

## 💻 CLI Usage

Once installed, you can use the `offline-article` command.

### Global Options

| Option | Description |
|--------|-------------|
| `--help`, `-h` | Show help message and exit |
| `--version`, `-V` | Show version and exit |
| `--verbose`, `-v` | Enable verbose logging |
| `--debug` | Enable debug mode with detailed logging |

### 1. Save a Web Page (Default to single-file HTML)

```bash
offline-article save https://example.com --output example.html
```

**Options:**

| Flag | Description |
|------|-------------|
| `--format`, `-f` | Output format: `html` (default), `zip`, `dir`, `mhtml` |
| `--output`, `-o` | Output file path or directory |
| `--browser`, `-b` | Browser engine: `chromium`, `firefox`, `webkit` |
| `--profile` | Path to browser profile directory for session/cookie reuse |
| `--cookies` | Path to Netscape-format cookies file |
| `--wait` | Wait condition: `load`, `domcontentloaded`, `networkidle` |
| `--timeout` | Timeout in seconds for page load and network operations |
| `--scroll` | Enable scrolling to trigger lazy-loaded content |
| `--proxy` | Proxy server URL (e.g., `http://user:pass@host:port`) |
| `--user-agent` | Custom User-Agent string |
| `--no-images` | Disable loading images (saves bandwidth) |
| `--no-js` | Disable JavaScript execution |
| `--interactive`, `-i` | Run browser headful and pause for manual login |
| `--open-after-save` | Open saved file in default browser after saving |
| `--keep-temp` | Keep temporary files after completion |
| `--overwrite` | Force overwrite existing files without prompting |
| `--concurrency` | Maximum concurrent asset downloads; default `16` |
| `--asset-retries` | Retries after first asset attempt; default `1` |

### 2. Save in a Different Format

To save as a ZIP archive:
```bash
offline-article save https://example.com --format zip --output example.zip
```

To save as a raw directory containing assets:
```bash
offline-article save https://example.com --format dir --output ./example_archive/
```

To save as MHTML:
```bash
offline-article save https://example.com --format mhtml --output example.mhtml
```

### 3. Authenticate / Login Flow

Launch an interactive browser to log in and capture profiles/cookies:
```bash
offline-article auth-login --browser chromium --profile ~/.config/offline-article/profiles/default
```

**Options:**

| Flag | Description |
|------|-------------|
| `--browser` | Browser engine to use |
| `--profile` | Path to store/load browser profile |
| `--timeout` | Timeout in seconds for login session |

### 4. Inspect a URL

Preview compatibility and resource metrics for a URL without saving it:
```bash
offline-article inspect https://example.com
```

**Options:**

| Flag | Description |
|------|-------------|
| `--browser` | Browser engine to use for inspection |

### 5. Validate a Saved Archive

Check a saved page for resource completeness and link integrity:
```bash
offline-article validate example.html
```

### 6. Batch Process URLs

Save multiple pages listed in a text file:
```bash
offline-article batch urls.txt --format html
```

**Options:**

| Flag | Description |
|------|-------------|
| `--format` | Output format for all URLs |
| `--output-dir` | Directory to save all outputs |
| `--profile` | Browser profile path for all requests |
| `--cookies` | Cookies file path for all requests |
| `--wait` | Wait condition for all pages |
| `--timeout` | Timeout for all pages |
| `--scroll` | Enable scrolling for all pages |
| `--overwrite` | Force overwrite all existing files |

### 7. Update offline-article

Automatically check for and install updates:
```bash
offline-article update
```

This command will upgrade the package to the latest available version using pip.

**Options:**

| Flag | Description |
|------|-------------|
| `--verbose`, `-v` | Enable verbose logging |
| `--debug` | Enable debug mode with detailed logging |

### 8. Check Version

Display the current version of offline-article:
```bash
offline-article --version
# or
offline-article -V
```

### 9. Faster / Concurrency

For a faster best-effort capture on a page with many images:
   ```bash
   offline-article save https://example.com \
   --output article.html \
   --concurrency 24 \
   --asset-retries 0
   ```

---


## How saving works

```text
URL
 |
 v
Playwright render
 |
 v
Rendered DOM
 |
 v
HTML/CSS resource discovery
 |
 v
Persistent cache + concurrent HTTP fetch
 |
 +--> success --> rewrite/embed --> archive writer
 |
 +--> failure --> log + skip --> continue capture
```

The browser renders the page first so dynamic content can be captured. Resource discovery then builds a URL graph from HTML and recursively referenced CSS. The fetcher checks the persistent cache, downloads uncached assets concurrently, and treats optional asset failures as non-fatal. Successful resources are then rewritten into the selected archive format.

---

## Performance tuning

The default `--concurrency 16` is intended to be a safe starting point. Increase it moderately for pages with many independent resources. Reduce it for remote hosts that rate-limit or reject bursts.

Set `--asset-retries 0` to skip failed optional assets immediately. Set it to `1` or `2` if transient network failures are common.

The disk cache lives under `~/.cache/offline-article` by default and avoids downloading unchanged URLs again during subsequent captures.


---

## 🧪 Development & Testing

All validation tools (`pytest`, `ruff`, and `mypy`) are set up for local development.

### Running Tests
Execute the unit test suite using `pytest`:
```bash
pytest
```

### Code Formatting and Linting
We use **Ruff** for fast linting and code formatting:
```bash
# Check code for lint issues
ruff check .

# Automatically fix fixable lint issues
ruff check --fix .

# Format code
ruff format .
```

### Type Checking
Ensure type safety using `mypy`:
```bash
mypy src
```

The browser-dependent tests require the Playwright Chromium executable. CI installs it before running the test suite.

See [docs/ENGINEERING.md](docs/ENGINEERING.md) for the architecture, pipeline graph, resource semantics, developer workflow, and design-pattern overview.

See [docs/FILE_GUIDE.md](docs/FILE_GUIDE.md) for a file-by-file explanation of the codebase.

---

## 📁 Project Structure

```
offline-article/
├── src/offline_article/    # Main source code
│   ├── cli.py              # CLI entrypoint
│   ├── app.py              # Core application logic
│   ├── config.py           # Configuration models
│   ├── browser/            # Browser automation
│   ├── discover/           # Resource discovery
│   ├── fetch/              # Resource fetching
│   ├── rewrite/            # HTML/CSS rewriting
│   ├── archive/            # Output writers
│   └── auth/               # Authentication helpers
├── tests/                  # Test suite
├── examples/               # Usage examples
└── docs/                   # Documentation
```

---

## 🔐 Security Notes

* Never store credentials in plain text
* Prefer browser profile/session reuse
* Only use user-authorized sessions
* Cookies and profiles are stored securely in user-specified directories

Use only browser profiles, cookies, and authenticated sessions that you are authorized to access. Do not commit credentials, exported cookies, or private browser profiles to source control.

---

## 📝 Examples

### Basic save
```bash
offline-article save https://example.com -o example.html
```

### Save with custom browser and timeout
```bash
offline-article save https://example.com --browser firefox --timeout 60 -o example.html
```

### Interactive login then save
```bash
# First, authenticate
offline-article auth-login --browser chromium --profile ~/.my-profile

# Then save protected page using the profile
offline-article save https://protected-site.com/dashboard --profile ~/.my-profile -o dashboard.html
```

### Batch save with overwrite protection disabled
```bash
offline-article batch urls.txt --format html --output-dir ./archives --overwrite
```

---

## 🤝 Contributing

Contributions are welcome! Please read our contributing guidelines before submitting PRs.

## 📄 License

MIT License - see LICENSE file for details.
