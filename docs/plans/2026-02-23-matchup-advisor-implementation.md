# Matchup Advisor Integration — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** When a live AoE2 match is detected, automatically show recommended unit compositions for the player's civ vs each opponent's civ in a new overlay section.

**Architecture:** Copy `best_units.py` and `simulation.py` from the aoe2-unit-analyzer repo into `src/matchup/`, along with their pre-computed databases into `assets/matchup_data/`. Patch database paths. Add a "Matchup Advisor" collapsible section to `tooltip.py`. Call the analyzer from `update_overlay()` in `AgeofDuck.py`.

**Tech Stack:** Python 3, PyQt5, sqlite3 (stdlib), json (stdlib)

---

### Task 1: Download and place analyzer files

**Files:**
- Create: `src/matchup/__init__.py`
- Create: `src/matchup/best_units.py` (from repo)
- Create: `src/matchup/simulation.py` (from repo)
- Create: `assets/matchup_data/` directory (with `aoe2_reference.db` and `civ_power_units.json`)

**Step 1: Create directories**

```bash
mkdir -p src/matchup
mkdir -p assets/matchup_data
```

**Step 2: Download files from the aoe2-unit-analyzer repository**

Download these 4 files from `https://github.com/ddk220-light/aoe2-unit-analyzer`:
- `webapp/best_units.py` → save to `src/matchup/best_units.py`
- `webapp/simulation.py` → save to `src/matchup/simulation.py`
- `webapp/aoe2_reference.db` → save to `assets/matchup_data/aoe2_reference.db`
- `webapp/civ_power_units.json` → save to `assets/matchup_data/civ_power_units.json`

```bash
# Clone temporarily, copy needed files, clean up
git clone --depth 1 https://github.com/ddk220-light/aoe2-unit-analyzer.git /tmp/aoe2-analyzer
cp /tmp/aoe2-analyzer/webapp/best_units.py src/matchup/best_units.py
cp /tmp/aoe2-analyzer/webapp/simulation.py src/matchup/simulation.py
cp /tmp/aoe2-analyzer/webapp/aoe2_reference.db assets/matchup_data/aoe2_reference.db
cp /tmp/aoe2-analyzer/webapp/civ_power_units.json assets/matchup_data/civ_power_units.json
rm -rf /tmp/aoe2-analyzer
```

**Step 3: Create `src/matchup/__init__.py`**

```python
# Matchup advisor integration — wraps aoe2-unit-analyzer's best_units module.
```

**Step 4: Verify files exist**

```bash
ls -la src/matchup/
ls -la assets/matchup_data/
```

Expected: `best_units.py`, `simulation.py`, `__init__.py` in `src/matchup/`; `aoe2_reference.db`, `civ_power_units.json` in `assets/matchup_data/`.

**Step 5: Commit**

```bash
git add src/matchup/ assets/matchup_data/
git commit -m "feat: add matchup advisor analyzer files and databases"
```

---

### Task 2: Patch database paths in best_units.py

**Files:**
- Modify: `src/matchup/best_units.py` (path constants near top of file)

**Context:** `best_units.py` has hardcoded paths using `os.path.dirname(__file__)` which assumes the database files are in the same directory. We need to redirect them to `assets/matchup_data/`.

**Step 1: Find and replace path constants**

In `src/matchup/best_units.py`, find the lines that define `DB_PATH` and `POWER_UNITS_PATH` (they look like):

```python
DB_PATH = os.path.join(os.path.dirname(__file__), "aoe2_reference.db")
POWER_UNITS_PATH = os.path.join(os.path.dirname(__file__), "civ_power_units.json")
```

Replace with:

```python
_MATCHUP_DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "assets", "matchup_data")
DB_PATH = os.path.join(_MATCHUP_DATA_DIR, "aoe2_reference.db")
POWER_UNITS_PATH = os.path.join(_MATCHUP_DATA_DIR, "civ_power_units.json")
```

This navigates from `src/matchup/` up to the project root, then into `assets/matchup_data/`.

**Step 2: Verify the import works**

