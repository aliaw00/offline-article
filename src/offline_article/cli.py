import logging
from pathlib import Path
from typing import Annotated, Any

import typer
from rich.console import Console
from rich.prompt import Confirm

from offline_article import __version__
from offline_article.app import App
from offline_article.config import CaptureConfig
from offline_article.logging import setup_logging

app = typer.Typer(
    name="offline-article",
    help="Save entire web pages for offline use.",
    no_args_is_help=True,
    context_settings={"help_option_names": ["-h", "--help"]},
)
console = Console()
logger = logging.getLogger("offline-article")


def version_callback(value: bool) -> None:
    """Callback to display version information."""
    if value:
        console.print(f"offline-article version [bold green]{__version__}[/]")
        raise typer.Exit()


@app.callback()
def main_callback(
    verbose: Annotated[bool, typer.Option("--verbose", "-v", help="Enable verbose logging")] = False,
    debug: Annotated[bool, typer.Option("--debug", help="Enable debug mode with detailed logging")] = False,
    version: Annotated[
        bool | None,
        typer.Option(
            "--version",
            "-V",
            callback=version_callback,
            help="Show version and exit",
            is_eager=True,
        ),
    ] = None,
) -> None:
    """Common callback to initialize logging levels and handle global options."""
    setup_logging(verbose=verbose, debug=debug)


@app.command(name="save")
def save_command(
    url: Annotated[str, typer.Argument(help="URL of the web page to save")],
    output: Annotated[
        Path | None,
        typer.Option("--output", "-o", help="Output file path or directory (defaults to auto-generated name)"),
    ] = None,
    format: Annotated[
        str,
        typer.Option("--format", "-f", help="Output archive format: html, zip, dir, mhtml"),
    ] = "html",
    browser: Annotated[
        str,
        typer.Option("--browser", "-b", help="Browser engine to use: chromium, firefox, webkit"),
    ] = "chromium",
    profile: Annotated[
        Path | None,
        typer.Option("--profile", help="Path to browser profile directory for session/cookie reuse"),
    ] = None,
    cookies: Annotated[
        Path | None,
        typer.Option("--cookies", help="Path to cookie file to import (JSON or Netscape format)"),
    ] = None,
    wait: Annotated[
        str,
        typer.Option("--wait", help="Wait condition after page load: load, domcontentloaded, networkidle"),
    ] = "networkidle",
    timeout: Annotated[
        int,
        typer.Option("--timeout", help="Timeout in seconds for page load and network operations"),
    ] = 30,
    scroll: Annotated[
        bool,
        typer.Option("--scroll", help="Enable scrolling down page to trigger lazy-loaded content"),
    ] = False,
    proxy: Annotated[
        str | None,
        typer.Option("--proxy", help="Proxy server URL (e.g., http://user:pass@host:port)"),
    ] = None,
    user_agent: Annotated[
        str | None,
        typer.Option("--user-agent", help="Custom User-Agent string to spoof browser identity"),
    ] = None,
    no_images: Annotated[
        bool,
        typer.Option("--no-images", help="Disable loading images in the browser (saves bandwidth)"),
    ] = False,
    no_js: Annotated[
        bool,
        typer.Option("--no-js", help="Disable JavaScript execution in the browser"),
    ] = False,
    verbose: Annotated[bool, typer.Option("--verbose", "-v", help="Enable verbose logging")] = False,
    debug: Annotated[bool, typer.Option("--debug", help="Enable debug mode with detailed logging")] = False,
    interactive: Annotated[
        bool,
        typer.Option("--interactive", "-i", help="Run browser in headful mode and pause for manual interaction/login"),
    ] = False,
    overwrite: Annotated[
        bool,
        typer.Option("--overwrite", help="Force overwrite existing output files without prompting"),
    ] = False,
) -> None:
    """
    Save a web page as a self-contained offline archive.
    """
    setup_logging(verbose=verbose, debug=debug)
    logger.info(f"Saving URL: {url} (Format: {format}, Browser: {browser})")

    # Construct the config object
    try:
        config = CaptureConfig(
            format=format,
            browser=browser,
            profile_path=profile,
            cookies_path=cookies,
            wait_until=wait,
            timeout=timeout,
            scroll=scroll,
            proxy=proxy,
            user_agent=user_agent,
            no_images=no_images,
            no_js=no_js,
            verbose=verbose,
            debug=debug,
            interactive=interactive,
        )
    except Exception as e:
        console.print(f"[bold red]Error in configuration parameters:[/] {e}")
        raise typer.Exit(1) from e

    console.print(f"[green]Starting capture for:[/] {url}")
    
    # Check if output file exists and handle overwrite logic
    if output is not None and output.exists() and not overwrite:
        if interactive or not Confirm.ask(
            f"File [bold]{output}[/] already exists. Overwrite?",
            default=False
        ):
            console.print("[yellow]Operation cancelled.[/]")
            raise typer.Exit(0)
    
    try:
        app_runner = App(config)
        with console.status("[bold green]Capturing page resources (this may take a few seconds)...", spinner="dots"):
            saved_path = app_runner.run(url, output)
        console.print(f"[bold green]Success![/] Saved page to: [bold]{saved_path}[/]")
    except Exception as e:
        console.print(f"[bold red]Execution error:[/] {e}")
        raise typer.Exit(1) from e


