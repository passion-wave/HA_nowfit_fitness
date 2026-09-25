"""Discover the real password login form without executing JavaScript."""

from __future__ import annotations

from urllib.parse import urljoin, urlparse

from bs4 import Tag

from ..const import ALLOWED_HOST, BASE_URL, LOGIN_PATH
from ..exceptions import UnsafeRedirect, UnsupportedLogin
from ..models import LoginForm
from .common import soup


def parse_login_form(html: str, page_url: str = f"{BASE_URL}{LOGIN_PATH}") -> LoginForm:
    document = soup(html)
    candidates: list[tuple[Tag, Tag, Tag]] = []
    for form in document.find_all("form"):
        password = form.find("input", attrs={"type": "password", "name": True})
        email = form.find("input", attrs={"name": True, "type": lambda v: v in {"email", "text"}})
        if password is not None and email is not None:
            candidates.append((form, email, password))
    if len(candidates) != 1:
        raise UnsupportedLogin("password_form_not_unique")
    form, email, password = candidates[0]
    method = str(form.get("method", "get")).casefold()
    if method != "post":
        raise UnsupportedLogin("login_method_not_post")
    action = urljoin(page_url, str(form.get("action") or page_url))
    parsed = urlparse(action)
    if (
        parsed.scheme != "https"
        or parsed.hostname != ALLOWED_HOST
        or parsed.port not in {None, 443}
    ):
        raise UnsafeRedirect("unsafe_login_action")
    if parsed.path != LOGIN_PATH:
        raise UnsupportedLogin("unexpected_login_path")
    hidden: list[tuple[str, str]] = []
    checkbox = form.find("input", attrs={"type": "checkbox", "name": True})
    remember_name = str(checkbox["name"]) if checkbox is not None else None
    for input_tag in form.find_all("input", attrs={"name": True}):
        field_type = str(input_tag.get("type", "text")).casefold()
        name = str(input_tag["name"])
        if field_type == "hidden" and name != remember_name:
            hidden.append((name, str(input_tag.get("value", ""))))
    return LoginForm(
        action=action,
        method=method,
        enctype=str(form.get("enctype") or "application/x-www-form-urlencoded"),
        email_name=str(email["name"]),
        password_name=str(password["name"]),
        remember_name=remember_name,
        hidden_fields=tuple(hidden),
    )
