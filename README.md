# NowFit for Home Assistant

Unofficial HACS custom integration for the NowFit member portal.

Repository: <https://github.com/passion-wave/HA_nowfit_fitness>

Current development status:

- Public studio occupancy: implemented and covered by parser/client tests.
- Native config flow, coordinator, sensors and rate-limited refresh button: implemented.
- Account/history parsers, visit cleanup and timezone-aware derivations: implemented against
  synthetic fixtures matching the observed structure.
- Member login form discovery: verified for the public form and implemented dynamically.
- Successful member login, cookie lifetime/rotation and reauthentication: require an authorized
  local live acceptance test before they may be described as production-ready.

No member HTML, credentials, cookies or access-code images are included in this repository.

See [architecture](docs/architecture.md), [protocol observations](docs/protocol-observations.md),
[migration](docs/migration.md), and the [acceptance report](docs/acceptance-report.md).

## Installation

During development, add `https://github.com/passion-wave/HA_nowfit_fitness` as a custom integration
repository in HACS and select a development release when one is published. Alternatively, copy
`custom_components/nowfit` below Home Assistant's `/config/custom_components/` for a local test.
Restart once after installing Python integration code, then add **NowFit** from Settings > Devices
& services.

Create the public studio entry first. Member data is a separate entry and remains optional. The
provided dashboards are examples and never overwrite Home Assistant's dashboard storage.

## Privacy and scope

The integration stores no HTML. A member password is saved only after explicit opt-in; otherwise an
expired session uses Home Assistant's reauthentication flow. Personal sensor states may still be
recorded by Home Assistant's Recorder and visible to authorized Home Assistant users.