@app.command(name="auth-login")
def auth_login_command(
    browser: Annotated[
        str,
        typer.Option("--browser", "-b", help="Browser engine to use: chromium, firefox, webkit"),
    ] = "chromium",
    profile: Annotated[
        Path | None,
        typer.Option("--profile", help="Path to browser profile directory for session/cookie reuse"),
    ] = None,
    verbose: Annotated[bool, typer.Option("--verbose", "-v", help="Enable verbose logging")] = False,
    debug: Annotated[bool, typer.Option("--debug", help="Enable debug mode with detailed logging")] = False,
) -> None:
    """
    Launch browser and let user log in manually to save session/profile context.
    """
    setup_logging(verbose=verbose, debug=debug)

    if not profile:
        profile = Path.home() / ".config" / "offline-article" / "profiles" / "default"

    console.print(f"[blue]Starting interactive login flow using {browser}...[/]")
    console.print(f"[green]Using browser profile directory:[/] {profile}")

    config = CaptureConfig(
        browser=browser,
        profile_path=profile,
        interactive=True,
        verbose=verbose,
        debug=debug,
    )

    from offline_article.browser import BrowserManager

    browser_manager = BrowserManager(config)

    try:
        with browser_manager.session() as context:
            page = context.new_page()
            # Open a basic page so user can navigate or we can let them use blank page
            page.goto("https://google.com")

            console.print("\n[bold green]Browser window is now open.[/]")
            console.print("Please navigate to your target website, perform any logins/OAuth flows,")
            console.print("then close the browser window or press [Enter] in this terminal to save session data.\n")

            input("Press [Enter] when finished...")

        console.print("[bold green]Success![/] Session profile saved successfully.")
    except Exception as e:
        console.print(f"[bold red]Login flow failed:[/] {e}")
        raise typer.Exit(1) from e


@app.command(name="inspect")
def inspect_command(
    url: Annotated[str, typer.Argument(help="URL to inspect for resource discovery")],
    browser: Annotated[
        str,
        typer.Option("--browser", "-b", help="Browser engine to use: chromium, firefox, webkit"),
    ] = "chromium",
    verbose: Annotated[bool, typer.Option("--verbose", "-v", help="Enable verbose logging")] = False,
    debug: Annotated[bool, typer.Option("--debug", help="Enable debug mode with detailed logging")] = False,
) -> None:
    """
    Inspect a URL, showing discovered resources and potential compatibility issues.
    
    This command opens the URL in a headless browser, renders the page, and lists
    all discovered assets (images, scripts, stylesheets, fonts, etc.) that would
    be captured during a save operation.
    """
    setup_logging(verbose=verbose, debug=debug)
    console.print(f"[blue]Inspecting URL:[/] {url}")

    from rich.table import Table

    from offline_article.browser import BrowserManager
    from offline_article.discover import ResourceDiscoverer
    from offline_article.render import PageLoader

    config = CaptureConfig(verbose=verbose, debug=debug)
    browser_manager = BrowserManager(config)
    page_loader = PageLoader(config)
    discoverer = ResourceDiscoverer()

    try:
        with browser_manager.session() as context:
            page = page_loader.load_page(context, url)
            html_content = page.content()
            resources = discoverer.discover_from_html(html_content, url)

        table = Table(title=f"Discovered Assets for {url}")
        table.add_column("Asset Type", style="cyan")
        table.add_column("Count", style="green")

        for category, urls in resources.items():
            table.add_row(category.capitalize(), str(len(urls)))

        console.print(table)

        if verbose or debug:
            for category, urls in resources.items():
                if urls:
                    console.print(f"\n[bold]{category.capitalize()}:[/]")
                    for u in sorted(urls):
                        console.print(f"  - {u}")
    except Exception as e:
        console.print(f"[bold red]Inspection error:[/] {e}")
        raise typer.Exit(1) from e


