# Changelog

## Unreleased

- Fix the public-club selector payload for Home Assistant 2026.9.
- Fix Options Flow initialization for Home Assistant 2026.9.
- Add privacy-safe member setup failure codes to the integration log.
- Recover once from a provider 5xx caused by a stale member session, with a persistent
  30-minute guard against repeated login attempts.
- Tag provider failures with allowlisted HTTP status and operation codes without logging URLs,
  response bodies, cookies, or credentials.

## 2.0.0 - 2026-09-25

- Replace the YAML/regex prototype with a HACS-ready custom integration.
- Add public studio discovery, occupancy coordinator, sensors and refresh button.
- Add member login/session framework, account/history parsers and reauthentication flow.
- Add normalized visit cleanup, coverage semantics, diagnostics allowlist and dashboards.
