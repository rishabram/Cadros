#!/usr/bin/env python3
"""
validate_store.py -- machine-side validator for the NERON verified rule store.

READ-ONLY WITH RESPECT TO VERDICTS: this harness NEVER invents, alters, or
implies a human verdict. It checks only machine-checkable facts and reports
findings; humans judge.

Checks
  [1] schema conformance -- every rule has rule_id, district, citation, quote,
      params, and human_verification{result, verified_by, verified_on}; the
      result value is one of the allowed enum
      {VERIFIED, CORRECTED, REJECTED, UNVERIFIED}. Field aliases "section" and
      "source_quote" are accepted for "citation"/"quote" (reported as notes).
  [2] citation resolvability -- every cited section (e.g. 21A.25.070) appears
      in the retrieved code text under the zoning corpus directory
      (default ~/workspace/neron-zoning/, files matching slc_code_*.md).
  [3] quote fidelity -- the recorded quote appears verbatim in the retrieved
      text. If not verbatim, the harness reports the closest matching passage
      and classifies it as MEANING-PRESERVED (heuristic similarity; needs a
      human to confirm) or MISMATCH. Absence claims (e.g. MU-11-11) get a
      machine-negative check instead: the cited sections are scanned for any
      contradicting "minimum lot area/width/size" language.
  [4] store fingerprint -- recomputed via fingerprint.canonical_hash and
      compared with the PINNED_FINGERPRINT in test_rulegraph.py when found.

Outcomes: PASS (machine check satisfied), REVIEW (machine cannot fully
decide; flagged for human judgment -- does not force a nonzero exit), FAIL
(machine-checkable requirement violated -- forces exit code 1).

Usage:
    python3 validate_store.py [store.json] [--zoning-dir DIR] [--corpus-glob GLOB]
"""

import argparse
import difflib
import json
import math
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))  # fingerprint.py lives next to this file
from fingerprint import canonical_hash  # noqa: E402

ALLOWED_RESULTS = {"VERIFIED", "CORRECTED", "REJECTED", "UNVERIFIED"}
EXECUTABLE_RESULTS = {"VERIFIED", "CORRECTED"}  # mirrors engine.EXECUTABLE_RESULTS
FIELD_ALIASES = {
    "citation": ("citation", "section"),
    "quote": ("quote", "source_quote"),
    # Engine-adapted canonical store (build_canonical_store.py): the verified
    # value/unit record lives under "canonical_params" (execution "params"
    # exist only for the executable subset); a rule scoped to several
    # districts carries a "districts" list instead of a "district" string.
    "params": ("params", "canonical_params"),
    "district": ("district", "districts"),
}
SIMILARITY_THRESHOLD = 0.55  # closest-passage heuristic boundary; see README
SECTION_RE = re.compile(r"21A\.\d+\.\d+")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
PINNED_RE = re.compile(r'PINNED_FINGERPRINT\s*=\s*"([0-9a-f]{64})"')
# Contradicting language for absence claims ("no minimum lot area/width").
CONTRA_RE = re.compile(r"minimum\s+lot\s+(area|width|size)", re.IGNORECASE)
NEGATION_RE = re.compile(r"\b(no|none|not|without|never)\b", re.IGNORECASE)
# After-window negation: "Minimum Lot Area And Lot Width: None required."
NEG_AFTER_RE = re.compile(r"\bnone\b|no\s+minimum|not\s+required",
                           re.IGNORECASE)


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------

def norm_ws(text):
    """Collapse all whitespace runs to single spaces."""
    return re.sub(r"\s+", " ", text).strip()


def strip_md(text):
    """Remove lightweight markdown markers that never occur in code text."""
    return text.replace("**", "").replace("__", "")


def resolve_field(rule, name):
    """Return (value, key_used, aliased). Tries aliases in order."""
    keys = FIELD_ALIASES.get(name, (name,))
    for key in keys:
        if key in rule and rule[key] not in (None, ""):
            return rule[key], key, key != keys[0]
    return rule.get(keys[0]), keys[0], False


def load_corpus(zoning_dir, glob):
    files = sorted(Path(zoning_dir).glob(glob))
    return [(p, p.read_text(encoding="utf-8")) for p in files]


