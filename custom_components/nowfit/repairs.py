"""Repair hooks are intentionally reserved for actionable, durable issues.

Authentication recovery is surfaced through Home Assistant's native reauth flow;
transient provider and parser failures do not create repair issues.
"""