```bash
cd src && python -c "from matchup.best_units import load_civ_power_units; data = load_civ_power_units(); print('OK' if data else 'FAIL')"
```

Expected: `OK`

**Step 3: Commit**

```bash
git add src/matchup/best_units.py
git commit -m "fix: patch matchup advisor database paths to assets/matchup_data/"
```

---

### Task 3: Add civ name mapping module

**Files:**
- Modify: `src/matchup/__init__.py`

**Step 1: Write the mapping and wrapper function**

Replace contents of `src/matchup/__init__.py` with:

```python
"""Matchup advisor integration — wraps aoe2-unit-analyzer's best_units module."""

import traceback

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
```

**Step 2: Verify the wrapper works**

```bash
cd src && python -c "
from matchup import get_matchup_text
result = get_matchup_text('Britons', ['Mongols', 'Franks'])
print(result)
"
```

Expected: Formatted text with `vs Mongols:` and `vs Franks:` sections, each with Best/Alt compositions.

**Step 3: Commit**

```bash
git add src/matchup/__init__.py
git commit -m "feat: add matchup advisor wrapper with civ name mapping"
```

---

### Task 4: Add Matchup Advisor section to tooltip.py

**Files:**
- Modify: `src/tooltip.py` (11 locations per ADDING_CIV_DATA.md pattern)

This task follows the ADDING_CIV_DATA.md guide exactly. The key difference is that this section's text is set externally via `set_matchup_text()` rather than from `civ_data.json`.

**Step 1: Declare the section and text widget (~line 273)**

After the existing section declarations, add:

```python
self.section_matchups   = CollapsibleSection("Matchup Advisor")
```

Insert after line 273 (`self.section_strategies = CollapsibleSection("Strategies")`), before line 274 (`self.section_units`).

**Step 2: Add to layout (~line 278)**

Insert between `self.layout.addWidget(self.section_strategies)` and `self.layout.addWidget(self.section_units)`:

```python
self.layout.addWidget(self.section_matchups)
```

**Step 3: Create the text widget (~line 283)**

After the existing text widget declarations, add:

```python
self.text_matchups    = QTextEdit(); self.text_matchups.setReadOnly(True)
```

**Step 4: Register for minimum height styling (~line 284)**

Change the existing loop from:

```python
for t in (self.text_bonuses, self.text_strength, self.text_weaknesses, self.text_strategies):
    t.setMinimumHeight(self._s(self._BASE_TEXT_MIN_H))
```

To:

```python
for t in (self.text_bonuses, self.text_strength, self.text_weaknesses, self.text_strategies, self.text_matchups):
    t.setMinimumHeight(self._s(self._BASE_TEXT_MIN_H))
```

**Step 5: Attach text widget to section (~line 289)**

After `self.section_strategies.setContentWidget(self.text_strategies)`, add:

```python
self.section_matchups.setContentWidget(self.text_matchups)
```

**Step 6: Register for padding/spacing (~line 292)**

Change:

```python
for sec in (self.section_strengths, self.section_weaknesses, self.section_strategies, self.section_units):
```

To:

```python
for sec in (self.section_strengths, self.section_weaknesses, self.section_strategies, self.section_matchups, self.section_units):
```

**Step 7: Add to initial-hide block (~line 296)**

Change:

```python
for w in (self.label_icon, self.label_name, self.label_team_bonus,
      self.section_bonuses, self.section_strengths, self.section_weaknesses,
      self.section_strategies, self.section_units):
    w.hide()
```

To:

```python
for w in (self.label_icon, self.label_name, self.label_team_bonus,
      self.section_bonuses, self.section_strengths, self.section_weaknesses,
      self.section_strategies, self.section_matchups, self.section_units):
    w.hide()
```

**Step 8: Register collapse/toggle signals (~line 300)**

Change:

```python
for sec in (self.section_bonuses, self.section_strengths, self.section_weaknesses,
    self.section_strategies, self.section_units):
    sec.collapsed.connect(self.on_section_collapsed)
    sec.toggled.connect(self.on_section_collapsed)
```

