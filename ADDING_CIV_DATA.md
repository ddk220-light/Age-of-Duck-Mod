# Adding New Civ Data to the Overlay

This guide explains how to add new information fields for civilizations in the Age of Duck overlay.

There are two parts: adding the data to `civ_data.json`, and wiring up the display in `src/tooltip.py`.

---

## 1. Add your data to `assets/civ_data.json`

Each civilization is a top-level key in the JSON file. To add a new field, add a new key to every civ object.

**Example** — adding a `"civMatchups"` field:

```json
{
    "Britons": {
        "civName": "Britons",
        "civSummary": "...",
        "civStrength": "...",
        "civWeakness": "...",
        "civStrategy": "...",
        "civTeamBonus": "...",
        "civMatchups": "Your new data goes here as a string.",
        "unitsAvailable": { ... },
        "unique_units_by_category": { ... }
    }
}
```

**Rules:**
- The key name must be the same across all civs (e.g. `"civMatchups"` everywhere).
- The value should be a plain string. Use `\n\n` for paragraph breaks and `\n` for line breaks — the display renders these as-is in a text box.
- Add the field to **every** civ entry, even if the value is empty (`""`), to avoid missing-key errors.

---

## 2. Wire up the display in `src/tooltip.py`

All civ info sections are rendered inside the `CivTooltip` class using the same repeating pattern: a `CollapsibleSection` (the expandable header) containing a `QTextEdit` (the text body). Follow these steps:

### Step A — Declare the section and text widget (~line 270)

Find the block where existing sections are created:

```python
self.section_bonuses    = CollapsibleSection("Civilization Bonuses")
self.section_strengths  = CollapsibleSection("Strengths")
self.section_weaknesses = CollapsibleSection("Weaknesses")
self.section_strategies = CollapsibleSection("Strategies")
self.section_units      = CollapsibleSection("Counter Unit Guide")
```

Add your new section. The string is the header label the user sees:

```python
self.section_matchups   = CollapsibleSection("Matchups")
```

### Step B — Add it to the layout (~line 275)

Find where sections are added to `self.layout`:

```python
self.layout.addWidget(self.section_bonuses)
self.layout.addWidget(self.section_strengths)
self.layout.addWidget(self.section_weaknesses)
self.layout.addWidget(self.section_strategies)
self.layout.addWidget(self.section_units)
```

Insert your section wherever you want it to appear in the UI order:

```python
self.layout.addWidget(self.section_matchups)
```

### Step C — Create the text widget (~line 280)

Find the block where text widgets are created:

```python
self.text_bonuses     = QTextEdit(); self.text_bonuses.setReadOnly(True)
self.text_strength    = QTextEdit(); self.text_strength.setReadOnly(True)
self.text_weaknesses  = QTextEdit(); self.text_weaknesses.setReadOnly(True)
self.text_strategies  = QTextEdit(); self.text_strategies.setReadOnly(True)
```

Add yours:

```python
self.text_matchups    = QTextEdit(); self.text_matchups.setReadOnly(True)
```

### Step D — Register it for minimum height styling (~line 284)

Add your text widget to the tuple that sets `setMinimumHeight`:

```python
for t in (self.text_bonuses, self.text_strength, self.text_weaknesses,
          self.text_strategies, self.text_matchups):
    t.setMinimumHeight(self._s(self._BASE_TEXT_MIN_H))
```

### Step E — Attach the text widget to its section (~line 286)

Find the `setContentWidget` calls:

```python
self.section_bonuses.setContentWidget(self.text_bonuses)
self.section_strengths.setContentWidget(self.text_strength)
self.section_weaknesses.setContentWidget(self.text_weaknesses)
self.section_strategies.setContentWidget(self.text_strategies)
```

Add yours:

```python
self.section_matchups.setContentWidget(self.text_matchups)
```

### Step F — Register for padding/spacing and collapse signals (~line 292)

Add your section to the loop that sets content margins and spacing:

