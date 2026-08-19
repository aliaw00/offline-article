# offline-article engineering documentation

## 1. Purpose

`offline-article` captures a rendered web page and turns it into an offline archive. The browser phase executes JavaScript and preserves the rendered DOM; the resource phase discovers referenced CSS, scripts, images, fonts, iframes, and metadata; the archive phase rewrites those references into a selected output format.

The 1.1.0 release changes the resource phase from serial downloading to bounded concurrent downloading. Asset failures are best-effort: the article is still saved, and failed visual resources are removed from the HTML so the saved document does not need the network to render a broken image.

## 2. Pipeline graph

```text
CLI / Python API
      |
      vv
   App.run()
      |
      +--> BrowserManager --> Playwright BrowserContext
      |                         |
      |                         +--> PageLoader --> rendered DOM
      |                                      |
      |                                      +--> serialize_page_dom()
      |
      +--> ResourceDiscoverer
      |       |
      |       +--> HTML resource discovery
      |       |
      |       +--> CSS discovery / nested @import discovery
      |
      +--> ResourceFetcher
      |       |
      |       +--> DiskCache
      |       |
      |       +--> HTTPX connection pool
      |       |
      |       +--> ThreadPoolExecutor
      |              |
      |              +--> successful assets
      |              +--> skipped failed assets
      |
      +--> remove_unavailable_visuals()
      |
      +--> ArchiveWriterFactory
              |
              +--> HtmlWriter
              +--> ZipWriter
              +--> DirWriter
              +--> MhtmlWriter
```

## 3. Why 1.1.0 is faster

Before 1.1.0, the application downloaded every resource one after another. A failed request used three attempts with 1 second and 2 second sleeps before the next URL could be attempted. In a page with many image URLs, one unavailable host could therefore dominate the capture time.

1.1.0 uses a bounded `ThreadPoolExecutor` and HTTPX connection pooling. The default is 16 concurrent asset downloads. Individual assets use one retry after the initial attempt, with a short delay only for transient transport/5xx/429 failures.

The goal is not to make every request succeed; the goal is to make the important page content available quickly while treating optional assets as best-effort.

## 4. Resource semantics

| Resource | Capture policy |
|---|---|
| Main HTML | Required. Browser capture failure aborts the save. |
| CSS | Discovered recursively because nested imports can contain fonts/backgrounds. |
| JavaScript | Best-effort asset. Successful scripts are captured and inlined for HTML output. |
| Images | Best-effort. Failed images are skipped and removed from the offline HTML references. |
| Fonts | Best-effort. Successful fonts are captured. |
| Favicons / metadata images | Best-effort. Failed visual metadata is removed. |
| Iframes | Best-effort; successfully fetched iframe content can be recursively inlined. |

## 5. Configuration

`CaptureConfig.concurrency` limits the maximum number of simultaneous asset requests.

`CaptureConfig.asset_retries` controls the number of retries after the first attempt. The default is `1`. Set it to `0` for the fastest possible best-effort capture on unreliable or blocked asset hosts.

Example:

```bash
offline-article save https://example.com/article \
  --output article.html \
  --concurrency 24 \
  --asset-retries 0
```

Use a smaller concurrency value for servers that rate-limit aggressively. Use a larger value only when the page contains many independent resources and your network/server can handle it.

## 6. File-by-file knowledge map

### Top-level

- `.github/workflows/ci.yml`: GitHub Actions workflow. Installs the project, installs Chromium, then runs Ruff, Mypy, and Pytest.
- `.gitignore`: ignores Python caches, virtual environments, build artifacts, logs, editor files, and local/private files.
- `.ruff.toml`: repository-wide Ruff style and lint configuration.
- `pyproject.toml`: package metadata, dependencies, CLI entry point, setuptools configuration, Ruff configuration, and Mypy configuration.
- `README.md`: user-facing installation, command usage, architecture summary, and development guide.
- `requirements.txt`: runtime dependencies.
- `requirements-dev.txt`: runtime dependencies plus test/lint/type-check tooling.

### `src/offline_article`

- `__init__.py`: package identity and version number.
- `__main__.py`: enables `python -m offline_article`.
- `app.py`: orchestration layer. It owns the complete capture pipeline and connects browser, discovery, fetching, rewriting, and archive strategies.
- `cli.py`: Typer command-line interface (`save`, `auth-login`, `inspect`, `validate`, `batch`, `update`).
- `config.py`: Pydantic configuration models and defaults.
- `exceptions.py`: domain-specific exception hierarchy.
- `logging.py`: logging setup with standard logging and optional Rich output.
- `types.py`: shared type declarations used by the package.

