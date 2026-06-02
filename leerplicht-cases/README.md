# Leerplichtwet art. 5 onder b — case scraper & corpus

Dutch case law on exemption from compulsory education based on **objections to
the direction (*richting*) of available education** — Leerplichtwet 1969,
art. 5 aanhef en onder b ("richtingbezwaar").

## Contents

- [`BEVINDINGEN.md`](BEVINDINGEN.md) — **rapport (NL)**: juridisch kader, maximumstraf, de toets bij art. 5 onder b, vrijspraak-vs-veroordeling, straffen in de praktijk, plus: bleven de kinderen van school? en recidive/herhaalde vervolging?
- [`FINDINGS.md`](FINDINGS.md) — **report (EN)**: legal framework, maximum punishment, the art. 5(b) test, acquittal-vs-conviction patterns, and sentences in practice.
- [`index.md`](index.md) — summary index: core arresten + related cases, sorted by date.
- [`cases/`](cases/) — one Markdown file per ECLI (metadata + inhoudsindicatie + full text).
- [`manifest.json`](manifest.json) — machine-readable metadata for every case (no body).
- [`scrape_leerplicht.py`](scrape_leerplicht.py) — the scraper (standard library only).

## How it works

The Rechtspraak open-data search feed (`data.rechtspraak.nl/uitspraken/zoeken`)
**ignores text queries** — it returns the same global set of most-recently
modified ECLI's no matter what you search for, and the website's full-text API
is not reliably reachable from automated clients. So the pipeline is split:

1. **Discovery** — relevant ECLI's are found via web search (the queries are
   recorded in `DISCOVERY_QUERIES` inside the script) and seeded in `SEED_ECLIS`.
2. **Retrieval** — each document's authoritative XML is fetched in parallel from
   the reliable content endpoint `data.rechtspraak.nl/uitspraken/content?id=ECLI:…`,
   with retry/backoff.
3. **Relevance scoring** — each doc is scored on topic terms (richtingbezwaar,
   "5 onder b", overwegende bedenkingen, …). Strong hits land in the core index;
   weaker leerplicht hits are listed separately so nothing is silently dropped.
4. **Output** — structured Markdown per case + an index + a JSON manifest.

## Usage

```bash
# Regenerate the whole corpus into ./leerplicht-cases
python3 leerplicht-cases/scrape_leerplicht.py

# Add extra cases on top of the seed list
python3 leerplicht-cases/scrape_leerplicht.py --ecli ECLI:NL:HR:2003:AJ0497

# Pull additional ECLI's out of any text file (e.g. a notes doc)
python3 leerplicht-cases/scrape_leerplicht.py --seed-file my-notes.md

# Options: -o/--out output dir, --workers N parallel fetchers
```

No third-party dependencies; requires Python 3.9+.

## Source & licence

All content comes from **Rechtspraak open data** (© Rechtspraak / Raad voor de
Rechtspraak). See each case's `source` link for the canonical published version.
