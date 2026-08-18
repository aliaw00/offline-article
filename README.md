# offline-article

`offline-article` is a Python-based CLI tool designed to capture and save full web pages for offline reading. The default output is a single, self-contained, offline-ready HTML file. It also supports exporting to ZIP archives, local directories, and MHTML files.

It is built for real-world usage, supporting normal static sites, JavaScript-heavy SPAs, and authenticated pages using Playwright.

---

## 🚀 Features

* **Single-File Output**: Saves pages as completely self-contained `.html` files (with base64 inlined assets) by default.
* **Format Plugin System**: Export captured pages to `html`, `zip`, `dir`, or `mhtml`.
* **Authenticated Capture**: Import browser cookies, sessions, or use an interactive login flow.
* **Modern Tech Stack**: Powered by Playwright, Typer, Rich, Pydantic, and HTTPX.
* **Smart Overwrite Protection**: Prompts before overwriting existing files, with `--overwrite` flag to force.
* **Comprehensive CLI Help**: Detailed help messages for all commands and flags.
* **Version Management**: Built-in version display and automatic update command.

---

## 🛠️ Installation & Setup

### Requirements
* Python 3.12+
* Linux (with support for Playwright browser dependencies)

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
| `--format` | Output format: `html` (default), `zip`, `dir`, `mhtml` |
| `--output`, `-o` | Output file path or directory |
| `--browser` | Browser engine: `chromium`, `firefox`, `webkit` |
| `--profile` | Path to browser profile directory for session/cookie reuse |
| `--cookies` | Path to Netscape-format cookies file |
| `--wait` | Wait condition: `load`, `domcontentloaded`, `networkidle` |
| `--timeout` | Timeout in seconds for page load and network operations |
| `--scroll` | Enable scrolling to trigger lazy-loaded content |
| `--proxy` | Proxy server URL (e.g., `http://user:pass@host:port`) |
| `--user-agent` | Custom User-Agent string |
| `--no-images` | Disable loading images (saves bandwidth) |
| `--no-js` | Disable JavaScript execution |
| `--interactive` | Run browser headful and pause for manual login |
| `--open-after-save` | Open saved file in default browser after saving |
| `--keep-temp` | Keep temporary files after completion |
| `--overwrite` | Force overwrite existing files without prompting |

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
