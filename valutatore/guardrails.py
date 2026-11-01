"""Deterministic checks on the researcher's output."""

import html
import re
from typing import Any, Tuple

import httpx

NOT_FOUND = "not found"
MAX_KEYWORD_WORDS = 5
MIN_KEYWORD_WORDS = 2
# Words that must sit next to the publisher's name on the page for it to count as named.
PUBLISHER_MARKERS = ("publisher", "published", "publishing", "©", "copyright")
WINDOW = 80


def _keyword_words(keyword: str) -> int:
    """Words of a keyword, not counting the "tabletop RPG" qualifier added to every search."""
    return len(re.sub(r"(?i)\btabletop\s+rpgs?\b", " ", keyword).split())


def _page_text(url: str) -> str | None:
    try:
        r = httpx.get(url, timeout=20, follow_redirects=True, headers={"User-Agent": "Mozilla/5.0"})
        r.raise_for_status()
    except Exception:
        return None
    text = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", r.text)
    text = html.unescape(re.sub(r"<[^>]+>", " ", text))
    return re.sub(r"\s+", " ", text).lower()


def _names_publisher(page: str, publisher: str) -> bool:
    name = re.sub(r"\s+", " ", publisher).strip().lower()
    for m in re.finditer(re.escape(name), page):
        around = page[max(0, m.start() - WINDOW) : m.end() + WINDOW]
        if any(marker in around for marker in PUBLISHER_MARKERS):
            return True
    return False


def check_similar_games(output) -> Tuple[bool, Any]:
    result = getattr(output, "pydantic", None)
    if result is None:
        return False, "The output must be a valid SimilarGamesResult."

    errors = []
    for kw in result.keywords_used:
        words = _keyword_words(kw)
        if not MIN_KEYWORD_WORDS <= words <= MAX_KEYWORD_WORDS:
            errors.append(
                f"Keyword '{kw}' has {words} words (not counting 'tabletop RPG'): "
                f"use {MIN_KEYWORD_WORDS} to {MAX_KEYWORD_WORDS}."
            )
    for game in result.games:
        if game.keyword not in result.keywords_used:
            errors.append(f"'{game.title}': keyword '{game.keyword}' is not in keywords_used.")
    if errors:
        return False, "\n".join(errors)

    # A publisher the source page does not name next to a publishing marker becomes "not found".
    changed = False
    for game in result.games:
        if game.publisher == NOT_FOUND:
            continue
        page = _page_text(game.source)
        if page is not None and not _names_publisher(page, game.publisher):
            game.publisher = NOT_FOUND
            changed = True
    if changed:
        output.raw = result.model_dump_json()
        output.json_dict = result.model_dump()
    return True, output


def check_report(output) -> Tuple[bool, Any]:
    """Structure of the publisher report: one title and three sections, in any language."""
    text = re.sub(r"^```(?:markdown)?\s*|\s*```$", "", (getattr(output, "raw", "") or "").strip())
    lines = text.splitlines()
    errors = []

    if sum(1 for line in lines if re.match(r"#\s+\S", line)) != 1:
        errors.append("The report must have exactly one '# <game title>' heading.")

    sections: list[list[str]] = []
    for line in lines:
        if re.match(r"##\s+\S", line):
            sections.append([])
        elif sections:
            sections[-1].append(line)

    if len(sections) != 3:
        errors.append(
            f"The report must have exactly three '##' sections (description, similar games, "
            f"strengths and weaknesses); it has {len(sections)}."
        )
    else:
        for n, body in enumerate(sections, start=1):
            if not "".join(body).strip():
                errors.append(f"Section {n} is empty.")
        bullets = sum(1 for line in sections[2] if re.match(r"\s*[-*]\s+\S", line))
        if bullets < 2:
            errors.append("The strengths and weaknesses section must list strengths and weaknesses as bullets.")

    if errors:
        return False, "\n".join(errors)
    return True, output
