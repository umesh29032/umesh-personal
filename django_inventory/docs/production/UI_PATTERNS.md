# UI Patterns — Production Tracking Templates

Reference for **every new HTML template** in `raw_materials/`, `production/`, `tracking/`. Anchored to project memories: `feedback_html_standards`, `feedback_ui_polish`, `feedback_form_inputs`, `project_form_shell`.

## Mobile responsiveness (non-negotiable)

- Every `<td>` has `data-label="Column Name"` — `accounts/base.html` global CSS auto-stacks them as label:value cards at ≤600px.
- Actions column `<td>` uses `class="td-actions"` → full-width button row on mobile.
- Multi-column form grids use page-scoped class with `@media (max-width: 768px) { grid-template-columns: 1fr }`.
- Filter rows: `flex-wrap: nowrap; overflow-x: auto` — single-row horizontal scroll on phones.
- Hero strips collapse to single column on ≤600px.
- Sticky actions stack column-reverse + full-width buttons on mobile.

## Form shell pattern (mandatory for all create/edit pages)

`include 'production/_form_styles.html'` in `extra_head`. Wrap content in `.form-shell`.

```django
{% extends "accounts/base.html" %}
{% block extra_head %}{% include 'production/_form_styles.html' %}{% endblock %}
{% block content %}
<div class="form-shell">
    <div class="hero">
        <h1>Page Title</h1>
        <p>Short subtitle.</p>
        <span class="hero-chip">CONTEXT TAG</span>
    </div>

    <form method="post" novalidate>
        {% csrf_token %}
        {% if form.non_field_errors %}<div class="form-error">{{ form.non_field_errors|join:" " }}</div>{% endif %}

        <div class="panel">
            <div class="panel-head"><div class="panel-num">01</div><div class="panel-title">Section Name</div></div>
            <div class="panel-body">
                <div class="form-grid">
                    <div class="field"><label>Name *</label>{{ form.name }}{% if form.name.errors %}<div class="field-error">{{ form.name.errors|join:" " }}</div>{% endif %}</div>
                    <div class="field full"><label>Notes</label>{{ form.notes }}</div>
                </div>
            </div>
        </div>

        <div class="sticky-actions">
            <a href="{% url 'app:list' %}" class="btn btn-ghost">Cancel</a>
            <button type="submit" class="btn btn-primary">Save</button>
        </div>
    </form>
</div>
{% endblock %}
```

Components:
- **Hero**: hardcoded dark gradient (`linear-gradient(135deg, #0a1628 0%, #1a2840 50%, #2a1f0e 85%, #b87333 130%)`). Never use CSS vars in hero — they flip in dark mode.
- **Panel**: copper-square numbered badge (`.panel-num` 01, 02, 03…) + Cormorant Garamond title.
- **Inputs**: cream bg + 1.5px solid `#cfc0aa` border + `inset 0 1.5px 4px rgba(14,11,9,0.07)` shadow. Copper focus glow.
- **Sticky actions**: `position: sticky; bottom: 14px` + frosted glass (`backdrop-filter: blur(16px)`).

## Filter bar pattern (list + dashboard pages)

Single-row scroll, never wraps:

```html
<form method="get" class="filter-card">
    <div class="field">
        <label>Status</label>
        <select name="status" data-no-fancy>...</select>
    </div>
    <div class="field"><label>&nbsp;</label><button type="submit" class="btn btn-primary">Apply</button></div>
    <div class="field"><label>&nbsp;</label><a href="{% url 'reset_url' %}" class="btn btn-ghost">Reset</a></div>
</form>
```

CSS pattern: `display:flex; gap:12px; align-items:end; flex-wrap:nowrap; overflow-x:auto`. Each child `flex-shrink:0`.

## Active-filter chips strip (roll-list shows this)

When any filter is applied, render summary strip below filter card with per-chip remove URLs.

View pattern:
```python
def _build_remove_url(self, key_to_remove):
    params = self.request.GET.copy()
    if key_to_remove in params:
        del params[key_to_remove]
    if 'page' in params:
        del params['page']
    qs = params.urlencode()
    return self.request.path + (('?' + qs) if qs else '')

# In get_context_data:
chips = []
if status:
    chips.append({'group': 'Status', 'label': label,
                  'remove_url': self._build_remove_url('status')})
ctx['active_filter_chips'] = chips
ctx['filtered_count'] = self.get_queryset().count() if chips else 0
```

Template:
```django
{% if active_filter_chips %}
<div class="filter-info">
    <span class="lbl">Active:</span>
    {% for chip in active_filter_chips %}
        <span class="chip">
            <span class="group">{{ chip.group }}</span>
            {{ chip.label }}
            <a href="{{ chip.remove_url }}" class="x" title="Remove this filter">✕</a>
        </span>
    {% endfor %}
    <span class="count">· <strong>{{ filtered_count }}</strong> row{{ filtered_count|pluralize }} match</span>
    <a href="{% url 'reset_url' %}" class="clear-all">Clear all ×</a>
</div>
{% endif %}
```

