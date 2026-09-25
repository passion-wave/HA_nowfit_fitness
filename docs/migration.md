# Migration from the YAML prototype

The current production instance still uses the v1 package and template files. Migration is a
separate, reversible operation and must happen only after approval.

1. Back up the Home Assistant configuration and entity registry.
2. Install v2 and restart Home Assistant once so the Python integration is loaded.
3. Add a public NowFit entry and select Now Fit Poing.
4. Verify occupancy and failure behavior under temporary, clearly distinct entity IDs.
5. Add a member entry only after an authorized live login acceptance test.
6. Resolve real v2 entity IDs from the registry and update dashboards/automations deliberately.
7. Disable only the old NowFit REST/template poller after v2 succeeds; do not replace the entire
   REST or template configuration.
8. Keep the v1 files and backup through the observation window, then remove them separately.

Known v1 IDs to account for:

- `sensor.nowfit_poing_auslastung`
- `sensor.nowfit_poing_abrufzeitpunkt`
- `sensor.nowfit_poing_auslastungsstufe`
- `binary_sensor.nowfit_poing_daten_frisch`

Equal display names do not preserve entity IDs, unique IDs, recorder history or statistics. Do not
take over registry identities without a reviewed mapping and explicit approval.

Read-only inventory on 2026-09-25 found all four v1 IDs in the storage dashboard `nowfit-poing`,
with the occupancy sensor referenced twice (five card references total). The MCP automation/script
scan was partial due to target-server timeouts; therefore templated consumers must be checked again
before any entity ID is removed or renamed.

Rollback: disable/remove the v2 entries, restore the backed-up v1 files if they were changed, check
configuration, and restart only with approval. Downgrading code does not automatically downgrade a
future storage schema.