@app.command(name="validate")
def validate_command(
    path: Annotated[Path, typer.Argument(help="Path to the saved offline archive file or directory")],
    verbose: Annotated[bool, typer.Option("--verbose", "-v", help="Enable verbose logging")] = False,
    debug: Annotated[bool, typer.Option("--debug", help="Enable debug mode with detailed logging")] = False,
) -> None:
    """
    Validate a saved offline archive for local links integrity and completeness.
    
    Checks for external resource references that should be inlined, broken local
    links, and missing required files (e.g., index.html in ZIP/directory archives).
    """
    setup_logging(verbose=verbose, debug=debug)
    console.print(f"[blue]Validating offline archive at:[/] {path}")

    if not path.exists():
        console.print(f"[bold red]Path does not exist:[/] {path}")
        raise typer.Exit(1)

    from bs4 import BeautifulSoup

    from offline_article.discover.html import get_str_attr

    issues: list[str] = []

    def check_html(html_text: str, check_file_exists_callback: Any = None) -> None:
        soup = BeautifulSoup(html_text, "lxml")

        # Check stylesheets
        for link in soup.find_all("link"):
            rel: Any = link.get("rel") or []
            rel_list = rel if isinstance(rel, list) else [rel]
            rel_lower = [str(r).lower() for r in rel_list]
            if "stylesheet" in rel_lower:
                href = get_str_attr(link, "href")
                if href:
                    if href.lower().startswith("http"):
                        issues.append(f"External stylesheet link: {href}")
                    elif check_file_exists_callback:
                        if not check_file_exists_callback(href):
                            issues.append(f"Broken local stylesheet link: {href}")

        # Check scripts
        for script in soup.find_all("script"):
            src = get_str_attr(script, "src")
            if src:
                if src.lower().startswith("http"):
                    issues.append(f"External script link: {src}")
                elif check_file_exists_callback:
                    if not check_file_exists_callback(src):
                        issues.append(f"Broken local script link: {src}")

        # Check images
        for img in soup.find_all("img"):
            src = get_str_attr(img, "src")
            if src:
                if src.lower().startswith("http"):
                    issues.append(f"External image link: {src}")
                elif check_file_exists_callback:
                    if not check_file_exists_callback(src):
                        issues.append(f"Broken local image link: {src}")

    if path.is_file() and path.suffix.lower() == ".zip":
        import zipfile

        try:
            with zipfile.ZipFile(path) as zf:
                namelist = zf.namelist()
                if "index.html" not in namelist:
                    issues.append("Missing index.html inside ZIP package.")
                else:
                    html_text = zf.read("index.html").decode("utf-8", errors="replace")
                    check_html(html_text, lambda rel: rel in namelist or rel.replace("\\", "/") in namelist)
        except Exception as e:
            issues.append(f"Failed to read ZIP archive: {e}")

    elif path.is_dir():
        index_file = path / "index.html"
        if not index_file.is_file():
            issues.append("Missing index.html inside extracted directory.")
        else:
            html_text = index_file.read_text(encoding="utf-8")
            check_html(html_text, lambda rel: (path / rel).is_file())

    elif path.is_file() and path.suffix.lower() in (".html", ".htm"):
        html_text = path.read_text(encoding="utf-8")
        check_html(html_text)

    else:
        console.print(
            "[bold red]Error:[/] Unsupported file extension for validation. Must be .zip, .html, or directory."
        )
        raise typer.Exit(1)

    if not issues:
        console.print("[bold green]Success![/] Offline archive is healthy. All references are fully self-contained.")
    else:
        console.print(f"[bold yellow]Validation found {len(issues)} issues:[/]")
        for issue in issues:
            console.print(f"  [red]-[/] {issue}")
        raise typer.Exit(1)