To:

```python
for sec in (self.section_bonuses, self.section_strengths, self.section_weaknesses,
    self.section_strategies, self.section_matchups, self.section_units):
    sec.collapsed.connect(self.on_section_collapsed)
    sec.toggled.connect(self.on_section_collapsed)
```

**Step 9: Clear on reset — in `on_civ_changed_waiting()` (~line 666)**

After `self.text_strategies.clear()`, add:

```python
self.text_matchups.clear()
```

**Step 10: Show when civ selected — in `on_civ_changed_waiting()` (~line 693)**

Change:

```python
for w in (self.label_name, self.label_team_bonus,
      self.section_bonuses, self.section_strengths, self.section_weaknesses,
      self.section_strategies, self.section_units):
    w.show()
```

To:

```python
for w in (self.label_name, self.label_team_bonus,
      self.section_bonuses, self.section_strengths, self.section_weaknesses,
      self.section_strategies, self.section_matchups, self.section_units):
    w.show()
```

**Step 11: Hide when civ deselected — in `on_civ_changed_waiting()` (~line 662)**

Change:

```python
for w in (self.label_icon, self.label_name, self.label_team_bonus,
      self.section_bonuses, self.section_strengths, self.section_weaknesses,
      self.section_strategies, self.section_units):
    w.hide()
```

To:

```python
for w in (self.label_icon, self.label_name, self.label_team_bonus,
      self.section_bonuses, self.section_strengths, self.section_weaknesses,
      self.section_strategies, self.section_matchups, self.section_units):
    w.hide()
```

**Step 12: Add to `set_scale()` text styling loop (~line 460)**

Change:

```python
for t in (self.text_bonuses, self.text_strength, self.text_weaknesses, self.text_strategies):
```

To:

```python
for t in (self.text_bonuses, self.text_strength, self.text_weaknesses, self.text_strategies, self.text_matchups):
```

**Step 13: Add to `set_scale()` section margins/header loop (~line 473)**

Change:

```python
for sec in (self.section_bonuses, self.section_strengths, self.section_weaknesses,
    self.section_strategies, self.section_units):
```

To:

```python
for sec in (self.section_bonuses, self.section_strengths, self.section_weaknesses,
    self.section_strategies, self.section_matchups, self.section_units):
```

**Step 14: Add to `set_font_size()` loop (~line 773)**

Change:

```python
for t in (self.text_bonuses, self.text_strength, self.text_weaknesses, self.text_strategies):
```

To:

```python
for t in (self.text_bonuses, self.text_strength, self.text_weaknesses, self.text_strategies, self.text_matchups):
```

**Step 15: Add `set_matchup_text()` method**

Add this new method to the `CivTooltip` class (after `set_game_state()`, before `set_font_size()`):

```python
def set_matchup_text(self, text: str):
    """Set the matchup advisor section text. Called from update_overlay()."""
    self.text_matchups.setPlainText(text)
```

**Step 16: Commit**

```bash
git add src/tooltip.py
git commit -m "feat: add Matchup Advisor collapsible section to civ tooltip"
```

---

### Task 5: Wire up matchup computation in AgeofDuck.py

**Files:**
- Modify: `src/AgeofDuck.py:897-931` (`update_overlay` method)

**Step 1: Add matchup import at top of file**

Near the existing imports at the top of `AgeofDuck.py` (after line 21, `from tooltip import CivTooltip`), add:

```python
    from matchup import get_matchup_text
```

Note: This is inside the `if sys.platform == "win32":` block, same as the other imports.

**Step 2: Identify opponent civs and compute matchups in `update_overlay()`**

In the `update_overlay()` method, after line 916 (`self.civ_tooltip.current_profile_civ = None`), before line 917 (`prev_selected = ...`), add the matchup computation block:

