"""Matchup advisor integration — wraps aoe2-unit-analyzer's best_units module."""

import os
import traceback

_MATCHUP_DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "assets", "matchup_data")
_DB_PATH = os.path.join(_MATCHUP_DATA_DIR, "aoe2_reference.db")
_POWER_UNITS_PATH = os.path.join(_MATCHUP_DATA_DIR, "civ_power_units.json")

MATCHUP_AVAILABLE = os.path.exists(_DB_PATH) and os.path.exists(_POWER_UNITS_PATH)

if not MATCHUP_AVAILABLE:
    print("[matchup] WARNING: Database files not found. Matchup advisor will be disabled.")

# Civ names that differ between Age of Duck (civ_data.json) and the analyzer
_CIV_NAME_MAP = {
    "Inca": "Incas",
    "Maya": "Mayans",
}


def _to_analyzer_name(civ_name: str) -> str:
    """Map an Age of Duck civ name to the analyzer's expected name."""
    return _CIV_NAME_MAP.get(civ_name, civ_name)


def get_matchup_text(my_civ: str, opponent_civs: list[str], age: str = "imperial") -> str:
    """Return formatted matchup advice text for my_civ vs each opponent civ.

    Returns a human-readable string ready for display in a QTextEdit.
    On any failure, returns a user-friendly fallback message.
    """
    if not MATCHUP_AVAILABLE:
        return "Matchup advisor unavailable (database files missing)."

    try:
        from matchup.best_units import get_matchup_recommendations
    except ImportError:
        return "Matchup advisor unavailable (module not found)."

    my_civ_mapped = _to_analyzer_name(my_civ)
    lines = []

    for opp_civ in opponent_civs:
        opp_mapped = _to_analyzer_name(opp_civ)
        try:
            recs = get_matchup_recommendations(my_civ_mapped, opp_mapped, age)
            comps = recs.get("recommended_compositions", [])
            if not comps:
                lines.append(f"vs {opp_civ}:")
                lines.append("  No recommendations available.")
                lines.append("")
                continue

            lines.append(f"vs {opp_civ}:")
            for i, comp in enumerate(comps[:2]):
                label = "Best" if i == 0 else "Alt"
                gold_unit = comp.get("gold_unit", {})
                trash_unit = comp.get("trash_unit", {})
                gold_name = _slug_to_name(gold_unit.get("unit_slug", ""))
                trash_name = _slug_to_name(trash_unit.get("unit_slug", "")) if trash_unit else None
                reasoning = comp.get("reasoning", "")

                if trash_name:
                    lines.append(f"  {label}: {gold_name} + {trash_name}")
                else:
                    lines.append(f"  {label}: {gold_name}")
                if reasoning:
                    lines.append(f"    {reasoning}")
            lines.append("")

        except Exception:
            traceback.print_exc()
            lines.append(f"vs {opp_civ}:")
            lines.append(f"  No matchup data available for {opp_civ}.")
            lines.append("")

    return "\n".join(lines).strip() if lines else "No matchup data available."


def _slug_to_name(slug: str) -> str:
    """Convert a unit slug like 'camel_rider' to 'Camel Rider'."""
    if not slug:
        return "Unknown"
    return slug.replace("_", " ").title()
