# Acceptance report

## Automated release-candidate checks

- Python compile check
- Ruff lint and formatting
- Public parser including a genuine numeric zero, ambiguity and invalid values
- Dynamic login form discovery and cross-origin rejection
- Synthetic account and history parsing, including DST gap rejection
- Visit deduplication, duration sum, local week/month and three-state coverage semantics
- Single-flight authentication recovery and required reauth without a password
- Cookie domain/expiry handling
- Native sections dashboard generation with injected entity IDs

Local result on Python 3.14.6: **29 passed**, **90% total selected core coverage**; authentication
95%, training/time logic 97%. Ruff formatting and lint passed. All integration platform modules
also imported successfully against Home Assistant 2026.9.3. The live public endpoint returned six
unambiguous clubs and exactly one Poing match with an integer occupancy value.

The Home Assistant MCP found five v1 references in the `nowfit-poing` dashboard. Its broad scan of
automation/script bodies was partial because the target server timed out while reading many
individual configurations. The reference graph returned no explicit automation matches, but
templated references in unread configurations remain an open migration check.

## Outstanding live acceptance

- Successful member login with authorized credentials
- Stable provider account identity and account-mismatch protection
- Real account/history selectors and pagination/coverage behavior
- Cookie rotation, expiry and rejected-session behavior
- Config-flow, unload, migration and reauth tests using the Home Assistant pytest harness
- Dashboard render and narrow iPhone viewport check on the target Home Assistant version
- A soak period covering transient failures and provider throttling

This is not a production acceptance until those items pass.
