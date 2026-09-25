# Architecture

NowFit uses two independent Home Assistant config-entry types.

- A **public** entry discovers clubs from the public counter page and polls one response every five
  minutes. One coordinator serves occupancy, last-success, source-status and refresh entities.
- A **member** entry owns its own `aiohttp` cookie jar, versioned cookie store and `SessionManager`.
  Account and training history have separate coordinators, refresh intervals and availability.

All HTTP requests are asynchronous, size-bounded and limited to HTTPS on
`nowfit.memberarea.club`. Redirects are followed manually so every hop can be checked. Parsers use
Beautiful Soup and return typed models; entity properties read normalized coordinator data only.

The member session may perform one single-flight re-login when a stored password was explicitly
enabled. Without it, Home Assistant opens the native reauthentication flow. No invented refresh
endpoint or keepalive request is used.

Dashboard generation is a pure function that accepts IDs already resolved from Home Assistant's
entity registry. It does not write Lovelace storage.
