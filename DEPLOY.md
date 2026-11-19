# Deploying sihtak.com

Azure Static Web App `fahsak-website` in resource group `fahsak-rg`, serving
sihtak.com and www.sihtak.com. **The GitHub Action does not fire.** Every
deploy is manual.

## Before you deploy

```
python build_covers.py       # only when covers-src/ has new masters
python build_content.py && python build_site.py && python build_tools.py && python build_about.py
python seo_audit.py          # must exit 0
git commit -am "..."         # the deploy ships committed code only
```

`build_covers.py` turns a master render in `covers-src/<slug>.jpg` into the
article hero and the two titled share cards, and records the alt text in
`content/covers.json`. The masters are gitignored and never ship; the three
derivatives under `images/articles/` do. Run it before the other builders,
because they read that manifest to decide which articles have a cover.

`build_og.py` writes `og-image.png`, the fallback social card for every page
without a cover of its own. It is not part of the per-build chain; run it when
the branding, the tagline or the app screenshots change. Like the share cards
it draws its text in Chromium, because Arabic needs bidi ordering and
contextual shaping and nothing else here does both.

`seo_audit.py` exits non-zero on blocker-level findings. It walks the working
tree but skips anything gitignored, so what it audits is what ships.

## Bump ASSET_V when shared CSS or JS changes

`staticwebapp.config.json` caches `*.css` and `*.js` for seven days. Every page
links them with `?v=<ASSET_V>`, declared once in `build_chrome.py`. Change
`style.css`, `articles/article.css`, `tools/tools.css` or `articles/hub.js`
without bumping `ASSET_V` and returning readers keep last week's file for a
week. The hand-written pages carry the stamp too, so re-stamp them when it
changes.

## Building the artifact

Deploy `git archive HEAD`, then strip what is source rather than site. 110M
becomes about 25M.

Strip these:

- `deck/` (71M) and `content/` (15M)
- the builders and dev tooling: `build_about.py`, `build_chrome.py`,
  `build_content.py`, `build_covers.py`, `build_home.py`, `build_og.py`, `build_site.py`, `build_tools.py`,
  `build_visuals.py`, `cite.py`, `merge_batches.py`, `validate_batch.py`,
  `add-analytics.py`, `verify-analytics.js`, `seo_audit.py`
- `email-signature.html`, `email-signature-ar.html` (email templates, not pages)
- `DEPLOY.md`

**Keep `screenshots/`.** It looks like a dev folder and is not: `index.html`
serves `/screenshots/ai-chat.png`, `/screenshots/dashboard.png` and
`/screenshots/voice-chat.png` from it. Grep the artifact for a folder's name
before deleting it.

`fahsak-com/` and `fahsak-co-uk/` are separate sites that happen to live in
this directory. They are gitignored, so `git archive` already excludes them.

## Shipping it

Run from an empty directory, not the repo, or the CLI uploads the repo:

```powershell
$TOK = az staticwebapp secrets list -n fahsak-website -g fahsak-rg --query "properties.apiKey" -o tsv
swa deploy ./site --env production --deployment-token "$TOK" --no-use-keychain
```

## Verifying

Never trust the deploy log. Fetch the live page and grep the served bytes for
something only the new build contains, and check the response size so an error
page cannot pass as a success.
