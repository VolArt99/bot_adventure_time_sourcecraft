"""Runtime flags for safe startup behavior in different environments."""

from __future__ import annotations

import os


def should_run_schema_init() -> bool:
    """Return whether `init_db()` should run during process startup.

    In serverless environments frequent cold starts can trigger bursts of
    `CREATE TABLE IF NOT EXISTS`, hitting YDB schema operation limits.
    Control via AUTO_INIT_DB:
      - 1/true/yes/on: always run init_db
      - 0/false/no/off: skip init_db
      - unset: default False in Cloud Functions, True elsewhere
    """
    raw = os.getenv("AUTO_INIT_DB")
    if raw is not None:
        return raw.strip().lower() in {"1", "true", "yes", "on"}

    runs_in_cloud_function = any(
        os.getenv(var_name)
        for var_name in ("FUNCTION_NAME", "FUNCTION_ID", "YC_FUNCTION_NAME", "YC_FUNCTION_ID")
    )
    return not runs_in_cloud_function


def should_run_schema_init_webhook() -> bool:
    """Return whether `init_db()` should run in webhook/serverless handlers.

    Webhook invocations are short-lived and can happen in bursts, so schema
    initialization is disabled by default unless explicitly enabled via
    AUTO_INIT_DB.
    """
    raw = os.getenv("AUTO_INIT_DB")
    if raw is not None:
        return raw.strip().lower() in {"1", "true", "yes", "on"}
    return False