def section_slices(corpus):
    """Map base section id -> (filename, text between its '##' heading and the
    next '##' heading). Only headings are used as slice boundaries."""
    slices = {}
    for path, text in corpus:
        lines = text.splitlines()
        cur_id, cur_start = None, None
        bounds = []
        for i, line in enumerate(lines):
            if line.startswith("##"):
                m = SECTION_RE.search(line)
                if cur_id is not None:
                    bounds.append((cur_id, cur_start, i))
                cur_id, cur_start = (m.group(0), i) if m else (None, None)
        if cur_id is not None:
            bounds.append((cur_id, cur_start, len(lines)))
        for sid, start, end in bounds:
            body = "\n".join(lines[start:end])
            if sid not in slices:  # first occurrence wins
                slices[sid] = (path.name, body)
    return slices


def candidates_from(text):
    """Split scoped text into candidate passages (paragraphs + bullet lines)."""
    cands = []
    for para in re.split(r"\n\s*\n", text):
        para = para.strip()
        if not para:
            continue
        cands.append(para)
        for line in para.splitlines():
            line = line.strip()
            if re.match(r"^[-*]\s+", line) and len(line) > 40:
                cands.append(line)
    return cands


def sim(a, b):
    return difflib.SequenceMatcher(None, a, b).ratio()


TOKEN_SYNONYMS = {
    "feet": "ft", "foot": "ft",
    "minimum": "min", "maximum": "max",
    "chapter": "ch", "street": "st", "avenue": "ave",
}


def word_tokens(text):
    toks = re.findall(r"[a-z0-9]+", text.lower())
    return [TOKEN_SYNONYMS.get(t, t) for t in toks]


def closest_passage(quote, text):
    """Return (best_score, best_passage) over candidate passages.

    Scoring is distinctiveness-weighted token recall: what fraction of the
    quote's content tokens (weighted by IDF over the candidates, so rare
    tokens like "mcclelland" or "125" count more than "the" or "21a") is
    covered by the candidate, blended with char-level sequence ratio. This
    ranks paraphrases ("125 feet" vs "125' max") far above passages that
    merely share boilerplate (e.g. the same zone list).
    """
    nq = norm_ws(strip_md(quote)).lower()
    # A trailing "(Table C.2, 21A.25.070)"-style reference is a retrieval note,
    # not code text; score with and without it and take the better ratio.
    nq_noref = re.sub(r"\s*\([^()]*table[^()]*\)\s*$", "", nq, flags=re.IGNORECASE)
    variants = [nq, nq_noref]
    cands = []
    for cand in candidates_from(text):
        nc = norm_ws(strip_md(cand)).lower()
        if len(nc) < 20:
            continue
        cands.append((nc, cand.strip()))
    if not cands:
        return 0.0, ""
    tok_lists = [word_tokens(nc) for nc, _ in cands]
    n = len(tok_lists)
    df = {}
    for toks in tok_lists:
        for t in set(toks):
            df[t] = df.get(t, 0) + 1
    weights = {t: math.log(1 + n / (1 + c)) for t, c in df.items()}
    best = (0.0, "")
    for (nc, raw), ct in zip(cands, tok_lists):
        cset = set(ct)
        for v in variants:
            qs = set(word_tokens(v))
            den = sum(weights.get(t, 0.0) for t in qs)
            rec = (sum(weights.get(t, 0.0) for t in qs if t in cset) / den
                   if den else 0.0)
            r = 0.7 * rec + 0.3 * sim(v, nc)
            if r > best[0]:
                best = (r, raw)
    return best


def word_diff(a, b, max_lines=40):
    diff = difflib.unified_diff(
        a.split(), b.split(), fromfile="recorded quote",
        tofile="closest retrieved passage", n=4, lineterm="",
    )
    lines = list(diff)
    if len(lines) > max_lines:
        lines = lines[:max_lines] + ["... (diff truncated)"]
    return "\n".join(lines)


# --------------------------------------------------------------------------
# checks [1]-[3] (per rule)
# --------------------------------------------------------------------------

