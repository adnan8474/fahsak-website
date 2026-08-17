# Sihtak article authoring spec

Every article is one JSON object. A batch file is a JSON **array** of these
objects written to `content/batches/<batch-id>.json` in UTF-8.

The site is bilingual Arabic/English. Arabic is the primary audience: it is the
default language and lives at `/articles/<slug>/`; English mirrors it at
`/en/articles/<slug>/`. Both versions must carry the same facts, the same
section count and the same FAQ count. Arabic is a real piece of writing for an
Arabic reader, not a translation that reads like one.

## The reader

Someone in Syria, Egypt, Jordan, Iraq, Lebanon, Saudi Arabia, the UAE, Sudan,
Yemen, Morocco, Algeria or the Gulf who has a symptom, a diagnosis, or a lab
report in their hand and wants a plain answer. They may not be able to reach a
doctor quickly. Medicine may be bought over the counter without a prescription.
The nearest lab may be a small private one. Write for that reality, not for a
reader with an NHS appointment next week.

## Object schema

```json
{
  "slug": "kebab-case-english-slug",
  "category": "one of the 12 category ids",
  "chip_ar": "اسم قصير للتصنيف",
  "chip_en": "Short category label",
  "date_iso": "2026-08-17",
  "sources": [
    {"label": "World Health Organization: Diabetes fact sheet", "url": "https://www.who.int/..."}
  ],
  "content": {
    "ar": { "...": "see below" },
    "en": { "...": "see below" }
  }
}
```

`icon`, `date_ar`, `date_en` and `read_min` are derived by the build. Do not
write them.

### Per-language block

```json
{
  "title": "Under 60 characters, the search headline, front-loaded keyword",
  "desc": "150-160 characters. A promise, not a summary of the page furniture.",
  "keywords": "six to ten comma separated phrases a real person would type",
  "h1": "The on-page headline. Close to title but may be longer and warmer.",
  "takeaways": ["3 to 5 one-sentence answers, each standing alone"],
  "sections": [ {"h2": "...", "paras": ["..."], "visual": {...}} ],
  "tie": "One short paragraph connecting to using Sihtak to track this.",
  "faqs": [ {"q": "...", "a": "..."} ]
}
```

### Length and shape

- **7 to 10 sections.** Each section 2 to 4 paragraphs, each paragraph 3 to 6
  sentences. Target 1,600 to 2,400 words per language.
- **6 to 9 FAQs.** Each answer 2 to 4 sentences and genuinely self-contained,
  because these are the answers Google lifts.
- The first section must answer the title question directly. Do not open with
  "In this article we will discuss". Someone who reads only the first
  paragraph should already have the answer.
- Every `h2` should read like something a person would search. "How long does
  it take to work" beats "Duration of therapeutic effect".

## Visuals

At least **3 visuals per article**, spread across different sections, and they
must be different types. A wall of prose does not hold anyone. Attach a visual
to a section with `"visual": {...}`, or several with `"visuals": [{...}]`.

Every visual is optional-titled and may carry `"source"` and `"source_url"`,
which render as a citation line underneath. Cite the source whenever a visual
carries a real statistic.

**Numbers in visuals must be real.** If you do not have a sourced figure, use a
visual type that does not need one (`table`, `steps`, `callout`, `timeline`).
Never invent a prevalence percentage to fill a bar chart.

### `range-scale` — a reference range with the reader's value on it
The single most valuable visual on the site, because "is my number normal" is
the question that brings people here. Use it for any lab test article.
```json
{"type": "range-scale", "title": "Where your result sits", "label": "TSH",
 "unit": "mIU/L", "min": 0, "max": 10,
 "zones": [{"to": 0.4, "tone": "warn", "label": "Low"},
           {"to": 4.0, "tone": "good", "label": "Normal"},
           {"to": 10,  "tone": "bad",  "label": "High"}],
 "marker": {"value": 6.2, "label": "Example result"},
 "source": "NHS reference ranges", "source_url": "https://www.nhs.uk/..."}
```
Zones run left to right and each needs only its upper bound `to`. A zone
narrower than a seventh of the track drops its label automatically, so keep
labels to one or two words. `marker` is optional.

### `bar` — comparison across countries, groups or options
```json
{"type": "bar", "title": "Diabetes prevalence in adults", "unit": "%",
 "items": [{"label": "Egypt", "value": 20.9, "tone": "bad"},
           {"label": "Syria", "value": 12.1}],
 "source": "WHO Global Health Observatory", "source_url": "https://..."}
```
Optional `max` to fix the scale, `display` per item to override the printed
number, `highlight: true` to emphasise one row.

### `donut` — one percentage
```json
{"type": "donut", "value": 72, "label": "of cases are women", "tone": "info"}
```

### `stats` — two to four headline figures
```json
{"type": "stats", "items": [{"value": "1 in 8", "label": "women affected", "tone": "warn"}]}
```

### `timeline` — what happens when
```json
{"type": "timeline", "title": "What happens after an abnormal result",
 "items": [{"when": "Week 0", "what": "Abnormal result found"},
           {"when": "Week 2", "what": "Repeat test to confirm"}]}
```