@app.command(name="batch")
def batch_command(
    file_path: Annotated[Path, typer.Argument(help="Path to text file containing URLs (one per line, # for comments)")],
    output_dir: Annotated[
        Path,
        typer.Option("--output-dir", help="Directory where captured files will be saved"),
    ] = Path("."),
    format: Annotated[
        str,
        typer.Option("--format", "-f", help="Output archive format: html, zip, dir, mhtml"),
    ] = "html",
    browser: Annotated[
        str,
        typer.Option("--browser", "-b", help="Browser engine to use: chromium, firefox, webkit"),
    ] = "chromium",
    profile: Annotated[
        Path | None,
        typer.Option("--profile", help="Path to browser profile directory for session/cookie reuse"),
    ] = None,
    cookies: Annotated[
        Path | None,
        typer.Option("--cookies", help="Path to cookie file to import (JSON or Netscape format)"),
    ] = None,
    wait: Annotated[
        str,
        typer.Option("--wait", help="Wait condition after page load: load, domcontentloaded, networkidle"),
    ] = "networkidle",
    timeout: Annotated[
        int,
        typer.Option("--timeout", help="Timeout in seconds for page load and network operations"),
    ] = 30,
    scroll: Annotated[
        bool,
        typer.Option("--scroll", help="Enable scrolling down page to trigger lazy-loaded content"),
    ] = False,
    verbose: Annotated[bool, typer.Option("--verbose", "-v", help="Enable verbose logging")] = False,
    debug: Annotated[bool, typer.Option("--debug", help="Enable debug mode with detailed logging")] = False,
    overwrite: Annotated[
        bool,
        typer.Option("--overwrite", help="Force overwrite existing output files without prompting"),
    ] = False,
) -> None:
    """
    Save multiple URLs in a batch process from a text file.
    
    Reads URLs from a text file (one per line, lines starting with # are comments)
    and saves each page using the specified format and options.
    """
    setup_logging(verbose=verbose, debug=debug)
    console.print(f"[blue]Processing batch from:[/] {file_path}")

    if not file_path.is_file():
        console.print(f"[bold red]File not found:[/] {file_path}")
        raise typer.Exit(1)

    urls: list[str] = []
    with open(file_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                urls.append(line)

    if not urls:
        console.print("[bold yellow]No valid URLs found in file.[/]")
        return

    console.print(f"[green]Found {len(urls)} URLs to capture.[/]")
    output_dir.mkdir(parents=True, exist_ok=True)

    config = CaptureConfig(
        format=format,
        browser=browser,
        profile_path=profile,
        cookies_path=cookies,
        wait_until=wait,
        timeout=timeout,
        scroll=scroll,
        verbose=verbose,
        debug=debug,
    )
    app_runner = App(config)

    success_count = 0
    for i, url in enumerate(urls, 1):
        console.print(f"\n[bold cyan][{i}/{len(urls)}][/] Capturing {url}...")
        
        # Determine output path
        from urllib.parse import urlparse

        parsed = urlparse(url)
        host = parsed.netloc.replace(".", "_") or "page"
        path_part = parsed.path.strip("/").replace("/", "_")
        filename = f"{host}_{path_part}" if path_part else host
        out_path = output_dir / f"{filename}.{format}"
        
        # Check for existing file and handle overwrite
        if out_path.exists() and not overwrite:
            if not Confirm.ask(
                f"File [bold]{out_path}[/] already exists. Overwrite?",
                default=False
            ):
                console.print("[yellow]Skipping.[/]")
                continue
        
        try:
            with console.status("[bold green]Capturing page...", spinner="dots"):
                saved_path = app_runner.run(url, out_path)

            console.print(f"  [bold green]Success![/] Saved to: [bold]{saved_path}[/]")
            success_count += 1
        except Exception as e:
            console.print(f"  [bold red]Failed:[/] {e}")

    console.print(f"\n[bold green]Batch complete![/] Successfully captured {success_count}/{len(urls)} pages.")


@app.command(name="update")
def update_command(
    verbose: Annotated[bool, typer.Option("--verbose", "-v", help="Enable verbose logging")] = False,
    debug: Annotated[bool, typer.Option("--debug", help="Enable debug mode with detailed logging")] = False,
) -> None:
    """
    Update offline-article to the latest version.
    
    This command checks for updates and upgrades the package automatically.
    It uses pip to perform the upgrade in-place.
    """
    import subprocess
    import sys
    
    setup_logging(verbose=verbose, debug=debug)
    console.print("[blue]Checking for updates...[/]")
    
    try:
        # Run pip install --upgrade offline-article
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "--upgrade", "offline-article"],
            capture_output=True,
            text=True,
            check=False,
        )
        
        if result.returncode == 0:
            if "Successfully installed" in result.stdout or "already up-to-date" in result.stdout.lower():
                console.print("[bold green]offline-article is up to date![/]")
            else:
                console.print(f"[bold green]Update completed![/]\n{result.stdout}")
        else:
            console.print(f"[bold red]Update failed:[/] {result.stderr}")
            raise typer.Exit(1)
            
    except Exception as e:
        console.print(f"[bold red]Update error:[/] {e}")
        raise typer.Exit(1) from e


if __name__ == "__main__":
    app()
