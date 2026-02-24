# Matchup Advisor Integration Design

## Overview

Integrate the aoe2-unit-analyzer's matchup-advisor feature into Age of Duck so that when a live match is detected, the overlay automatically shows recommended unit compositions for the player's civ vs each opponent's civ.

## Architecture

### Approach: Synchronous on-match-detect

When `update_overlay()` fires with a new match, call `get_matchup_recommendations(my_civ, opponent_civ, "imperial")` for each opponent civ. Format the results as text and display in a new collapsible section. No background threads or pre-computation needed — the function reads pre-computed JSON/SQLite data and completes in <100ms per opponent.

### File Structure

```
Age-of-Duck-Mod/
├── src/
│   ├── AgeofDuck.py          (modified)
│   ├── tooltip.py            (modified)
│   ├── matchup/              (NEW)
│   │   ├── __init__.py
│   │   ├── best_units.py     (from aoe2-unit-analyzer/webapp/)
│   │   └── simulation.py     (from aoe2-unit-analyzer/webapp/)
├── assets/
│   ├── matchup_data/         (NEW)
│   │   ├── aoe2_reference.db (~8.3MB)
│   │   └── civ_power_units.json (~1.1MB)
```

### Dependencies

No new pip dependencies. `best_units.py` and `simulation.py` use only Python stdlib (`json`, `os`, `sqlite3`, `random`).

## Data Flow

1. Match detected → `fetch_all_players_elos()` returns player list
2. `update_overlay()` identifies:
   - `my_civ = get_civ_for_profile_id(match, profile_id)` (existing)
   - `opponent_civs = [p["civ"] for p in players if p on different team]` (new)
3. For each opponent_civ, apply civ name mapping then call:
   - `recs = get_matchup_recommendations(my_civ, opponent_civ, "imperial")`
4. Format results as readable text
5. Set text on the new "Matchup Advisor" collapsible section via `civ_tooltip.set_matchup_text(text)`

### Civ Name Mapping

Two civ names differ between Age of Duck and the analyzer:

| Age of Duck | Analyzer |
|---|---|
| `Inca` | `Incas` |
| `Maya` | `Mayans` |

A mapping dict normalizes names before calling the analyzer.

## UI Design

New "Matchup Advisor" collapsible section in the civ tooltip, placed between "Strategies" and "Counter Unit Guide". Follows the existing `ADDING_CIV_DATA.md` widget pattern.

### Display Format

```
▶ Matchup Advisor
  vs Mongols:
    Best: Arbalester + Light Cavalry
      → Arbalester outranges Mangudai; Skirm covers weakness
    Alt: Pikeman + Skirmisher
      → Pikeman counters cavalry threat

  vs Franks:
    Best: Camel Rider + Spearman
      → Camel Rider dominates Knight line
```

### Key difference from existing sections

Existing sections read static per-civ data from `civ_data.json`. The Matchup Advisor section is computed dynamically per-match (depends on both player civ and opponent civs). Text is set from `AgeofDuck.py` via a new `set_matchup_text()` method rather than from `on_civ_changed()`.

## Error Handling

1. **Unrecognized civ**: Show "No matchup data available for [civ]"
2. **Missing database files**: Log warning at startup, hide section entirely
3. **No profile civ detected** (spectating): Show "Join a game to see matchup advice"
4. **Mirror matchups**: Still shown (valid analysis)
5. **Computation failure**: Catch exceptions, show fallback text, don't crash overlay

## What This Does NOT Change

- No changes to `civ_data.json`
- No changes to the existing Counter Unit Guide
- No new threads or async patterns
- No new pip dependencies
- No changes to the AoE2 Companion API integration
