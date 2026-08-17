#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sihtak article visual system.

Renders the "visual" object attached to any article section into semantic
HTML. Deliberately HTML/CSS rather than SVG for everything except the donut
ring, because:
  - RTL flips for free, so the Arabic pages are correct with no extra work
  - the numbers stay as real selectable text, so Google indexes them
  - screen readers get a table or a list instead of an opaque graphic
  - no JS, no extra requests, and dark mode follows the CSS variables

Visual types
------------
range-scale : coloured reference-range bar, for lab values
bar         : horizontal comparison bars, for prevalence and survey data
donut       : one headline percentage as a ring
stats       : a row of big numbers
timeline    : ordered when/what rows, for schedules and disease course
steps       : numbered process
table       : comparison table with a stacked mobile fallback
callout     : red-flag / warning / tip box
figure      : self-hosted image with caption and credit

Every type accepts an optional "source" (and "source_url") which renders as a
citation line under the visual. Health content without provenance is worthless,
so this is surfaced rather than hidden.
"""
import html

TONES = {
    "good": "good", "normal": "good", "teal": "good",
    "warn": "warn", "warning": "warn", "amber": "warn", "caution": "warn",
    "bad": "bad", "danger": "bad", "high": "bad", "rose": "bad",
    "info": "info", "blue": "info",
    "neutral": "neutral", "purple": "neutral",
}

L = {
    "ar": {
        "source": "المصدر",
        "figure": "شكل",
        "chart_alt": "رسم بياني",
        "low": "منخفض", "normal": "طبيعي", "high": "مرتفع",
        "your_value": "قيمتك",
        "swipe": "مرّر أفقياً لعرض الجدول كاملاً",
    },
    "en": {
        "source": "Source",
        "figure": "Figure",
        "chart_alt": "Chart",
        "low": "Low", "normal": "Normal", "high": "High",
        "your_value": "Your value",
        "swipe": "Scroll sideways to see the full table",
    },
}


def e(s, quote=False):
    return html.escape(str(s), quote=quote)


def tone_of(v):
    return TONES.get(str(v or "neutral").lower(), "neutral")


def _source(lang, v):
    src = v.get("source")
    if not src:
        return ""
    url = v.get("source_url")
    label = e(src)
    inner = (f'<a href="{e(url, True)}" target="_blank" rel="noopener nofollow">{label}</a>'
             if url else label)
    return f'        <p class="viz-source">{L[lang]["source"]}: {inner}</p>\n'


def _caption(v):
    cap = v.get("caption")
    return f'        <p class="viz-caption">{e(cap)}</p>\n' if cap else ""


def _title(v):
    t = v.get("title")
    return f'        <h3 class="viz-title">{e(t)}</h3>\n' if t else ""


def _wrap(lang, v, inner, extra_class=""):
    cls = f"viz viz--{v['type']}" + (f" {extra_class}" if extra_class else "")
    return (f'      <figure class="{cls} reveal">\n'
            + _title(v) + inner + _caption(v) + _source(lang, v)
            + '      </figure>\n')


# --------------------------------------------------------------------------
# range-scale: the reference-range bar. The single most useful visual we have,
# because "is my number normal" is the query that brings people here.
# --------------------------------------------------------------------------
def render_range_scale(lang, v):
    lo = float(v["min"])
    hi = float(v["max"])
    span = hi - lo or 1.0
    zones = v["zones"]
    unit = v.get("unit", "")

    segs, labels = [], []
    prev = lo
    for z in zones:
        top = float(z["to"])
        pct = max((top - prev) / span * 100.0, 0.0)
        tone = tone_of(z.get("tone"))
        zl = str(z.get("label", ""))
        # A label wider than its zone renders as "L…". Below roughly a seventh of
        # the track there is no room for text, so the zone keeps the name only
        # for assistive tech and the axis ticks carry the boundary.
        if zl and pct >= 14.0:
            body = f'<span class="viz-zone-label">{e(zl)}</span>'
        else:
            body = ""
        aria = f' aria-label="{e(zl, True)}"' if zl and not body else ""
        segs.append(
            f'            <div class="viz-zone viz-zone--{tone}" style="flex:0 0 {pct:.4f}%"{aria}>'
            f'{body}</div>\n'
        )
        # boundary tick, skipped for the final upper bound which is open-ended
        if top < hi:
            at = (top - lo) / span * 100.0
            labels.append(
                f'            <span class="viz-tick" style="inset-inline-start:{at:.4f}%">'
                f'{e(_num(top))}</span>\n'
            )
        prev = top

    marker = ""
    mk = v.get("marker")
    if mk is not None:
        # Authors write either `"marker": 6.2` or `{"value": 6.2, "label": "..."}`.
        mk = mk if isinstance(mk, dict) else {"value": mk}
        m = float(mk["value"])
        at = min(max((m - lo) / span * 100.0, 0.0), 100.0)
        flag = mk.get("label") or L[lang]["your_value"]
        # A flag centred on the marker hangs off the figure when the value sits
        # near either end of the scale, which is exactly where an interesting
        # result sits. Near an edge it hangs inward from the line instead.
        edge = (" viz-marker--start" if at < 15
                else " viz-marker--end" if at > 85 else "")
        marker = (
            f'            <div class="viz-marker{edge}" style="inset-inline-start:{at:.4f}%">\n'
            f'              <span class="viz-marker-flag">{e(flag)} {e(_num(m))}</span>\n'
            '            </div>\n'
        )

    unit_html = f'<span class="viz-unit">{e(unit)}</span>' if unit else ""
    label = v.get("label") or v.get("analyte") or ""
    inner = (
        '        <div class="viz-range">\n'
        f'          <div class="viz-range-head"><span class="viz-range-label">{e(label)}</span>{unit_html}</div>\n'
        '          <div class="viz-range-track">\n'
        + "".join(segs)
        + marker
        + '          </div>\n'
        '          <div class="viz-range-axis">\n'
        f'            <span class="viz-tick viz-tick--start">{e(_num(lo))}</span>\n'
        + "".join(labels)
        + f'            <span class="viz-tick viz-tick--end">{e(_num(hi))}</span>\n'
        '          </div>\n'
        '        </div>\n'
    )
    return _wrap(lang, v, inner)


def _num(x):
    f = float(x)
    return str(int(f)) if f == int(f) else (f"{f:g}")


# --------------------------------------------------------------------------
# bar: horizontal comparison. Values are normalised against the largest item
# unless an explicit max is given.
# --------------------------------------------------------------------------
def render_bar(lang, v):
    items = v["items"]
    unit = v.get("unit", "")
    top = float(v.get("max") or max(float(i["value"]) for i in items) or 1.0)
    rows = []
    for i in items:
        val = float(i["value"])
        pct = min(val / top * 100.0, 100.0) if top else 0.0
        tone = tone_of(i.get("tone") or v.get("tone") or "good")
        hl = " viz-bar-row--hl" if i.get("highlight") else ""
        rows.append(
            f'            <div class="viz-bar-row{hl}">\n'
            f'              <span class="viz-bar-label">{e(i["label"])}</span>\n'
            '              <span class="viz-bar-track">\n'
            f'                <span class="viz-bar-fill viz-bar-fill--{tone}" style="width:{pct:.3f}%"></span>\n'
            '              </span>\n'
            f'              <span class="viz-bar-value">{e(i.get("display") or _num(val))}{e(unit)}</span>\n'
            '            </div>\n'
        )
    inner = '        <div class="viz-bars">\n' + "".join(rows) + '        </div>\n'
    return _wrap(lang, v, inner)


# --------------------------------------------------------------------------
# donut: one number, as a ring. SVG here because a ring cannot be done cleanly
# in CSS without conic-gradient colour-stop rounding artefacts.
# --------------------------------------------------------------------------
def render_donut(lang, v):
    pct = max(0.0, min(float(v["value"]), 100.0))
    tone = tone_of(v.get("tone") or "good")
    r = 52.0
    circ = 2 * 3.141592653589793 * r
    dash = circ * pct / 100.0
    label = v.get("label", "")
    inner = (
        '        <div class="viz-donut">\n'
        f'          <svg viewBox="0 0 128 128" width="128" height="128" role="img" aria-label="{e(str(pct), True)}%">\n'
        f'            <circle class="viz-donut-bg" cx="64" cy="64" r="{r}" fill="none" stroke-width="13"/>\n'
        f'            <circle class="viz-donut-fg viz-donut-fg--{tone}" cx="64" cy="64" r="{r}" fill="none" stroke-width="13"\n'
        f'              stroke-linecap="round" stroke-dasharray="{dash:.2f} {circ - dash:.2f}" transform="rotate(-90 64 64)"/>\n'
        '          </svg>\n'
        '          <div class="viz-donut-text">\n'
        f'            <strong>{e(v.get("display") or (_num(pct) + "%"))}</strong>\n'
        '          </div>\n'
        '        </div>\n'
        # The caption sits under the ring, not inside it: the hole is about 90px
        # across and any real sentence overlaps the stroke.
        + (f'        <p class="viz-donut-cap">{e(label)}</p>\n' if label else "")
    )
    return _wrap(lang, v, inner)


# --------------------------------------------------------------------------
def render_stats(lang, v):
    cells = "".join(
        f'          <div class="viz-stat viz-stat--{tone_of(i.get("tone") or "good")}">\n'
        f'            <strong>{e(i["value"])}</strong>\n'
        f'            <span>{e(i["label"])}</span>\n'
        '          </div>\n'
        for i in v["items"]
    )
    return _wrap(lang, v, '        <div class="viz-stats">\n' + cells + '        </div>\n')


def render_timeline(lang, v):
    rows = "".join(
        f'          <li class="viz-tl-item viz-tl-item--{tone_of(i.get("tone") or "good")}">\n'
        f'            <span class="viz-tl-when">{e(i["when"])}</span>\n'
        f'            <span class="viz-tl-what">{e(i["what"])}</span>\n'
        '          </li>\n'
        for i in v["items"]
    )
    return _wrap(lang, v, '        <ol class="viz-timeline">\n' + rows + '        </ol>\n')


def render_steps(lang, v):
    rows = "".join(
        f'          <li><span class="viz-step-n">{n}</span><span class="viz-step-t">{e(i)}</span></li>\n'
        for n, i in enumerate(v["items"], 1)
    )
    return _wrap(lang, v, '        <ol class="viz-steps">\n' + rows + '        </ol>\n')


def render_table(lang, v):
    head = v["head"]
    ths = "".join(f'              <th scope="col">{e(h)}</th>\n' for h in head)
    trs = []
    for row in v["rows"]:
        tds = [f'              <th scope="row">{e(row[0])}</th>\n']
        for ci, cell in enumerate(row[1:], 1):
            lbl = e(head[ci], True) if ci < len(head) else ""
            tds.append(f'              <td data-label="{lbl}">{e(cell)}</td>\n')
        trs.append('            <tr>\n' + "".join(tds) + '            </tr>\n')
    inner = (
        '        <div class="viz-table-wrap" tabindex="0" role="region">\n'
        '          <table class="viz-table">\n'
        '            <thead>\n            <tr>\n' + ths + '            </tr>\n            </thead>\n'
        '            <tbody>\n' + "".join(trs) + '            </tbody>\n'
        '          </table>\n'
        '        </div>\n'
    )
    return _wrap(lang, v, inner)


def render_callout(lang, v):
    tone = tone_of(v.get("tone") or "danger")
    icons = {
        "bad": '<path d="M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>',
        "warn": '<circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>',
        "good": '<path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/>',
        "info": '<circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/>',
        "neutral": '<circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/>',
    }
    body = ""
    if v.get("items"):
        body += ('          <ul>\n'
                 + "".join(f'            <li>{e(i)}</li>\n' for i in v["items"])
                 + '          </ul>\n')
    if v.get("text"):
        body += f'          <p>{e(v["text"])}</p>\n'
    return (
        f'      <aside class="viz-callout viz-callout--{tone} reveal" role="note">\n'
        '        <div class="viz-callout-icon" aria-hidden="true">\n'
        f'          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">{icons.get(tone, icons["info"])}</svg>\n'
        '        </div>\n'
        '        <div class="viz-callout-body">\n'
        + (f'          <h3>{e(v["title"])}</h3>\n' if v.get("title") else "")
        + body
        + '        </div>\n'
        '      </aside>\n'
    )


def render_figure(lang, v):
    credit = ""
    if v.get("credit"):
        c = e(v["credit"])
        credit = (f'<a href="{e(v["credit_url"], True)}" target="_blank" rel="noopener nofollow">{c}</a>'
                  if v.get("credit_url") else c)
        credit = f'        <p class="viz-credit">{credit}</p>\n'
    w = v.get("width", 1200)
    h = v.get("height", 675)
    inner = (
        f'        <img src="{e(v["src"], True)}" alt="{e(v.get("alt", ""), True)}" '
        f'width="{w}" height="{h}" loading="lazy" decoding="async" class="viz-img">\n'
    )
    return _wrap(lang, v, inner + credit)


RENDERERS = {
    "range-scale": render_range_scale,
    "bar": render_bar,
    "donut": render_donut,
    "stats": render_stats,
    "timeline": render_timeline,
    "steps": render_steps,
    "table": render_table,
    "callout": render_callout,
    "figure": render_figure,
}


# Aliases. Content is authored by many hands across 150 articles, so accept the
# obvious synonyms rather than silently dropping a chart over a key name.
_TOP_ALIASES = {
    "head": ("head", "columns", "headers"),
    "items": ("items", "rows", "data", "bars", "points"),
    "value": ("value", "percent", "pct"),
}
_ITEM_ALIASES = {
    "when": ("when", "time", "date", "stage", "day"),
    "what": ("what", "text", "desc", "description", "detail"),
    "label": ("label", "name", "title"),
    "value": ("value", "amount", "percent", "pct", "number"),
}


def _pick(d, names):
    for n in names:
        if d.get(n) is not None:
            return d[n]
    return None


def _normalise(v):
    v = dict(v)
    t = v.get("type")
    if t == "table":
        # 'rows' means the body here, so resolve the header before touching items
        head = _pick(v, _TOP_ALIASES["head"])
        if head is not None:
            v["head"] = head
        return v
    if t == "donut" and v.get("value") is None:
        got = _pick(v, _TOP_ALIASES["value"])
        if got is not None:
            v["value"] = got
    if v.get("items") is None:
        got = _pick(v, _TOP_ALIASES["items"])
        if got is not None:
            v["items"] = got
    items = v.get("items")
    if isinstance(items, list) and t in ("timeline", "stats", "bar", "steps"):
        out = []
        for it in items:
            if not isinstance(it, dict):
                # steps take bare strings; the others need a label to render
                out.append(it if t == "steps" else {"label": str(it), "value": 0})
                continue
            it = dict(it)
            for key, names in _ITEM_ALIASES.items():
                if it.get(key) is None:
                    got = _pick(it, names)
                    if got is not None:
                        it[key] = got
            if t == "steps":
                # a step is one string; join an authored {title, text} pair
                parts = [str(it.get("label") or ""), str(it.get("what") or "")]
                out.append(": ".join(p for p in parts if p) or str(it))
            else:
                out.append(it)
        v["items"] = out
    return v


def render(lang, v):
    """Render one visual. Unknown types are dropped rather than crashing the
    build, because a bad visual must never cost us the whole article."""
    if not v or not isinstance(v, dict):
        return ""
    fn = RENDERERS.get(v.get("type"))
    if not fn:
        return ""
    try:
        return fn(lang, _normalise(v))
    except Exception as exc:  # noqa: BLE001 - build must survive bad data
        print(f"    ! visual skipped ({v.get('type')}): {exc}")
        return ""


def render_all(lang, section):
    """A section may carry one 'visual' or a list under 'visuals'."""
    out = []
    if section.get("visual"):
        out.append(render(lang, section["visual"]))
    for v in section.get("visuals") or []:
        out.append(render(lang, v))
    return "".join(out)
