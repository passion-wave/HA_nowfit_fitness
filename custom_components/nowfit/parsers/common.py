"""Parser helpers."""

from __future__ import annotations

import re

from bs4 import BeautifulSoup

from ..exceptions import ParseError

_SPACE = re.compile(r"\s+")


def soup(html: str) -> BeautifulSoup:
    if not html or not html.strip():
        raise ParseError("empty_html")
    return BeautifulSoup(html, "html.parser")


def text(value: str) -> str:
    return _SPACE.sub(" ", value.replace("\xa0", " ")).strip()


def integer(value: str, field: str) -> int:
    normalized = text(value)
    if not re.fullmatch(r"[0-9]+", normalized):
        raise ParseError(f"invalid_integer:{field}")
    return int(normalized)
