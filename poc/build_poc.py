"""Generate the NERON POC single-file HTML (no build step).

Embeds the canonical verified_rules.json (59 dimensional rules) and the
combined use pack (191 M-1/OS/PL rows + 322 MU rows = 513). Everything
provisional is labeled provisional. Rebuild any time the store or packs
change: `venv/bin/python poc/build_poc.py`.

STANDARDS CHANGES (e.g. the 10px base-font standard, Rishab 2026-09-24):
route through a lane claim, then:
1. Edit the builder's CSS/template (body font-size is the base; the rest is em-based).
2. Rebuild: `venv/bin/python poc/build_poc.py` (freshness gate must pass).
3. Run poc tests + full suite: `venv/bin/python -m unittest poc.test_build_poc`
   and the repo-root discover run. Confirm the built HTML embeds the new
   standard before reporting done.
"""
import html
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "poc"))

from useallow.pack import load_pack
from useallow.mu_pack import load_mu_pack
from input_freshness import (
    BUILD_DATE,
    EXPECTED_INPUTS,
    assert_inputs_fresh,
    store_fingerprint,
)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(ROOT, "poc")
os.makedirs(OUT_DIR, exist_ok=True)

store = json.load(open(os.path.join(ROOT, "rulegraph", "verified_rules.json")))
rules = store["rules"]

pack_191 = load_pack()      # 191 M-1/OS/PL rows
pack_322 = load_mu_pack()   # 322 MU rows (Caddy's verified_uses_mu.json)

# Freshness gate: refuse to build a silently stale POC. Fails loudly with the
# changed input named; update BUILD_DATE + EXPECTED_INPUTS together after
# verifying the change.
live_fps = assert_inputs_fresh(
    store_fingerprint(rules), pack_191.fingerprint, pack_322.fingerprint
)
assert set(live_fps) == set(EXPECTED_INPUTS)  # gate must cover every expected input

uses = []
for r in pack_191.rows:
    hv = r.human_verification or {}
    uses.append({
        "rule_id": r.rule_id,
        "district": r.district,
        "use_name": r.use_name,
        "status": r.status,          # permitted|conditional|not_permitted|unresolved
        "marking": r.marking,
        "footnotes": list(r.footnotes),
        "flags": r.flags,
        "provenance": r.provenance,
        "verified_by": hv.get("verified_by"),
        "verified_on": hv.get("verified_on"),
    })
n_191 = len(uses)
for r in pack_322.rows:  # 322 MU rows (Caddy's verified_uses_mu.json)
    hv = r.human_verification or {}
    uses.append({
        "rule_id": r.rule_id,
        "district": r.district,
        "use_name": r.use_name,
        "status": r.status,          # permitted|conditional only; blank cells have no rows
        "marking": r.marking,
        "footnotes": list(r.footnotes),
        "flags": r.flags,
        "provenance": r.provenance,  # "caddy-batch-verified"
        "verified_by": hv.get("verified_by"),
        "verified_on": hv.get("verified_on"),
    })
n_322 = len(uses) - n_191

rules_json = json.dumps(rules, ensure_ascii=False)
uses_json = json.dumps(uses, ensure_ascii=False)

banner = (
    "POC \u2014 MACHINE DRAFT. Not a compliance finding. Dimensional rules below are\n"
    "human-verified as labeled; every provisional figure is an estimate, labeled "
    '<span class="provisional">provisional</span>.\n'
    f"Built {BUILD_DATE} from the canonical verified rule store ({len(rules)} rules) "
    f"+ use packs ({len(uses)} rows: {n_191} M-1/OS/PL + {n_322} MU)."
    f' <span class="tag">input fingerprints: store {live_fps["rule_store"][:12]} · '
    f'm1_os_pl {live_fps["pack_m1_os_pl"][:12]} · mu {live_fps["pack_mu"][:12]}</span>'
)

page = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>NERON — POC (machine draft)</title>
<style>
body{font-family:system-ui,-apple-system,sans-serif;font-size:10px;max-width:960px;margin:0 auto;padding:16px;color:#1a1a1a}
.banner{background:#fff3cd;border:2px solid #b78a00;padding:12px 16px;border-radius:8px;margin-bottom:20px;font-weight:600}
section{border:1px solid #ddd;border-radius:8px;padding:16px;margin-bottom:20px}
h1{font-size:1.6em}h2{font-size:1.2em;margin-top:0}
.pill{display:inline-block;background:#eef;padding:2px 8px;border-radius:12px;font-size:.85em;margin:2px}
.tag{font-size:.8em;color:#555}
.provisional{color:#8a5a00;font-weight:600}
table{border-collapse:collapse;width:100%;font-size:.9em}
th,td{border:1px solid #ccc;padding:6px 8px;text-align:left;vertical-align:top}
th{background:#f5f5f5}
input,select{font-size:1em;padding:6px 8px;margin:4px 0}
.quote{font-style:italic;color:#333}
.district-btn{cursor:pointer;margin:2px}
.district-btn.active{background:#0b5fff;color:#fff;border-color:#0b5fff}
</style>
</head>
<body>
<div class="banner">__BANNER__</div>

<h1>NERON — parcel feasibility POC</h1>

<section>
<h2>1. Dimensional rules by district</h2>
<div id="districts"></div>
<div id="rules"></div>
<p class="tag">47 of the 59 canonical rules are stored-but-not-executable (no evaluator
registered) and evaluate UNKNOWN in the engine — honest UNKNOWN, never FAIL.
Executable coverage grows as Caddy's native-store params land.</p>
</section>

<section>
<h2>2. Use lookup (all districts)</h2>
<p class="tag">__N_USES__ use rows: __N_191__ M-1/OS/PL (21A.33.040/.070, Rohan-verified)
+ __N_322__ MU-5/MU-6/MU-11 (21A.33.030, Caddy batch-verified 2026-09-23).
MU blank cells have no rows: an absent MU use evaluates UNKNOWN, never
"not allowed" — the extraction may be incomplete.</p>
<input id="q" type="text" placeholder="Search a use, e.g. bar, warehouse, daycare" size="42">
<div id="uses"></div>
</section>

<section>
<h2>3. Jefferson demo walkthrough <span class="tag">(canned demo numbers)</span></h2>
<p>A real parcel run through the pipeline (demo input, <span class="provisional">provisional</span> economics):</p>
<table>
<tr><th>Scheme</th><th>Lots</th><th>Profit</th><th>Margin</th><th>RuleGraph</th><th>Use allowance</th></tr>
<tr><td>Top scheme</td><td>11</td><td class="provisional">$634,700 (demo, provisional)</td><td class="provisional">60.7% (demo, provisional)</td><td>8/8 UNKNOWN — canonical store: MU rules stored-but-not-executable (honest UNKNOWN, not FAIL)</td><td>UNKNOWN — no proposed uses supplied</td></tr>
<tr><td>Jefferson parcel</td><td>—</td><td class="provisional">$602,392 (demo, provisional)</td><td class="provisional">81.4% (demo, provisional)</td><td colspan="2">canned walkthrough figures</td></tr>
</table>
<p class="tag">Jefferson: top-scheme profit <span class="provisional">$602,392 (provisional)</span>,
margin <span class="provisional">81.4% (provisional)</span>. Economics are starting estimates, not appraisals.</p>
</section>

<script>
const RULES = __RULES__;
const USES = __USES__;
const DISTRICTS = ["MU-5","MU-6","MU-11","M-1","OS","PL"];

function esc(s){return String(s==null?"":s).replace(/[&<>"]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));}

function ruleApplies(r,d){
  if(r.district===d)return true;
  if(Array.isArray(r.districts)&&r.districts.indexOf(d)>=0)return true;
  return false;
}
function ruleDistricts(r){
  if(Array.isArray(r.districts))return r.districts.join(", ");
  return r.district||"";
}
function paramsText(r){
  const p=r.canonical_params;
  if(p==null)return"";
  if(typeof p==="string")return p;
  try{return JSON.stringify(p);}catch(e){return"";}
}

function renderDistricts(active){
  const d=document.getElementById("districts");
  d.innerHTML=DISTRICTS.map(x=>`<button class="district-btn${x===active?' active':''}" data-d="${x}">${x}</button>`).join("");
  d.querySelectorAll("button").forEach(b=>b.onclick=()=>{renderDistricts(b.dataset.d);renderRules(b.dataset.d);});
}
function renderRules(district){
  const rows=RULES.filter(r=>ruleApplies(r,district));
  const el=document.getElementById("rules");
  if(!rows.length){el.innerHTML=`<p>No dimensional rules in the verified store for <strong>${esc(district)}</strong> yet.</p>`;return;}
  el.innerHTML=`<table><tr><th>Rule</th><th>Name</th><th>Claimed value</th><th>Quote</th><th>Verified</th></tr>`+
    rows.map(r=>`<tr><td><span class="pill">${esc(r.rule_id)}</span><br><span class="tag">${esc(r.citation||"")}</span><br><span class="tag">${esc(ruleDistricts(r))}</span></td>`+
      `<td>${esc(r._caddy_rule_name||"")}</td><td>${esc(paramsText(r))}</td>`+
      `<td class="quote">${esc(r.quote||"")}</td>`+
      `<td>${esc(r.human_verification.verified_by)}, ${esc(r.human_verification.verified_on)}<br><span class="tag">${esc(r.human_verification.result)}</span></td></tr>`).join("")+`</table>`;
}
function useLabel(u){
  if(u.status==="unresolved")return"Needs human review";
  if(u.footnotes&&u.footnotes.length)return"Needs human review";
  if(u.status==="permitted")return"Permitted";
  if(u.status==="conditional")return"Conditional";
  if(u.status==="not_permitted")return"Not allowed";
  return"Needs human review";
}
function renderUses(){
  const q=document.getElementById("q").value.trim().toLowerCase();
  const el=document.getElementById("uses");
  if(!q){el.innerHTML="<p class='tag'>Type to search the __N_USES__ verified use rows.</p>";return;}
  const hits=USES.filter(u=>u.use_name.toLowerCase().includes(q)).slice(0,40);
  if(!hits.length){el.innerHTML="<p>No matching use in the pack — verdict would be UNKNOWN (no verified row).</p>";return;}
  el.innerHTML=`<table><tr><th>Use</th><th>District</th><th>Verdict</th><th>Rule</th><th>Detail</th></tr>`+
    hits.map(u=>`<tr><td>${esc(u.use_name)}</td><td>${esc(u.district)}</td><td><strong>${esc(useLabel(u))}</strong></td>`+
      `<td><span class="pill">${esc(u.rule_id)}</span></td>`+
      `<td class="tag">${esc(u.marking||"")}${u.footnotes&&u.footnotes.length?" · footnotes "+u.footnotes.join(","):""}${u.flags?" · "+esc(u.flags):""}<br>${esc(u.provenance||"")} · verified: ${esc(u.verified_by)}, ${esc(u.verified_on)}</td></tr>`).join("")+`</table>`;
}
document.getElementById("q").addEventListener("input",renderUses);
renderDistricts("MU-11");renderRules("MU-11");renderUses();
</script>
</body>
</html>
"""
page = (page.replace("__BANNER__", banner)
            .replace("__RULES__", rules_json)
            .replace("__USES__", uses_json)
            .replace("__N_USES__", str(len(uses)))
            .replace("__N_191__", str(n_191))
            .replace("__N_322__", str(n_322)))
out = os.path.join(OUT_DIR, "neron_poc.html")
with open(out, "w") as f:
    f.write(page)
print("wrote", out, len(page), "bytes")
print("rules embedded:", len(rules), "| uses embedded:", len(uses),
      f"({n_191} M-1/OS/PL + {n_322} MU)")
