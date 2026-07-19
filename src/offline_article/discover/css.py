import logging

import tinycss2
from tinycss2.ast import AtRule, Declaration, QualifiedRule

from offline_article.discover.html import normalize_url

logger = logging.getLogger("offline-article.discover.css")


def discover_css_resources(css_content: str, base_url: str) -> dict[str, set[str]]:
    """
    Parses CSS content using tinycss2 to extract url() links:
    - stylesheets (from @import rules)
    - images (from background-image, background, content, cursor etc.)
    - fonts (from @font-face rules src declarations)
    """
    resources: dict[str, set[str]] = {
        "stylesheets": set(),
        "images": set(),
        "fonts": set(),
    }

    # Skip comments and parse stylesheet
    rules = tinycss2.parse_stylesheet(css_content, skip_comments=True)

    def get_url_from_token(token: tinycss2.ast.Node) -> str | None:
        """Helper to get url value from a tinycss2 token node."""
        if token.type == "url":
            return token.value
        if token.type == "function" and token.lower_name == "url":
            for sub_token in token.arguments:
                if sub_token.type == "string":
                    return sub_token.value
        return None

    def process_declaration(dec: Declaration, is_font_face: bool = False) -> None:
        """Processes a CSS declaration to find url() tokens."""
        if not hasattr(dec, "value") or dec.value is None:
            return

        for token in dec.value:
            url_val = get_url_from_token(token)
            if url_val:
                abs_url = normalize_url(base_url, url_val)
                if not abs_url:
                    continue

                # Categorize resource type
                name = getattr(dec, "name", "").lower()
                if is_font_face or "font" in name:
                    resources["fonts"].add(abs_url)
                elif "image" in name or "background" in name or "cursor" in name or "content" in name:
                    resources["images"].add(abs_url)
                else:
                    # Default fallback to image type for generic urls
                    resources["images"].add(abs_url)

    def process_rules(rules_list: list[tinycss2.ast.Node]) -> None:
        """Recursively parses CSS rule nodes."""
        for rule in rules_list:
            if isinstance(rule, AtRule):
                if rule.lower_at_keyword == "import":
                    # Find URL in the import prelude
                    for token in rule.prelude:
                        url_val = get_url_from_token(token)
                        if url_val:
                            abs_url = normalize_url(base_url, url_val)
                            if abs_url:
                                resources["stylesheets"].add(abs_url)
                            break
                        elif token.type == "string":
                            abs_url = normalize_url(base_url, token.value)
                            if abs_url:
                                resources["stylesheets"].add(abs_url)
                            break
                elif rule.lower_at_keyword == "font-face":
                    # Process declarations in @font-face
                    decls = tinycss2.parse_declaration_list(rule.content or [])
                    for dec in decls:
                        if isinstance(dec, Declaration):
                            process_declaration(dec, is_font_face=True)
                elif rule.content:
                    # Parse nested rules (e.g. inside @media)
                    nested_rules = tinycss2.parse_rule_list(rule.content)
                    process_rules(nested_rules)

            elif isinstance(rule, QualifiedRule):
                # Process selector rules list
                decls = tinycss2.parse_declaration_list(rule.content or [])
                for dec in decls:
                    if isinstance(dec, Declaration):
                        process_declaration(dec)

    process_rules(rules)

    # Clean up empty strings
    for category in resources:
        resources[category] = {url for url in resources[category] if url}

    return resources
