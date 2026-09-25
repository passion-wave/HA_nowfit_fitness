from custom_components.nowfit.exceptions import ParseError, UnsafeRedirect
from custom_components.nowfit.flow_helpers import safe_error_code


def test_safe_error_code_allows_only_internal_codes() -> None:
    assert safe_error_code(ParseError("account_markers_missing")) == "account_markers_missing"
    assert safe_error_code(UnsafeRedirect("https://example.test/?token=secret")) == "redacted"
