# offline-article

`offline-article` is a Linux-first, Python-based CLI tool designed to capture and save full web pages for offline reading. The default output is a single, self-contained, offline-ready HTML file. It also supports exporting to ZIP archives, local directories, and MHTML files.

It is built for real-world usage, supporting normal static sites, JavaScript-heavy SPAs, and authenticated pages using Playwright.

---

## 🚀 Features

* **Single-File Output**: Saves pages as completely self-contained `.html` files (with base64 inlined assets) by default.
* **Format Plugin System**: Export captured pages to `html`, `zip`, `dir`, or `mhtml`.
* **Authenticated Capture**: Import browser cookies, sessions, or use an interactive login flow.
* **Modern Tech Stack**: Powered by Playwright, Typer, Rich, Pydantic, and HTTPX.

---

## 🛠️ Installation & Setup

### Requirements
* Python 3.12+
* Linux (with support for Playwright browser dependencies)

### Developer Installation
To set up a local development environment:

1. Clone the repository and navigate into it:
   ```bash
   git clone <repo-url> offline-article
   cd offline-article
   ```

2. Create and activate a virtual environment:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. Install the package in editable mode with development dependencies:
   ```bash
   pip install --no-build-isolation -e .[dev]
   ```

4. Install Playwright browser binaries:
   ```bash
   playwright install chromium
   ```

---

## 💻 CLI Usage

Once installed, you can use the `offline-article` command.

### 1. Save a Web Page (Default to single-file HTML)
```bash
offline-article save https://example.com --output example.html
```

### 2. Save in a Different Format
To save as a ZIP archive:
```bash
offline-article save https://example.com --format zip --output example.zip
```

To save as a raw directory containing assets:
```bash
offline-article save https://example.com --format dir --output ./example_archive/
```

### 3. Authenticate / Login Flow
Launch an interactive browser to log in and capture profiles/cookies:
```bash
offline-article auth-login --browser chromium --profile ~/.config/offline-article/profiles/default
```

### 4. Inspect a URL
Preview compatibility and resource metrics for a URL without saving it:
```bash
offline-article inspect https://example.com
```

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