def check_schema(rule):
    notes, problems = [], []
    # required fields
    for name in ("rule_id", "district", "citation", "quote", "params",
                 "human_verification"):
        value, key, aliased = resolve_field(rule, name)
        if value in (None, ""):
            problems.append(f"missing required field {name!r} "
                            f"(aliases tried: {', '.join(FIELD_ALIASES.get(name, (name,)))})")
        elif aliased:
            notes.append(f"field {name!r} supplied via alias {key!r}")
    rid, _, _ = resolve_field(rule, "rule_id")
    if isinstance(rid, str) and not rid.strip():
        problems.append("rule_id is empty")
    district, _, _ = resolve_field(rule, "district")
    if isinstance(district, str) and not district.strip():
        problems.append("district is empty")
    if isinstance(district, (list, tuple)) and not district:
        problems.append("districts list is empty")
    params, _, _ = resolve_field(rule, "params")
    if params is not None and not isinstance(params, dict):
        problems.append(f"params must be an object, got {type(params).__name__}")
    hv, _, _ = resolve_field(rule, "human_verification")
    gate_info = "gate: not evaluable (see problems)"
    if isinstance(hv, dict):
        result = hv.get("result")
        by = str(hv.get("verified_by") or "").strip()
        on = str(hv.get("verified_on") or "").strip()
        if result not in ALLOWED_RESULTS:
            problems.append(
                f"human_verification.result {result!r} not in allowed enum "
                f"{sorted(ALLOWED_RESULTS)}")
        if not by:
            problems.append("human_verification.verified_by is empty")
        if not on:
            problems.append("human_verification.verified_on is empty")
        elif not DATE_RE.match(on):
            notes.append(f"verified_on {on!r} is not YYYY-MM-DD "
                         f"(informational only)")
        if result in EXECUTABLE_RESULTS and by and on:
            gate_info = (f"gate: executable by engine "
                         f"(result={result}, by={by}, on={on})")
        else:
            gate_info = (f"gate: NOT executable by engine "
                         f"(result={result!r}; engine requires VERIFIED/CORRECTED "
                         f"+ named verifier/date)")
    elif hv is not None:
        problems.append("human_verification must be an object")
    verdict = "FAIL" if problems else "PASS"
    detail = "; ".join(problems + notes) if (problems or notes) else "all fields present"
    return verdict, [detail, gate_info]


def check_citation(rule, corpus, slices):
    citation, key, aliased = resolve_field(rule, "citation")
    if not citation:
        return "FAIL", ["no citation to resolve (see schema check)"]
    raw = str(citation).strip()
    base_m = SECTION_RE.search(raw.replace("§", ""))
    needles = []
    if base_m:
        needles.append(base_m.group(0))
    if raw.replace("§", "").strip() not in needles:
        needles.append(raw.replace("§", "").strip())
    hits = []
    for path, text in corpus:
        for n in needles:
            if n and n in text:
                hits.append((path.name, n))
                break
    if hits:
        files = sorted({f for f, _ in hits})
        note = f"{'/'.join(needles)} found in {', '.join(files)}"
        if aliased:
            note += f" (citation read from field {key!r})"
        return "PASS", [note]
    scope = "no retrievable section scope"
    if base_m and base_m.group(0) in slices:
        scope = f"section scope available in {slices[base_m.group(0)][0]}"
    return "FAIL", [f"{'/'.join(needles)} NOT found in any corpus file "
                    f"({len(corpus)} files searched); {scope}"]


def check_quote(rule, corpus, slices):
    quote, key, aliased = resolve_field(rule, "quote")
    if not quote or not str(quote).strip():
        return "FAIL", ["no quote to check (see schema check)"]
    quote = str(quote)
    full_text = "\n\n".join(t for _, t in corpus)

    # --- absence claims: machine-negative check, not a verbatim check ---
    claim = str(rule.get("claim") or "")
    if "absence" in (quote + " " + claim).lower():
        return _check_absence_claim(rule, quote, corpus, slices)

    # --- tier 1: exact verbatim ---
    if quote in full_text:
        return "PASS", ["verbatim match in retrieved text (exact)"]
    # --- tier 2: format-tolerant verbatim (markdown/whitespace) ---
    nq = norm_ws(strip_md(quote))
    for _, text in corpus:
        if nq in norm_ws(strip_md(text)):
            return "PASS", ["verbatim match in retrieved text "
                            "(whitespace/markdown-tolerant)"]

    # --- tier 3: closest passage ---
    citation, _, _ = resolve_field(rule, "citation")
    scope_text, scope_src = full_text, "full corpus"
    base_m = SECTION_RE.search(str(citation or "").replace("§", ""))
    if base_m and base_m.group(0) in slices:
        fname, body = slices[base_m.group(0)]
        scope_text = body
        scope_src = f"section {base_m.group(0)} in {fname}"
    ratio, passage = closest_passage(quote, scope_text)
    header = (f"NOT verbatim in retrieved text "
              f"(searched {scope_src}); closest passage "
              f"(heuristic similarity {ratio:.2f}):")
    body = [header, f'"""{passage[:1200]}"""']
    if ratio >= SIMILARITY_THRESHOLD:
        body.append("verdict: MEANING-PRESERVED (heuristic -- "
                    "a human must confirm the paraphrase)")
        body.append(word_diff(nq, norm_ws(strip_md(passage))))
        return "REVIEW", body
    body.append("verdict: MISMATCH -- closest passage is too dissimilar; "
                "human review required")
    body.append(word_diff(nq, norm_ws(strip_md(passage))))
    return "FAIL", body