```python
        # --- Matchup Advisor ---
        if current_civ:
            my_team = None
            for p in players:
                if p.get("profile_id") == int(self.worker.profile_id):
                    my_team = p.get("team")
                    break
            opponent_civs = []
            for p in players:
                opp_civ = p.get("civ", "")
                if opp_civ and p.get("team") != my_team:
                    opponent_civs.append(opp_civ)
            # Deduplicate while preserving order
            seen = set()
            unique_opponents = []
            for c in opponent_civs:
                if c not in seen:
                    seen.add(c)
                    unique_opponents.append(c)
            try:
                matchup_text = get_matchup_text(current_civ, unique_opponents)
                self.civ_tooltip.set_matchup_text(matchup_text)
            except Exception as e:
                print(f"Matchup advisor error: {e}")
                self.civ_tooltip.set_matchup_text("Matchup advisor encountered an error.")
        else:
            self.civ_tooltip.set_matchup_text("Join a game to see matchup advice.")
```

**Step 3: Verify the app starts without errors**

```bash
cd src && python AgeofDuck.py
```

Expected: App launches normally. When a live game is detected with a set profile ID, the Matchup Advisor section in the civ tooltip should show recommendations.

**Step 4: Commit**

```bash
git add src/AgeofDuck.py
git commit -m "feat: compute and display matchup advice when a live match is detected"
```

---

### Task 6: Handle missing database files gracefully

**Files:**
- Modify: `src/matchup/__init__.py` (add startup check)

**Step 1: Add database availability check**

At the top of `src/matchup/__init__.py`, after the imports, add:

```python
import os

_MATCHUP_DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "assets", "matchup_data")
_DB_PATH = os.path.join(_MATCHUP_DATA_DIR, "aoe2_reference.db")
_POWER_UNITS_PATH = os.path.join(_MATCHUP_DATA_DIR, "civ_power_units.json")

MATCHUP_AVAILABLE = os.path.exists(_DB_PATH) and os.path.exists(_POWER_UNITS_PATH)

if not MATCHUP_AVAILABLE:
    print(f"[matchup] WARNING: Database files not found. Expected:")
    print(f"  {_DB_PATH}")
    print(f"  {_POWER_UNITS_PATH}")
    print(f"  Matchup advisor will be disabled.")
```

**Step 2: Guard `get_matchup_text()` with availability check**

At the start of the `get_matchup_text()` function, add:

```python
    if not MATCHUP_AVAILABLE:
        return "Matchup advisor unavailable (database files missing)."
```

**Step 3: Optionally hide the section when unavailable**

In `src/tooltip.py`, in the `CivTooltip.__init__()` method, after creating `self.section_matchups`, add a check:

```python
try:
    from matchup import MATCHUP_AVAILABLE
    self._matchup_available = MATCHUP_AVAILABLE
except ImportError:
    self._matchup_available = False
```

Then in the show-widgets tuples (Steps 10/11 from Task 4), the section only shows if `self._matchup_available` is True. Modify `set_matchup_text()`:

```python
def set_matchup_text(self, text: str):
    """Set the matchup advisor section text. Called from update_overlay()."""
    if not getattr(self, '_matchup_available', False):
        self.section_matchups.hide()
        return
    self.text_matchups.setPlainText(text)
```

**Step 4: Commit**

```bash
git add src/matchup/__init__.py src/tooltip.py
git commit -m "fix: gracefully handle missing matchup advisor database files"
```

---

### Task 7: End-to-end manual test

**Files:** None (testing only)

**Step 1: Verify app launches**

```bash
cd src && python AgeofDuck.py
```

Expected: App starts, tray icon appears, no errors in console about matchup module.

**Step 2: Test with a live game**

1. Launch AoE2 DE and join a game (or use a test profile ID that has a live match)
2. Verify the overlay shows player ELOs as before
3. Click the civ dropdown — select your civ
4. Expand "Matchup Advisor" section
5. Verify it shows "vs [OpponentCiv]:" with Best/Alt compositions

**Step 3: Test edge cases**

- Select "Select a civ" — matchup section should hide
- Test when not in a game — section should show "Join a game to see matchup advice"
- If database files are missing, section should hide entirely

**Step 4: Final commit (if any fixes needed)**

```bash
git add -A
git commit -m "fix: address issues found during manual testing"
```
