"""Print exports that can verify a provisional fit."""

import json

from . import db

PROVENANCE = ", confirmed by a printed fit test"


def is_coupon(part):
    return part["name"].endswith("_fit_test")


def default_values(run, values):
    defaults = {param["name"]: param["default"] for param in json.loads(run["params"])}
    return all(name in defaults and defaults[name] == value for name, value in values.items())


def basis(part, run, measurements, names):
    """The measured values a successful, unmodified coupon build can confirm."""
    if (
        not is_coupon(part) or not names or run is None or run["status"] != "ok"
        or run["revision_id"] != part["current_revision_id"]
        or not default_values(run, json.loads(run["overrides"]))
    ):
        return None
    rows = {row["name"]: row for row in measurements}
    values = {}
    for name in names:
        row = rows.get(name)
        if row is None or row["unit"] != "mm" or row["value_changed_at"] > run["started_at"]:
            return None
        values[name] = [row["value"], row["value_changed_at"]]
    return values


def export_id(part, run, measurements, names):
    if run is None or not run["fit_export"]:
        return None
    saved = json.loads(run["fit_export"])
    if saved and saved["values"] == basis(part, run, measurements, names):
        return saved["id"]
    return None


def confirm(conn, project_id, measurements, names):
    with db.transaction(conn):
        for row in measurements:
            if row["name"] in names and row["provisional"]:
                prior = row["how"].removesuffix(PROVENANCE).removesuffix(", not printed yet")
                how = prior + PROVENANCE
                db.set_measurement(conn, project_id, row["name"], row["value"], how)
