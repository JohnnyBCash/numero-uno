#!/usr/bin/env python3
"""Scrape Dutch case law on Leerplichtwet art. 5 onder b (richtingbezwaar).

Why this exists
---------------
The Rechtspraak open-data feed at ``data.rechtspraak.nl/uitspraken/zoeken``
deliberately does NOT support full-text search: it returns the same global set
of most-recently-modified ECLI's regardless of any query parameter you pass.
The modern website full-text API (``uitspraken.rechtspraak.nl/api/zoek``) is not
reliably reachable from automated clients.

So discovery and retrieval are split into two stages:

  1. DISCOVERY  -- a curated seed list of ECLI's found via web search for the
                   topic "leerplichtwet artikel 5 onder b / richtingbezwaar".
                   Extra ECLI's can be supplied with --ecli or --seed-file.
  2. RETRIEVAL  -- the authoritative per-document XML is fetched in parallel
                   from the open-data content endpoint, which IS reliable:
                   ``data.rechtspraak.nl/uitspraken/content?id=ECLI:...``

Each document is parsed, relevance-scored against the topic, rendered to a
structured Markdown file, and an index + JSON manifest are written.

Pure standard library -- no third-party dependencies.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field, asdict
from pathlib import Path

CONTENT_URL = "https://data.rechtspraak.nl/uitspraken/content?id="
DEEPLINK = "https://uitspraken.rechtspraak.nl/details?id="
USER_AGENT = (
    "leerplicht-case-scraper/1.0 (legal research; "
    "open data via data.rechtspraak.nl)"
)

# --- Stage 1: discovery seeds -------------------------------------------------
# ECLI's surfaced by web search for the topic. Mixed instances (Hoge Raad,
# its Parket/PHR conclusies, gerechtshoven, rechtbanken) so the corpus shows
# the full doctrinal chain on art. 5 onder b. Relevance is verified per-doc in
# stage 2; off-topic hits are kept out of the core index automatically.
SEED_ECLIS = [
    "ECLI:NL:HR:2003:AF1264",
    "ECLI:NL:HR:2010:BL6719",
    "ECLI:NL:PHR:2012:BV9201",
    "ECLI:NL:GHSHE:2012:BW4064",
    "ECLI:NL:RBBRE:2010:BL7280",
    "ECLI:NL:RBAMS:2011:BU8403",
    "ECLI:NL:RBSHE:2011:BP2276",
    "ECLI:NL:GHARL:2015:5814",
    "ECLI:NL:RBGEL:2017:1420",
    "ECLI:NL:HR:2018:1071",
    "ECLI:NL:GHAMS:2018:1564",
    "ECLI:NL:HR:2019:960",
    "ECLI:NL:PHR:2020:219",
    "ECLI:NL:GHAMS:2020:1670",
    "ECLI:NL:GHDHA:2021:505",
    "ECLI:NL:HR:2022:1004",
    "ECLI:NL:PHR:2022:506",
    "ECLI:NL:RBMNE:2022:750",
    "ECLI:NL:RBROT:2022:8514",
    "ECLI:NL:RBROT:2022:8517",
    "ECLI:NL:GHARL:2024:2205",
    "ECLI:NL:GHAMS:2024:2924",
    "ECLI:NL:HR:2026:659",
]

# Web-search queries used to assemble the seed list above (recorded for
# reproducibility; see module docstring for why we cannot query the API).
DISCOVERY_QUERIES = [
    'leerplichtwet "5 onder b" richtingbezwaar vrijstelling',
    "leerplicht richtingbezwaar Hoge Raad overwegende bedenkingen",
    "leerplichtwet artikel 5 onder b kennisgeving veroordeling ouders",
]

# --- Relevance scoring --------------------------------------------------------
# (compiled pattern, weight, label). A document needs at least one STRONG hit
# (weight >= 3) to be treated as a core art. 5-onder-b case.
SCORE_TERMS = [
    (re.compile(r"richtingbezwa(?:ar|ren)", re.I), 3, "richtingbezwaar"),
    (re.compile(r"\b5[,\s]+(?:aanhef en )?onder\s+b\b", re.I), 3, "5 onder b"),
    (re.compile(r"overwegende bedenkingen", re.I), 2, "overwegende bedenkingen"),
    (re.compile(r"richting van het onderwijs", re.I), 2, "richting van het onderwijs"),
    (re.compile(r"\bleerplicht", re.I), 1, "leerplicht"),
    (re.compile(r"vrijstelling", re.I), 1, "vrijstelling"),
]
STRONG_THRESHOLD = 3

# Rechtspraak content schema uses a default namespace; tags are matched by
# their local name throughout, so namespaces are simply stripped.
DCTERMS = "{http://purl.org/dc/terms/}"
PSI = "{http://psi.rechtspraak.nl/}"

INLINE_BLOCKS = {"para", "bridgehead", "nr", "title"}
HEADING_BLOCKS = {"bridgehead", "title"}


@dataclass
class Case:
    ecli: str
    title: str = ""
    court: str = ""
    date: str = ""          # uitspraakdatum
    published: str = ""     # publicatiedatum
    zaaknummer: str = ""
    procedure: str = ""
    rechtsgebied: str = ""
    place: str = ""
    inhoudsindicatie: str = ""
    body_md: str = ""
    vindplaatsen: list = field(default_factory=list)
    score: int = 0
    matched_terms: list = field(default_factory=list)
    has_body: bool = False
    deeplink: str = ""


def fetch(url: str, retries: int = 4, timeout: int = 30) -> bytes:
    """GET with exponential backoff (2s, 4s, 8s, 16s) on transient errors."""
    last = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.read()
        except (urllib.error.URLError, TimeoutError) as exc:  # network/timeout
            last = exc
            if attempt < retries - 1:
                time.sleep(2 ** (attempt + 1))
    raise RuntimeError(f"fetch failed after {retries} attempts: {url} ({last})")


def localname(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def norm(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def render_block(el: ET.Element, depth: int = 0) -> list[str]:
    """Recursively render a rechtspraak body element to Markdown blocks."""
    tag = localname(el.tag)
    blocks: list[str] = []

    if tag in INLINE_BLOCKS:
        text = norm("".join(el.itertext()))
        if not text:
            return []
        if tag in HEADING_BLOCKS:
            return [f"### {text}"]
        return [text]

    if tag == "title":  # (already handled above, kept for clarity)
        return [f"## {norm(''.join(el.itertext()))}"]

    if tag == "section":
        nr = el.findtext("{*}nr") or ""
        # A section's own title is rendered as a heading; remaining children recurse.
        title_el = el.find("{*}title")
        if title_el is not None:
            htext = norm(f"{nr} {''.join(title_el.itertext())}")
            if htext:
                blocks.append(f"## {htext}")
        for child in el:
            if child is title_el or localname(child.tag) == "nr":
                continue
            blocks.extend(render_block(child, depth + 1))
        return blocks

    if tag == "list":
        for item in el:
            for j, b in enumerate(render_block(item, depth + 1)):
                blocks.append(("- " + b) if j == 0 else ("  " + b))
        return blocks

    # Generic container (parablock, uitspraak.info, item, footnote, table, ...).
    direct = norm(el.text or "")
    if direct:
        blocks.append(direct)
    for child in el:
        blocks.extend(render_block(child, depth + 1))
    return blocks


def parse_case(ecli: str, raw: bytes) -> Case:
    case = Case(ecli=ecli, deeplink=DEEPLINK + ecli)
    root = ET.fromstring(raw)

    # Metadata lives in the rdf:Description whose dcterms:identifier is the ECLI.
    for desc in root.iter("{http://www.w3.org/1999/02/22-rdf-syntax-ns#}Description"):
        ident = desc.findtext(f"{DCTERMS}identifier") or ""
        if not ident.startswith("ECLI"):
            continue
        case.court = norm(desc.findtext(f"{DCTERMS}creator") or "")
        case.date = norm(desc.findtext(f"{DCTERMS}date") or "")
        case.published = norm(desc.findtext(f"{DCTERMS}issued") or "")
        case.zaaknummer = norm(desc.findtext(f"{PSI}zaaknummer") or "")
        case.procedure = norm(desc.findtext(f"{PSI}procedure") or "")
        case.rechtsgebied = norm(desc.findtext(f"{DCTERMS}subject") or "")
        case.place = norm(desc.findtext(f"{DCTERMS}spatial") or "")
        version = desc.find(f"{DCTERMS}hasVersion")
        if version is not None:
            case.vindplaatsen = [norm(li.text or "") for li in version.iter()
                                 if localname(li.tag) == "li" and norm(li.text or "")]
        break

    # Human-readable title is on the deeplink Description.
    for desc in root.iter("{http://www.w3.org/1999/02/22-rdf-syntax-ns#}Description"):
        t = desc.findtext(f"{DCTERMS}title")
        if t:
            case.title = norm(t)
            break
    if not case.title:
        case.title = f"{ecli}, {case.court}"

    inh = next((e for e in root.iter() if localname(e.tag) == "inhoudsindicatie"), None)
    if inh is not None:
        case.inhoudsindicatie = "\n\n".join(
            b for b in render_block(inh) if b
        ).strip()

    body = next((e for e in root.iter()
                 if localname(e.tag) in ("uitspraak", "conclusie")), None)
    if body is not None:
        blocks = render_block(body)
        case.body_md = "\n\n".join(b for b in blocks if b).strip()
        case.has_body = bool(case.body_md)

    haystack = f"{case.inhoudsindicatie}\n{case.body_md}".lower()
    score = 0
    matched = []
    for pat, weight, label in SCORE_TERMS:
        if pat.search(haystack):
            score += weight
            matched.append(label)
    case.score = score
    case.matched_terms = matched
    return case


def case_filename(ecli: str) -> str:
    return ecli.replace(":", "-") + ".md"


def write_case_md(case: Case, out_dir: Path) -> Path:
    rg = case.rechtsgebied or "—"
    front = [
        "---",
        f"ecli: {case.ecli}",
        f"court: {case.court}",
        f"date: {case.date}",
        f"published: {case.published}",
        f"zaaknummer: {case.zaaknummer}",
        f"procedure: {case.procedure}",
        f"rechtsgebied: {rg}",
        f"relevance_score: {case.score}",
        f"matched_terms: {', '.join(case.matched_terms) or '—'}",
        f"source: {case.deeplink}",
        "---",
        "",
    ]
    parts = ["\n".join(front)]
    parts.append(f"# {case.ecli}\n")
    meta = [
        f"- **Instantie:** {case.court or '—'}",
        f"- **Uitspraakdatum:** {case.date or '—'}",
        f"- **Zaaknummer:** {case.zaaknummer or '—'}",
        f"- **Procedure:** {case.procedure or '—'}",
        f"- **Rechtsgebied:** {rg}",
        f"- **Zittingsplaats:** {case.place or '—'}",
        f"- **Relevantie (art. 5 onder b):** score {case.score} "
        f"({', '.join(case.matched_terms) or 'geen treffers'})",
        f"- **Bron:** [{case.deeplink}]({case.deeplink})",
    ]
    if case.vindplaatsen:
        meta.append(f"- **Vindplaatsen:** {'; '.join(case.vindplaatsen)}")
    parts.append("\n".join(meta) + "\n")

    parts.append("## Inhoudsindicatie\n")
    parts.append((case.inhoudsindicatie or "_Geen inhoudsindicatie beschikbaar._") + "\n")

    parts.append("## Volledige tekst\n")
    if case.has_body:
        parts.append(case.body_md + "\n")
    else:
        parts.append("_Geen volledige tekst in de open-data set; "
                     f"zie [bron]({case.deeplink})._\n")

    path = out_dir / case_filename(case.ecli)
    path.write_text("\n".join(parts).rstrip() + "\n", encoding="utf-8")
    return path


def write_index(cases: list[Case], out_root: Path, cases_dir: Path) -> None:
    core = sorted([c for c in cases if c.score >= STRONG_THRESHOLD],
                  key=lambda c: c.date, reverse=True)
    related = sorted([c for c in cases if 0 < c.score < STRONG_THRESHOLD],
                     key=lambda c: c.date, reverse=True)
    failed = [c for c in cases if c.score == 0]
    rel = cases_dir.name

    lines = [
        "# Leerplichtwet art. 5 onder b — richtingbezwaar: jurisprudentie",
        "",
        "Corpus of Dutch case law on exemption from compulsory education based on "
        "objections to the *direction* (richting) of available education "
        "(Leerplichtwet 1969, art. 5 aanhef en onder b).",
        "",
        f"- Documents fetched: **{len(cases)}**",
        f"- Core art. 5-onder-b cases (strong relevance): **{len(core)}**",
        f"- Related / peripheral: **{len(related)}**",
        "- Source: Rechtspraak open data — "
        "`data.rechtspraak.nl/uitspraken/content`",
        f"- Generated: {time.strftime('%Y-%m-%d')}",
        "",
        "> Discovery note: the open-data search feed ignores text queries, so "
        "ECLI's were discovered via web search (see `scrape_leerplicht.py`) and "
        "then retrieved + relevance-scored from the authoritative content API.",
        "",
    ]

    def table(rows: list[Case]) -> list[str]:
        out = ["| Datum | Instantie | ECLI | Score | Onderwerp |",
               "|---|---|---|---|---|"]
        for c in rows:
            summary = norm(c.inhoudsindicatie).replace("|", "\\|")
            if len(summary) > 90:
                summary = summary[:87] + "…"
            link = f"[{c.ecli}]({rel}/{case_filename(c.ecli)})"
            out.append(f"| {c.date or '—'} | {c.court or '—'} | {link} | "
                       f"{c.score} | {summary or '—'} |")
        return out

    lines.append("## Kernarresten en -uitspraken (art. 5 onder b)\n")
    lines += table(core) if core else ["_Geen._"]
    lines.append("")
    if related:
        lines.append("## Gerelateerde uitspraken (leerplicht, andere grondslag)\n")
        lines += table(related)
        lines.append("")
    if failed:
        lines.append("## Zonder relevantietreffer\n")
        lines += [f"- {c.ecli} — {c.court} ({c.date})" for c in failed]
        lines.append("")

    (out_root / "index.md").write_text("\n".join(lines).rstrip() + "\n",
                                        encoding="utf-8")

    manifest = [{k: v for k, v in asdict(c).items() if k != "body_md"}
                for c in sorted(cases, key=lambda c: c.date, reverse=True)]
    (out_root / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")


def collect_eclis(args) -> list[str]:
    eclis = list(SEED_ECLIS)
    if args.seed_file:
        text = Path(args.seed_file).read_text(encoding="utf-8")
        eclis += re.findall(r"ECLI:[A-Z]{2}:[A-Z0-9]+:\d{4}:[A-Z0-9.]+", text)
    eclis += args.ecli or []
    seen, ordered = set(), []
    for e in eclis:
        if e not in seen:
            seen.add(e)
            ordered.append(e)
    return ordered


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("-o", "--out", default="leerplicht-cases",
                    help="output directory (default: leerplicht-cases)")
    ap.add_argument("--ecli", action="append", help="extra ECLI to include (repeatable)")
    ap.add_argument("--seed-file", help="file to scrape additional ECLI's from")
    ap.add_argument("--workers", type=int, default=6, help="parallel fetchers")
    args = ap.parse_args()

    eclis = collect_eclis(args)
    out_root = Path(args.out)
    cases_dir = out_root / "cases"
    cases_dir.mkdir(parents=True, exist_ok=True)

    print(f"Fetching {len(eclis)} ECLI's with {args.workers} workers...",
          file=sys.stderr)

    cases: list[Case] = []
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(fetch, CONTENT_URL + e): e for e in eclis}
        for fut in as_completed(futures):
            ecli = futures[fut]
            try:
                case = parse_case(ecli, fut.result())
            except Exception as exc:  # keep going; report at end
                print(f"  ! {ecli}: {exc}", file=sys.stderr)
                continue
            path = write_case_md(case, cases_dir)
            flag = "★" if case.score >= STRONG_THRESHOLD else " "
            print(f"  {flag} {ecli}  score={case.score:<2} -> {path.name}",
                  file=sys.stderr)
            cases.append(case)

    if not cases:
        print("No cases retrieved.", file=sys.stderr)
        return 1

    write_index(cases, out_root, cases_dir)
    core = sum(1 for c in cases if c.score >= STRONG_THRESHOLD)
    print(f"\nDone: {len(cases)} cases ({core} core) -> {out_root}/index.md",
          file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
