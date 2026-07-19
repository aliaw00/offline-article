import logging
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console

from offline_article.app import App
from offline_article.config import CaptureConfig
from offline_article.logging import setup_logging

app = typer.Typer(
    name="offline-article",
    help="Save entire web pages for offline use.",
    no_args_is_help=True,
)
console = Console()
logger = logging.getLogger("offline-article")


def common_callback(
    verbose: Annotated[bool, typer.Option("--verbose", "-v", help="Enable verbose logging")] = False,
    debug: Annotated[bool, typer.Option("--debug", "-d", help="Enable debug logging")] = False,
) -> None:
    """Common callback to initialize logging levels."""
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
        typer.Option("--browser", "-b", help="Browser to use: chromium, firefox, webkit"),
    ] = "chromium",
    profile: Annotated[
        Path | None,
        typer.Option("--profile", help="Path to browser profile directory to use"),
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
        typer.Option("--timeout", help="Timeout in seconds for operations"),
    ] = 30,
    scroll: Annotated[
        bool,
        typer.Option("--scroll", help="Enable scrolling down page to trigger lazy loading"),
    ] = False,
    proxy: Annotated[
        str | None,
        typer.Option("--proxy", help="Proxy server URL"),
    ] = None,
    user_agent: Annotated[
        str | None,
        typer.Option("--user-agent", help="Custom User-Agent string"),
    ] = None,
    no_images: Annotated[
        bool,
        typer.Option("--no-images", help="Disable loading images in the browser"),
    ] = False,
    no_js: Annotated[
        bool,
        typer.Option("--no-js", help="Disable JavaScript execution in the browser"),
    ] = False,
    verbose: Annotated[bool, typer.Option("--verbose", "-v", help="Enable verbose logging")] = False,
    debug: Annotated[bool, typer.Option("--debug", "-d", help="Enable debug logging")] = False,
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
        )
    except Exception as e:
        console.print(f"[bold red]Error in configuration parameters:[/] {e}")
        raise typer.Exit(1) from e

    console.print(f"[green]Starting capture for:[/] {url}")
    try:
        app_runner = App(config)
        saved_path = app_runner.run(url, output)
        console.print(f"[bold green]Success![/] Saved page to: [bold]{saved_path}[/]")
    except Exception as e:
        console.print(f"[bold red]Execution error:[/] {e}")
        raise typer.Exit(1) from e


@app.command(name="auth-login")
def auth_login_command(
    browser: Annotated[
        str,
        typer.Option("--browser", "-b", help="Browser to use: chromium, firefox, webkit"),
    ] = "chromium",
    profile: Annotated[
        Path | None,
        typer.Option("--profile", help="Path to browser profile directory to use"),
    ] = None,
    verbose: Annotated[bool, typer.Option("--verbose", "-v", help="Enable verbose logging")] = False,
    debug: Annotated[bool, typer.Option("--debug", "-d", help="Enable debug logging")] = False,
) -> None:
    """
    Launch browser and let user log in manually to save session/profile context.
    """
    setup_logging(verbose=verbose, debug=debug)
    console.print(f"[blue]Starting interactive login flow using {browser}...[/]")
    # TODO: Implement login workflow helper


@app.command(name="inspect")
def inspect_command(
    url: Annotated[str, typer.Argument(help="URL to inspect")],
    verbose: Annotated[bool, typer.Option("--verbose", "-v", help="Enable verbose logging")] = False,
    debug: Annotated[bool, typer.Option("--debug", "-d", help="Enable debug logging")] = False,
) -> None:
    """
    Inspect a URL, showing discovered resources and potential compatibility issues.
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
    debug: Annotated[bool, typer.Option("--debug", "-d", help="Enable debug logging")] = False,
) -> None:
    """
    Validate a saved offline archive for local links integrity and completeness.
    """
    setup_logging(verbose=verbose, debug=debug)
    console.print(f"[blue]Validating offline archive at:[/] {path}")
    # TODO: Implement integrity verification


@app.command(name="batch")
def batch_command(
    file_path: Annotated[Path, typer.Argument(help="Path to file containing URLs (one per line)")],
    format: Annotated[str, typer.Option("--format", "-f")] = "html",
    verbose: Annotated[bool, typer.Option("--verbose", "-v", help="Enable verbose logging")] = False,
    debug: Annotated[bool, typer.Option("--debug", "-d", help="Enable debug logging")] = False,
) -> None:
    """
    Save multiple URLs in a batch process from a text file.
    """
    setup_logging(verbose=verbose, debug=debug)
    console.print(f"[blue]Processing batch from:[/] {file_path}")
    # TODO: Implement batch processing pipeline


if __name__ == "__main__":
    app()