### `steps` — an ordered how-to. Items are plain strings.
```json
{"type": "steps", "title": "Preparing for the test",
 "items": ["Fast for 8 to 12 hours", "Take the sample in the morning"]}
```

### `table` — structured comparison
```json
{"type": "table", "title": "What each test tells you",
 "head": ["Test", "Normal range", "What a high result suggests"],
 "rows": [["TSH", "0.4 - 4.0 mIU/L", "Underactive thyroid"]]}
```
The first column becomes the row header. Keep to 3 or 4 columns so it survives
a phone screen.

### `callout` — a safety box. Use `tone: "bad"` for red-flag symptoms.
```json
{"type": "callout", "tone": "bad", "title": "Get urgent help if",
 "items": ["Chest pain that does not settle", "Sudden weakness on one side"]}
```
Every article about a condition needs **one red-flag callout**.

Tones everywhere: `good` teal, `warn` amber, `bad` rose, `info` blue,
`neutral` purple.

## Sources

**4 to 7 per article** in the top-level `sources` array. They render as a
citation list and feed the page's structured data. This is the single biggest
lever we have on trust, because the byline is a health software engineer and
not a physician: the authority has to come from what is cited.

Aim for a mix, and **at least two should be primary research** rather than a
fact sheet:

1. **Peer-reviewed studies**, ideally ones run in the region. Name the journal
   and the year, and prefer a real PubMed or DOI landing page:
   `{"label": "Prevalence of vitamin D deficiency among Saudi adults, Saudi Medical Journal, 2023", "url": "https://pubmed.ncbi.nlm.nih.gov/..."}`
   Regional evidence beats a bigger Western study for this audience, because
   sun exposure, diet, consanguinity rates and access to care all differ.
2. **Doctoral theses and university research** from regional institutions
   (Damascus University, Cairo University, the American University of Beirut,
   King Saud University, the University of Jordan, Sudanese and Moroccan
   faculties of medicine). Cite these as
   `"label": "PhD thesis, Faculty of Medicine, Damascus University, 2021"`.
   These are often the only published data that exist for a Syrian or Sudanese
   population, so they are genuinely valuable here, not decoration.
3. **Institutional guidance**: the World Health Organization and its Eastern
   Mediterranean Regional Office, the NHS, the CDC, the International Diabetes
   Federation, national ministries of health.

Where a study is worth quoting, quote it **in the body text too**, not only in
the source list. "A 2023 study of 1,200 adults in Riyadh found that..." is far
more persuasive than an unattributed claim, and it is what a reader deciding
whether to trust the page is looking for. A sourced statistic can also carry
its own visual, with `source` and `source_url` set on that visual.

**Accuracy rule, and it overrides everything above. Look every citation up.**

```
python cite.py search "anaemia prevalence egyptian women" --n 8
```

It returns real PubMed papers with a ready-made `label` and `url`. Copy both
exactly. Never write a PubMed ID from memory: recalled IDs are almost always a
real paper about something else entirely, which is far worse than no citation.
`python validate_batch.py` verifies every one against PubMed and fails the
article if the ID belongs to a different paper or a link 404s.

If a study has no reliable landing page, give the `label` with journal or
institution and year and omit `url`. If you are unsure the study exists at all,
leave it out and write the sentence without a number.

## Voice and safety

- Plain language. Explain a term the first time it appears and then use it.
- **No em-dashes anywhere**, Arabic or English. Use a comma, a full stop, or
  rewrite the sentence.
- Second person. "Your result", "you may notice".
- Never diagnose, never give a specific dose to take, never tell anyone to stop
  a prescribed medicine. Describing how a drug is normally prescribed is fine.
  Telling the reader what to take is not.
- Say when to see a doctor, and be specific about what counts as urgent.
- Be honest about regional constraints: a test may not be available locally, a
  medicine may be sold without a prescription, a result may come from a lab
  with no quality accreditation. Address that rather than pretending otherwise.
- No invented statistics, no invented studies, no invented guidelines. If you
  do not know a number, write the sentence without one.

## Arabic specifics

- Modern Standard Arabic, warm and direct, the register of a good regional
  health broadcaster. Not stiff, not classical.
- Keep the English term in brackets on first mention for anything a reader will
  see printed on a lab report: `الغدة الدرقية (Thyroid)`.
- Lab units and analyte codes stay in Latin script: `TSH`, `mIU/L`, `HbA1c`.
- Arabic-Indic or Western digits are both fine, but be consistent inside one
  article. Western digits are safer inside visuals.
- The Arabic is not a translation. Write it as its own article: the examples,
  the foods, the clinic situations should be ones an Arabic reader recognises.

## Slugs

English, kebab-case, descriptive, no stop words where avoidable, and stable
forever because it becomes the URL. `vitamin-d-deficiency-symptoms` not
`article-about-vitamin-d`. Never reuse a slug already in `content/articles.json`
unless you were explicitly asked to rewrite that article.
