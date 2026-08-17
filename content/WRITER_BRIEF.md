# Writer brief

You are writing health education articles for Sihtak (www.sihtak.com), a
bilingual Arabic/English consumer health site for the Middle East. This is real
content that will be published under a named byline. Accuracy matters more than
speed.

Working directory: `C:\Users\user\OneDrive\Desktop\fahsak-website`

## Do this in order

1. **Read `content/SPEC.md` in full.** It is the contract: exact JSON schema,
   all 9 visual types with their exact key names, sourcing rules, voice rules.

2. **Read your assigned topics** from `content/topics.json`. You will be told
   which slugs are yours. Each topic gives you:
   - `slug` : the exact slug to use. Do not change it. It becomes the URL.
   - `cat`  : the exact category id to use.
   - `en`   : the intended English angle for the title. You may refine wording.
   - `angle`: editorial direction. Follow it. It encodes why the topic earns
     traffic and what the competing pages get wrong.

3. **Absorb the house voice.** In `content/articles.json`, read the object with
   slug `thyroid-tsh-guide`, both `content.ar` and `content.en`. Match that tone
   and that Arabic register. Important: the existing articles are shorter and
   have no visuals and no sources. They are a voice reference, not a length or
   quality reference. You must exceed them on all three counts.

4. **Look up your citations BEFORE you write.** This is not optional and it is
   the step writers skip. See "Citations" below.

5. **Write ONE FILE PER ARTICLE**, as a single JSON object (not an array), to
   `content/batches/<slug>.json`. Use the Write tool, UTF-8.

   This one-file-per-article rule is not stylistic. A single response cannot
   exceed 32,000 output tokens, and two bilingual articles in one Write call
   will exceed it and lose all your work. Write each article in its own call.

6. **Validate and fix until clean.** With the Bash tool:
   ```
   cd C:/Users/user/OneDrive/Desktop/fahsak-website && python validate_batch.py content/batches/<slug>.json
   ```
   It checks section counts, body word counts, FAQ counts, visual counts, that
   every visual actually renders, em-dashes, Arabic/English script mixing, and
   it verifies every citation against PubMed. Keep fixing and re-running until
   it reports **0 errors**. Fix the warnings you reasonably can.

## Citations: look them up, never recall them

**You cannot remember PubMed IDs correctly.** This has been measured on this
project: of 12 PubMed IDs written from memory by a careful writer, 9 pointed at
a completely unrelated paper. A citation for "the definition of anaemia" landed
on a study of VEGF blockade in mice. Three hand-written NHS and WHO URLs were
404s. The validator now checks every one of these against the live PubMed API,
so recalled citations will simply fail you.

Use the lookup tool. It queries PubMed and hands you back real papers:

```
cd C:/Users/user/OneDrive/Desktop/fahsak-website && python cite.py search "vitamin d deficiency saudi arabia prevalence" --n 8
```

Every hit comes with a ready-made `label` line and a `url`. **Copy those two
values exactly.** Do not retype the title, do not tidy the author list, do not
guess a PMID you think you remember.

Search once per major claim, with the regional term in the query
(`"brucellosis raw milk jordan"`, `"anaemia prevalence egyptian women"`). Prefer
what comes back from a region-specific query, because regional evidence is worth
more to this reader than a larger Western study.

For non-PubMed sources (WHO, NHS, CDC, IDF, a ministry of health), **WebFetch
the URL to confirm it resolves** before you cite it, or give the `label` with no
`url` at all. The validator flags 404s.

For a thesis or a print journal with no reliable landing page, give the `label`
with institution and year and omit `url` entirely. That is a good citation, not
a weak one.

If a search returns nothing useful for a claim, write the sentence without the
number. That is always the right call.

## Where writers fail

**No em-dashes or en-dashes.** Anywhere, Arabic or English, in any field. The
site owner rejects them on sight. Use a comma, a full stop, or rewrite. The
validator fails you on these.

**Sources must be real.** 4 to 7 per article, and at least two should be primary
research: a named peer-reviewed study with journal and year, or a doctoral
thesis from a regional university. Get them from `cite.py search`, as above.

**Quote the research in the body, not only in the source list.** "A 2019 study
of 500 adults in Amman found that..." is what persuades a reader to trust the
page. An unattributed claim does not.

**At least 3 visuals per language per article**, of at least two different
types, spread across different sections. A lab test article needs a
`range-scale`. A condition article needs a red-flag `callout` with tone `bad`.
Numbers inside visuals must be real and sourced, so if you do not have a sourced
figure, choose a visual type that does not need one (`table`, `steps`,
`callout`, `timeline`).

**The Arabic is not a translation.** Write it as its own article for an Arabic
reader: its own examples, foods and clinic situations. Same facts, same section
count, same FAQ count as the English. Keep lab abbreviations and units in Latin
script (`TSH`, `mIU/L`, `HbA1c`), and put the English term in brackets on first
mention of anything printed on a lab report.

**Length.** 7 to 10 sections, 1,600 to 2,400 words per language. The validator
counts **body paragraphs only**: headings, takeaways and FAQ text do not count
towards it, so an article that looks long because of its furniture will still
fail. It hard-fails under 1,100 words of English prose (950 Arabic) and warns
under 1,500 (1,300 Arabic). These pages need to be the best answer on the
internet for their query in Arabic, because that is the entire commercial point
of the site.

**Safety.** Never diagnose. Never give the reader a specific dose to take. Never
tell anyone to stop a prescribed medicine. Describing how a drug is normally
prescribed is fine. Be specific about what counts as urgent and when to go to
hospital rather than wait.

**Dates.** Set `date_iso` to a date between `2026-06-20` and `2026-08-16`, and
vary it across your articles so the site does not look published in one burst.

You may use WebSearch and WebFetch to verify prevalence figures and to confirm a
study exists before citing it. Do this for any statistic you plan to put in a
visual.

## Your reply

One line only: how many articles you wrote, and the validator's final error and
warning count. Do not summarise the articles. Do not paste any article content.
