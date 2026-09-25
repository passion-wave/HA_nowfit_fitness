"""Generate native dashboards from entity-registry-resolved IDs."""

from __future__ import annotations


def public_dashboard(entity_ids: dict[str, str]) -> dict:
    occupancy = entity_ids["occupancy"]
    last_success = entity_ids["public_last_success"]
    refresh = entity_ids["public_refresh"]
    return {
        "title": "NowFit",
        "views": [
            {
                "title": "NowFit",
                "path": "nowfit",
                "icon": "mdi:dumbbell",
                "type": "sections",
                "max_columns": 3,
                "sections": [
                    {
                        "type": "grid",
                        "cards": [
                            {
                                "type": "heading",
                                "heading": "Jetzt im Studio",
                                "icon": "mdi:account-group",
                            },
                            {"type": "tile", "entity": occupancy, "name": "Aktuell eingecheckt"},
                            {"type": "tile", "entity": last_success, "name": "Stand"},
                            {
                                "type": "button",
                                "entity": refresh,
                                "name": "Auslastung aktualisieren",
                            },
                            {
                                "type": "history-graph",
                                "title": "Eingecheckte Personen · 24 Stunden",
                                "hours_to_show": 24,
                                "entities": [{"entity": occupancy, "name": "Personen"}],
                            },
                        ],
                    }
                ],
            }
        ],
    }


def personal_dashboard(entity_ids: dict[str, str]) -> dict:
    dashboard = public_dashboard(entity_ids)
    sections = dashboard["views"][0]["sections"]
    sections.extend(
        [
            {
                "type": "grid",
                "cards": [
                    {"type": "heading", "heading": "Meine Ziele", "icon": "mdi:target"},
                    {
                        "type": "tile",
                        "entity": entity_ids["week_goal_current"],
                        "name": "Diese Woche",
                    },
                    {
                        "type": "gauge",
                        "entity": entity_ids["week_goal_display_percent"],
                        "name": "Wochenziel",
                        "min": 0,
                        "max": 100,
                    },
                    {
                        "type": "tile",
                        "entity": entity_ids["checkins_month"],
                        "name": "Check-ins diesen Monat",
                    },
                ],
            },
            {
                "type": "grid",
                "cards": [
                    {"type": "heading", "heading": "Mein Verlauf", "icon": "mdi:history"},
                    {
                        "type": "tile",
                        "entity": entity_ids["last_training_start"],
                        "name": "Letzter Besuch",
                    },
                    {
                        "type": "tile",
                        "entity": entity_ids["last_training_duration"],
                        "name": "Besuchsdauer",
                    },
                    {"type": "tile", "entity": entity_ids["trained_today"], "name": "Heute"},
                    {"type": "tile", "entity": entity_ids["trained_yesterday"], "name": "Gestern"},
                    {
                        "type": "button",
                        "entity": entity_ids["member_refresh"],
                        "name": "Meine Daten aktualisieren",
                    },
                ],
            },
        ]
    )
    return dashboard