def _check_absence_claim(rule, quote, corpus, slices):
    """Negative check for absence claims: scan the cited sections' text for
    contradicting 'minimum lot area/width/size' language. A negative machine
    check is NOT a proof of absence -- best outcome is REVIEW."""
    text = " ".join([str(rule.get("citation") or rule.get("section") or ""),
                     str(rule.get("claim") or ""), quote])
    sections = []
    for m in SECTION_RE.finditer(text):
        if m.group(0) not in sections:
            sections.append(m.group(0))
    if not sections:
        return "REVIEW", ["absence claim cites no parseable section id; "
                          "cannot scope negative check -- human review required"]
    contradictions, notes = [], []
    for sid in sections:
        if sid not in slices:
            notes.append(f"section {sid}: not present in retrieved text; "
                         f"negative check could not cover it")
            continue
        fname, body = slices[sid]
        # Headings and ★ meta-notes carry retriever commentary ("Minimum-lot-
        # size finding ... the absence claim is supported"), not code text, so
        # they are excluded from the contradiction scan.
        code_lines = [ln for ln in body.splitlines()
                      if not ln.lstrip().startswith("#") and "★" not in ln]
        code_text = "\n".join(code_lines)
        for m in CONTRA_RE.finditer(code_text):
            before = code_text[max(0, m.start() - 40):m.start()]
            after = code_text[m.end():m.end() + 200]
            if NEGATION_RE.search(before) or NEG_AFTER_RE.search(after):
                continue  # "no minimum lot area ..." / "...: None required"
            start = max(0, m.start() - 120)
            contradictions.append(
                f"{sid} ({fname}): ...{norm_ws(code_text[start:m.end() + 120])}...")
    if contradictions:
        return "FAIL", (["ABSENCE-CONTRADICTED: retrieved text asserts a "
                         "minimum where the claim says none:"] + contradictions)
    # Related evidence: prefer passages that actually discuss "minimum lot".
    related = []
    for sid in sections:
        if sid not in slices:
            continue
        body = slices[sid][1]
        minlot_paras = [p for p in candidates_from(body)
                        if re.search(r"minimum[\s-]+lot", p, re.IGNORECASE)]
        if not minlot_paras:
            continue
        score, cand = closest_passage(quote, "\n\n".join(minlot_paras))
        related.append((score, sid, cand))
    related.sort(key=lambda t: t[0], reverse=True)
    out = ["ABSENCE-CONSISTENT: no contradicting 'minimum lot area/width/size' "
           "language found in the cited sections' retrieved text. "
           "A negative machine check is NOT a proof of absence -- "
           "human judgment required."]
    out += notes
    for score, sid, cand in related[:2]:
        out.append(f"related passage in {sid} (similarity {score:.2f}): "
                   f'"""{cand[:800]}"""')
    if not related:
        out.append("no passage mentioning 'minimum lot' found in the cited "
                   "sections at all")
    return "REVIEW", out


# --------------------------------------------------------------------------
# store-level checks
# --------------------------------------------------------------------------

def check_duplicates(rules):
    seen, dupes = {}, []
    for r in rules:
        rid = r.get("rule_id")
        if rid in seen:
            dupes.append(rid)
        seen[rid] = True
    if dupes:
        return "FAIL", [f"duplicate rule_ids: {sorted(set(dupes))}"]
    return "PASS", [f"{len(rules)} rules, no duplicate rule_ids"]