```python
for sec in (self.section_strengths, self.section_weaknesses,
            self.section_strategies, self.section_units, self.section_matchups):
```

And the collapse/toggle signal connections (~line 300):

```python
for sec in (self.section_bonuses, self.section_strengths, self.section_weaknesses,
            self.section_strategies, self.section_units, self.section_matchups):
    sec.collapsed.connect(self.on_section_collapsed)
    sec.toggled.connect(self.on_section_collapsed)
```

### Step G — Hide it initially (~line 296)

Add it to the initial-hide block:

```python
for w in (self.label_icon, self.label_name, self.label_team_bonus,
          self.section_bonuses, self.section_strengths, self.section_weaknesses,
          self.section_strategies, self.section_units, self.section_matchups):
    w.hide()
```

### Step H — Populate it when a civ is selected (~line 697)

In the `on_civ_changed_waiting()` method, find where existing text is set:

```python
self.text_weaknesses.setPlainText(civ.get("civWeakness", "No weakness info available."))
self.text_strategies.setPlainText(civ.get("civStrategy", "No strategy info available."))
```

Add your field, using the same JSON key you added in step 1:

```python
self.text_matchups.setPlainText(civ.get("civMatchups", "No matchup info available."))
```

### Step I — Clear it on reset (~line 666)

In the same method, find where text widgets are cleared when "Select a civ" is chosen:

```python
self.text_bonuses.clear()
self.text_strength.clear()
self.text_weaknesses.clear()
self.text_strategies.clear()
```

Add:

```python
self.text_matchups.clear()
```

### Step J — Show it when a civ is selected (~line 693)

Add it to the tuple that shows widgets:

```python
for w in (self.label_name, self.label_team_bonus,
          self.section_bonuses, self.section_strengths, self.section_weaknesses,
          self.section_strategies, self.section_units, self.section_matchups):
    w.show()
```

### Step K — Add to scaling methods

In `set_scale()` (~line 460), add your text widget to the styling loop:

```python
for t in (self.text_bonuses, self.text_strength, self.text_weaknesses,
          self.text_strategies, self.text_matchups):
```

And add the section to the margins/header-scale loop (~line 473):

```python
for sec in (self.section_bonuses, self.section_strengths, self.section_weaknesses,
            self.section_strategies, self.section_units, self.section_matchups):
```

Do the same in `set_font_size()` (~line 773):

```python
for t in (self.text_bonuses, self.text_strength, self.text_weaknesses,
          self.text_strategies, self.text_matchups):
```

---

## Quick reference: existing fields

| JSON key | Display section | Notes |
|---|---|---|
| `civName` | Header label | Displayed next to civ icon |
| `civTeamBonus` | Team Bonus label | Shown below the header |
| `civStrength` | "Civilization Bonuses" + "Strengths" | Split on first `\n\n` — first chunk = bonuses, rest = strengths |
| `civWeakness` | "Weaknesses" | Displayed as-is |
| `civStrategy` | "Strategies" | Displayed as-is |
| `unitsAvailable` | "Counter Unit Guide" | Dict of category -> unit -> bool |
| `unique_units_by_category` | "Counter Unit Guide" | Dict of category -> list of unit names |

---

## Summary checklist

1. Add your new key (e.g. `"civMatchups"`) to every civ in `assets/civ_data.json`
2. In `src/tooltip.py`, touch these 11 locations:
   - **A** — Create `CollapsibleSection`
   - **B** — Add to `self.layout`
   - **C** — Create `QTextEdit`
   - **D** — Add to min-height loop
   - **E** — `setContentWidget`
   - **F** — Add to padding/spacing and signal loops
   - **G** — Add to initial-hide block
   - **H** — `setPlainText` in `on_civ_changed_waiting()`
   - **I** — `.clear()` on reset
   - **J** — `.show()` when civ selected
   - **K** — Add to `set_scale()` and `set_font_size()` loops
