# Troubleshooting

## Public data unavailable

Check Home Assistant's integration page and internet access to `nowfit.memberarea.club`. A failed
request makes the entity unavailable; it never substitutes zero people. Manual refresh has a
60-second local cooldown and cannot bypass provider rate limits.

## Member data unavailable

Open Settings > Devices & services > NowFit. If reauthentication is requested, enter the password
there. The public studio entry remains independent. When a stale session makes an authenticated
provider endpoint return a server error, the integration discards only its NowFit cookies and
attempts one controlled login. Failed automatic logins are limited across Home Assistant reloads
by a persistent 30-minute guard.

## Values changed after a portal update

Disable the affected entry and retain a sanitized structural sample only if it can be made free of
names, identifiers, timestamps, tokens, cookies and other account data. Never post raw member HTML
in an issue. Parser changes should first receive synthetic regression fixtures.

## Diagnostics

The downloadable diagnostics contain versions, entry type, source health and aggregate parser row
counts only. They intentionally omit email, names, cookies, HTML and visit timestamps.