Clicking `✕` on a chip removes only that filter — keeps the others intact.

## Time-log accordion (collapsible — `<details>/<summary>`)

Native HTML5, no JS. Shared partials in `templates/inventory/`.

Include in `extra_head`:
```django
{% include 'inventory/_time_log_styles.html' %}
```

Render in `content`:
```django
{# Cloth-roll movements: needs `roll_events` context var (ClothRollHistory queryset) #}
{% include 'inventory/_roll_events_accordion.html' %}

{# Adda lifecycle: needs `adda_events` context var (AddaHistory queryset) #}
{% include 'inventory/_adda_events_accordion.html' %}
```

View must populate context:
```python
from tracking.models import ClothRollHistory  # lazy import in view
ctx['roll_events'] = (
    ClothRollHistory.objects
    .select_related('roll', 'roll__cloth_type', 'roll__cloth_color', 'actor')
    .order_by('-created_at')[:30]
)
# OR for Adda:
from tracking.models import AddaHistory
ctx['adda_events'] = (
    AddaHistory.objects
    .select_related('adda', 'adda__product', 'stage_from', 'stage_to', 'roll', 'actor')
    .order_by('-created_at')[:30]
)
```

**Where applied:**
- `/raw-materials/` → roll events
- `/raw-materials/cloth/` → roll events
- `/raw-materials/rolls/` → roll events (50 latest)
- `/production/` → adda events
- `/tracking/` → adda events (barcodes flow through Adda lifecycle)

Visual: closed by default; click summary → expand; chevron `▾` rotates 180° + copper color when open.

## Worker checkbox grid widget

`production/forms/_shared.py` defines `_WorkerCheckboxes` extending `CheckboxSelectMultiple` with custom template `production/_workers_widget.html`. Renders as chip-style grid (one per worker), copper-tinted on `:has(input:checked)`. Friendlier than Ctrl+click `SelectMultiple` default.

Used by `StartLayeringForm` (in `forms/layering.py`) + `CuttingForm` (in `forms/cutting.py`).

## QR print sheet (`barcode_print_sheet.html`)

Standalone HTML (does NOT extend `accounts/base.html`). A4-anchored grid. ECC level Q (25% damage tolerance).

3 density modes via `?size=`:

| Mode | QR size | Grid | Per A4 |
|---|---|---|---|
| small (default) | 22mm | 6×9 | **54** |
| medium | 30mm | 5×7 | 35 |
| large | 42mm | 4×6 | 24 |

`?status=pending|packed|dispatched|missing` filters before printing (reprint flow). *(R0 note 2026-06-10: the `missing` filter is currently inert end-to-end — `mark_status` has no UI caller, so nothing can be marked missing yet; see SYSTEM_DESIGN scan-flow correction.)*

Toolbar sticky-top + hidden in `@media print`. Mobile preview stacks toolbar + lets QR images scale to viewport (mm-anchored for actual paper print).

## Single CSS source rule

- All shared classes live in `accounts/base.html`. NEVER duplicate.
- Page-specific CSS goes in `{% block extra_head %}` scoped under a page class (`.cloth-dash`, `.roll-list`, `.adda-detail`, `.bulk-roll-create`) so it can't leak.
- New shared partials go under `config/templates/inventory/_*.html`.

## Hinglish comment rule

Every template + Python file must have Hinglish `{# ... #}` / `# ... ` / docstring comments. Match the existing project style (see `config/config/settings/base.py` "YEH FILE KYU HAI?" pattern).

Focus on **Django primitive** being used:
- ✓ `{# `rolls` queryset — data-label attr har <td> pe, mobile pe stack ho ke card banta hai #}`
- ✓ `# select_for_update() = Postgres row-level lock — race-safe`
- ✗ Long English explanations of obvious things

## Shared partials inventory

```
config/templates/inventory/
  _time_log_styles.html              ← accordion + time-log CSS (include in extra_head)
  _roll_events_accordion.html        ← cloth-roll movements timeline
  _adda_events_accordion.html        ← adda lifecycle timeline

config/production/templates/production/
  _form_styles.html                  ← form-shell CSS (include in extra_head)
  _workers_widget.html               ← worker checkbox grid render
```

## Status badge patterns

Use base.html's `.badge-active` / `.badge-inactive` (auto-flip in dark mode) by default. For other statuses, inline-style with `var(--*-bg)` + `var(--*)` tokens:

```html
<span class="badge badge-active">● Available</span>
<span class="badge badge-inactive">Used</span>
<span class="badge" style="padding:2px 8px; border-radius:10px; font-size:11px;
                          background:var(--info-bg); color:var(--info);">In Progress</span>
```

## Empty states

Use base.html's `.empty-state`:

```html
<div class="empty-state">
    <h3>No rolls yet</h3>
    <p>Bulk add rolls to get started.</p>
</div>
```