def fingerprint_block(store):
    lines = []
    store_hash = canonical_hash(store)
    rules_hash = canonical_hash({"rules": store.get("rules", [])})
    lines.append(f"store fingerprint (canonical_hash of full store): {store_hash}")
    lines.append(f"rules fingerprint (canonical_hash of {{'rules': rules}}, "
                 f"engine-stamped): {rules_hash}")
    test_path = HERE / "test_rulegraph.py"
    pinned = None
    if test_path.exists():
        m = PINNED_RE.search(test_path.read_text(encoding="utf-8"))
        if m:
            pinned = m.group(1)
    if pinned is None:
        lines.append("pinned value: not found in test_rulegraph.py (skipped)")
        return "REVIEW", lines
    if rules_hash == pinned:
        lines.append(f"pinned PINNED_FINGERPRINT in test_rulegraph.py: MATCH")
        return "PASS", lines
    lines.append(f"pinned PINNED_FINGERPRINT in test_rulegraph.py: MISMATCH")
    lines.append(f"  pinned:   {pinned}")
    lines.append(f"  computed: {rules_hash}")
    lines.append("store changed without updating the test pin "
                 "(or vice versa) -- human must reconcile")
    return "FAIL", lines


# --------------------------------------------------------------------------
# report
# --------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(
        description="Machine-side validator for the NERON verified rule store.")
    ap.add_argument("store", nargs="?",
                    default=str(HERE / "verified_rules.json"),
                    help="path to verified_rules.json")
    ap.add_argument("--zoning-dir", default=str(Path.home() / "workspace" / "neron-zoning"),
                    help="directory of retrieved code text")
    ap.add_argument("--corpus-glob", default="slc_code_*.md",
                    help="glob for retrieved-text files inside --zoning-dir")
    args = ap.parse_args()

    store_path = Path(args.store)
    try:
        store = json.loads(store_path.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"FATAL: cannot load store {store_path}: {e}", file=sys.stderr)
        return 2
    rules = store.get("rules")
    if not isinstance(rules, list):
        print("FATAL: store has no 'rules' list", file=sys.stderr)
        return 2

    corpus = load_corpus(args.zoning_dir, args.corpus_glob)
    if not corpus:
        print(f"FATAL: no corpus files matching {args.corpus_glob!r} in "
              f"{args.zoning_dir}", file=sys.stderr)
        return 2
    slices = section_slices(corpus)

    out = []
    out.append("=" * 72)
    out.append(f"NERON rule-store validation -- {store_path}")
    out.append(f"rules: {len(rules)} | corpus: {args.corpus_glob} "
               f"({len(corpus)} files in {args.zoning_dir})")
    out.append("READ-ONLY re verdicts: findings reported; humans judge.")
    out.append("=" * 72)

    tally = {"PASS": 0, "REVIEW": 0, "FAIL": 0}
    any_fail = False
    for rule in rules:
        rid = rule.get("rule_id", "<missing rule_id>")
        title = rule.get("title", "")
        district, _, _ = resolve_field(rule, "district")
        citation, _, _ = resolve_field(rule, "citation")
        hv = rule.get("human_verification") or {}
        out.append("")
        out.append(f"RULE {rid} -- {title}")
        out.append(f"  district={district} citation={citation} "
                   f"result={hv.get('result')} "
                   f"by={hv.get('verified_by')} on={hv.get('verified_on')}")
        for num, (name, fn) in (
                ("1", ("schema", lambda: check_schema(rule))),
                ("2", ("citation", lambda: check_citation(rule, corpus, slices))),
                ("3", ("quote fidelity", lambda: check_quote(rule, corpus, slices)))):
            verdict, details = fn()
            tally[verdict] += 1
            if verdict == "FAIL":
                any_fail = True
            out.append(f"  [{num}] {name:14s} {verdict}")
            for d in details:
                for line in str(d).splitlines():
                    out.append(f"        {line}")

    out.append("")
    out.append("-" * 72)
    out.append("STORE-LEVEL")
    for name, fn in (("duplicate rule_ids", lambda: check_duplicates(rules)),
                     ("fingerprint", lambda: fingerprint_block(store))):
        verdict, details = fn()
        tally[verdict] += 1
        if verdict == "FAIL":
            any_fail = True
        out.append(f"  {name:18s} {verdict}")
        for d in details:
            for line in str(d).splitlines():
                out.append(f"        {line}")

    out.append("")
    out.append("-" * 72)
    out.append(f"SUMMARY: {tally['PASS']} PASS, {tally['REVIEW']} REVIEW, "
               f"{tally['FAIL']} FAIL")
    out.append("EXIT: " + ("1 (one or more checks FAILED)" if any_fail
                           else "0 (no check failed; REVIEWs need human eyes)"))
    print("\n".join(out))
    return 1 if any_fail else 0


if __name__ == "__main__":
    sys.exit(main())