### `browser/`

- `cookies.py`: reads/writes JSON and Netscape cookie files.
- `manager.py`: owns Playwright lifecycle, browser selection, proxy setup, profile reuse, user-agent configuration, and JavaScript disabling.
- `__init__.py`: public browser API exports.

### `render/`

- `loader.py`: navigates pages, waits for the configured load state, detects login pages, optionally scrolls, and can block image requests during browser rendering to avoid duplicate browser-side image downloads.
- `__init__.py`: public render API exports.

### `discover/`

- `html.py`: parses HTML and extracts resource references from link/script/img/source/svg/meta/iframe elements.
- `css.py`: parses CSS with `tinycss2` and extracts `@import`, background-image, cursor, content, and font URLs.
- `resources.py`: recursively combines HTML and CSS discovery into one resource graph.
- `__init__.py`: public discovery API exports.

### `fetch/`

- `client.py`: HTTPX resource client. Contains connection pooling, retries, caching integration, concurrent batch fetching, and data-URI encoding.
- `cache.py`: persistent URL-keyed disk cache for downloaded resource bytes and content types.
- `__init__.py`: public fetch API exports.

### `rewrite/`

- `html.py`: converts captured HTML into an offline-friendly representation, including stylesheet/script/image/font/iframe inlining and failed-visual cleanup.
- `css.py`: recursively inlines CSS imports and URL-based assets.
- `__init__.py`: public rewrite API exports.

### `archive/`

- `base.py`: Strategy Pattern interface implemented by all archive writers.
- `factory.py`: selects the writer from the configured output format.
- `html_writer.py`: creates one self-contained HTML file.
- `dir_writer.py`: writes `index.html` and an `assets/` directory.
- `zip_writer.py`: builds a temporary directory archive and packages it into ZIP.
- `mhtml_writer.py`: creates a multipart/related MHTML archive.
- `__init__.py`: public archive API exports.

### `tests/`

- `conftest.py`: common local HTTP server fixtures and shared test setup.
- `unit/test_app.py`: application orchestration integration tests.
- `unit/test_archive.py`: archive writer and output-format tests.
- `unit/test_auth.py`: cookie/profile/browser session tests.
- `unit/test_cli.py`: command-line behavior tests.
- `unit/test_config.py`: configuration defaults and validation tests.
- `unit/test_discover.py`: HTML/CSS resource graph tests.
- `unit/test_fetch.py`: disk cache, HTTP fetch, retry, concurrency, and best-effort behavior tests.
- `unit/test_hard_sites.py`: shadow DOM and recursive iframe handling tests.
- `unit/test_login_workflow.py`: login detection and interactive workflow tests.
- `unit/test_mhtml.py`: MHTML structure and payload tests.
- `unit/test_rewrite.py`: HTML/CSS resource rewriting tests.

## 7. Developer workflow

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --no-build-isolation -e ".[dev]"
playwright install chromium
```

Fast checks:

```bash
PYTHONPATH=src python -m pytest -q
ruff check .
ruff format --check .
mypy src
```

For browser/E2E tests, Chromium must be installed. CI performs that installation automatically.

## 8. Debugging a slow capture

1. Run with `--verbose` to see discovery and fetch summaries.
2. If the page contains hundreds of resources, inspect it first with `offline-article inspect URL`.
3. Lower `--asset-retries` to `0` when the remote asset host is known to be unreachable.
4. Increase `--concurrency` moderately when the page has many independent resources.
5. Use the disk cache to avoid re-downloading resources from previous captures.

## 9. Design patterns and graph knowledge

The project combines a few useful software-design ideas:

- **Strategy Pattern**: `ArchiveWriter` defines the output contract; each writer implements one archive format.
- **Factory Pattern**: `ArchiveWriterFactory` decouples output-format selection from the application orchestrator.
- **Pipeline architecture**: rendering, discovery, fetching, rewriting, and writing are separated into modules with narrow responsibilities.
- **Cache-aside pattern**: `ResourceFetcher` checks `DiskCache` first, then populates it after a successful network request.
- **Best-effort concurrency**: independent assets are fetched in parallel, while one failed asset is isolated from the rest of the batch.

The resource dependency graph is intentionally recursive:

```text
HTML
 ├── stylesheet.css
 │    ├── @import nested.css
 │    │    └── font.woff2
 │    └── background.png
 ├── script.js
 ├── image.png
 ├── srcset image@2x.png
 └── iframe.html
      └── nested image / stylesheet / script
```

That graph is why resource discovery is separate from downloading: discovery describes *what exists*, while the fetcher decides *how efficiently it is retrieved*.
