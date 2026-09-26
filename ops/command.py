#!/usr/bin/env python3
"""command - Cadros central command board.

One canonical task ledger that every agent reads and writes. The ledger is an
append-only event log (board.jsonl). Current state is the fold of that log, so
ten agents can write concurrently without locks and without lost updates:
each mutation is a single sub-4KB O_APPEND write, which POSIX makes atomic.

Conflict rule: for any task, the FIRST event of a kind wins. Two agents that
claim the same task both succeed at writing; the fold names one winner and
`claim` tells the loser it lost. No file is ever rewritten in place.

Standard library only. No network. Nothing here touches the engine.
"""

import json
import os
import sys
from datetime import datetime, timedelta

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(ROOT, "data")
BOARD = os.path.join(DATA, "board.jsonl")
BOARD_MD = os.path.join(os.path.dirname(ROOT), "BOARD.md")

STATES = ("READY", "CLAIMED", "RUNNING", "REVIEW", "MERGED",
          "BLOCKED_HUMAN", "BLOCKED_TECHNICAL", "WAITING_FOR_WAKE")
TERMINAL = ("MERGED",)
LIVE = ("CLAIMED", "RUNNING", "REVIEW")

# Gate clock. Local wall time on the day of the sprint.
GATES = [
    ("14:00", "policy lock",         "Soarer",            "one crisp intervention named"),
    ("18:00", "evidence lock",       "Caddy / LEX",       "every headline claim sourced"),
    ("20:00", "quantification lock", "LeBron",            "reproducible + labeled numbers"),
    ("22:00", "narrative lock",      "Overseer",          "three-minute coherent story"),
    ("08:45", "submission lock",     "founders",          "uploaded and confirmed"),
]

# Who exists, what they own, and where they run.
ROSTER = {
    "LeBron":       ("Muse",         "COO - coordination, priorities, task state, deconfliction"),
    "Cora":         ("Muse",         "CTO - architecture; SOLE hackathon verification authority"),
    "D-Wade":       ("Muse",         "CEng - deterministic engine, regression discipline"),
    "TMac":         ("Muse",         "CStrategy - market thesis, falsification, pivot"),
    "Caddy":        ("Muse",         "CEvidence - evidence readiness, rule-store, provenance"),
    "Soarer":       ("Muse",         "CCommercial - positioning, policy/bottleneck selection"),
    "Chat 1":       ("Chat Plus",    "CEval - independent benchmark scoring and verification"),
    "Chat 2":       ("Chat Plus",    "CFO - financial models, economics, cost visibility"),
    "Antigravity 1":("Antigravity",  "CDataSystems - spatial pipelines, geospatial reliability"),
    "Antigravity 2":("Antigravity",  "CPlatformDelivery - runtime, deployment, delivery"),
    "Spark 1":      ("Gemini Spark", "research worker under TMac"),
    "Spark 2":      ("Gemini Spark", "commercial drafting worker under Soarer"),
}

DOCTRINE = [
    "Models interpret evidence. Deterministic software owns geometry, validation,",
    "rule execution, arithmetic, ranking and export.",
    "Missing information never defaults to compliance. Unknowns stay visible.",
    "One accountable owner, one acceptance test, one named artifact, one reviewer.",
    "The producing lane is never the only reviewer of a headline result.",
    "No fabricated precision. No hidden denominator. No self-verification.",
    "Founders retain final control over money, credentials, legal commitments,",
    "external promises, deployments, pivots, and human verification verdicts.",
]


# ---------- io ----------

def now():
    return datetime.now().astimezone()


def ts(dt=None):
    return (dt or now()).strftime("%Y-%m-%dT%H:%M")


def ensure():
    os.makedirs(DATA, exist_ok=True)
    if not os.path.exists(BOARD):
        open(BOARD, "a").close()


def emit(ev):
    """One atomic append. Never rewrites. Never locks."""
    ensure()
    ev.setdefault("at", ts())
    line = json.dumps(ev, sort_keys=True) + "\n"
    if len(line.encode()) > 4000:
        raise SystemExit("event too large to append atomically; shorten the text")
    fd = os.open(BOARD, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
    try:
        os.write(fd, line.encode())
    finally:
        os.close(fd)


def events():
    ensure()
    out = []
    with open(BOARD) as fh:
        for ln in fh:
            ln = ln.strip()
            if ln:
                try:
                    out.append(json.loads(ln))
                except ValueError:
                    pass
    return out


def fold():
    """Current task state = deterministic fold of the event log."""
    tasks = {}
    for e in events():
        tid = e.get("task")
        if not tid:
            continue
        k = e.get("kind")
        if k == "POST":
            if tid in tasks:
                continue                      # first POST wins
            tasks[tid] = {
                "task": tid, "title": e.get("title", ""),
                "owner": e.get("owner", "-"), "reviewer": e.get("reviewer", "-"),
                "acceptance": e.get("acceptance", "-"),
                "artifact": e.get("artifact", "-"),
                "gate": e.get("gate", "-"), "priority": e.get("priority", "P2"),
                "state": "READY", "posted": e["at"], "touched": e["at"],
                "note": "", "by": e.get("by", "-"),
            }
        elif tid in tasks:
            t = tasks[tid]
            t["touched"] = e["at"]
            if k == "CLAIM":
                if t["state"] == "READY" or t["owner"] in ("-", "", "UNASSIGNED"):
                    t["owner"] = e.get("by", "-")
                    t["state"] = "CLAIMED"    # first CLAIM wins; later ones are no-ops
            elif k == "STATE":
                st = e.get("state")
                if st in STATES:
                    t["state"] = st
                if e.get("note"):
                    t["note"] = e["note"]
                if e.get("artifact"):
                    t["artifact"] = e["artifact"]
            elif k == "ASSIGN":
                t["owner"] = e.get("owner", t["owner"])
                if t["state"] == "READY":
                    t["state"] = "CLAIMED"
            elif k == "NOTE":
                t["note"] = e.get("note", t["note"])
    return tasks


def age_min(t):
    try:
        then = datetime.strptime(t["touched"], "%Y-%m-%dT%H:%M").astimezone()
        return int((now() - then).total_seconds() // 60)
    except Exception:
        return 0


def next_gate():
    n = now()
    for hhmm, name, owner, cond in GATES:
        h, m = (int(x) for x in hhmm.split(":"))
        when = n.replace(hour=h, minute=m, second=0, microsecond=0)
        if when < n:
            when += timedelta(days=1) if h < 12 else timedelta(0)
        if when > n:
            return hhmm, name, owner, cond, int((when - n).total_seconds() // 60)
    return None


# ---------- commands ----------

def cmd_post(a):
    tid = a.task or "CADROS-%s-%03d" % (now().strftime("%Y%m%d"), len(fold()) + 1)
    if tid in fold():
        raise SystemExit("task %s already exists" % tid)
    emit({"kind": "POST", "task": tid, "title": a.title, "owner": a.owner or "UNASSIGNED",
          "reviewer": a.reviewer or "-", "acceptance": a.acceptance,
          "artifact": a.artifact or "-", "gate": a.gate or "-",
          "priority": a.priority, "by": a.by or "LeBron"})
    if a.owner and a.owner != "UNASSIGNED":
        emit({"kind": "ASSIGN", "task": tid, "owner": a.owner, "by": a.by or "LeBron"})
    print("posted %s -> %s" % (tid, a.owner or "UNASSIGNED"))
    return 0


def cmd_claim(a):
    t = fold().get(a.task)
    if not t:
        raise SystemExit("no such task: %s" % a.task)
    emit({"kind": "CLAIM", "task": a.task, "by": a.agent})
    t = fold()[a.task]
    if t["owner"] == a.agent:
        print("CLAIMED %s by %s" % (a.task, a.agent))
        print("  acceptance: %s" % t["acceptance"])
        print("  artifact  : %s" % t["artifact"])
        print("  reviewer  : %s" % t["reviewer"])
        return 0
    print("LOST %s - already owned by %s. Pick another task." % (a.task, t["owner"]))
    return 1


def cmd_state(a):
    if a.task not in fold():
        raise SystemExit("no such task: %s" % a.task)
    emit({"kind": "STATE", "task": a.task, "state": a.to, "note": a.note or "",
          "artifact": a.artifact or "", "by": a.agent or "-"})
    print("%s -> %s" % (a.task, a.to))
    if a.to == "REVIEW":
        r = fold()[a.task]["reviewer"]
        print("  reviewer %s must sign before MERGED. The producing lane cannot self-verify." % r)
    return 0


def cmd_board(a):
    tasks = fold()
    g = next_gate()
    lines = ["# Cadros BOARD - canonical operating state",
             "", "generated %s  |  do not hand-edit; every change is a cadops command" % ts(), ""]
    if g:
        lines += ["**Next gate: %s %s** - owner %s - %s - **%dh%02dm out**"
                  % (g[0], g[1], g[2], g[3], g[4] // 60, g[4] % 60), ""]
    by_state = {}
    for t in tasks.values():
        by_state.setdefault(t["state"], []).append(t)
    order = ["BLOCKED_HUMAN", "BLOCKED_TECHNICAL", "REVIEW", "RUNNING",
             "CLAIMED", "READY", "WAITING_FOR_WAKE", "MERGED"]
    for st in order:
        rows = sorted(by_state.get(st, []), key=lambda r: (r["priority"], r["task"]))
        if not rows:
            continue
        lines += ["## %s (%d)" % (st, len(rows)), "",
                  "| task | pri | owner | title | acceptance | reviewer | gate | idle |",
                  "|---|---|---|---|---|---|---|---|"]
        for t in rows:
            lines.append("| %s | %s | %s | %s | %s | %s | %s | %dm |" % (
                t["task"], t["priority"], t["owner"], t["title"],
                t["acceptance"], t["reviewer"], t["gate"], age_min(t)))
        lines.append("")
    lines += ["## Roster", "", "| agent | platform | domain |", "|---|---|---|"]
    for name, (plat, dom) in ROSTER.items():
        lines.append("| %s | %s | %s |" % (name, plat, dom))
    lines += ["", "## Doctrine", ""] + ["- " + d for d in DOCTRINE] + [""]
    open(BOARD_MD, "w").write("\n".join(lines))
    print("wrote %s  (%d tasks)" % (BOARD_MD, len(tasks)))
    return 0


def cmd_brief(a):
    """The command surface. Change the board, every agent's orders change."""
    agent = a.agent
    tasks = fold()
    mine = [t for t in tasks.values() if t["owner"] == agent and t["state"] not in TERMINAL]
    review = [t for t in tasks.values() if t["reviewer"] == agent and t["state"] == "REVIEW"]
    free = [t for t in tasks.values() if t["state"] == "READY"]
    g = next_gate()
    plat, dom = ROSTER.get(agent, ("-", "-"))
    w = []
    w.append("=" * 72)
    w.append("CADROS STANDING ORDER  -  %s  (%s)" % (agent, plat))
    w.append("issued %s" % ts())
    w.append("=" * 72)
    w.append("")
    w.append("YOUR DOMAIN: %s" % dom)
    if g:
        w.append("NEXT GATE  : %s %s (owner %s) in %dh%02dm - %s"
                 % (g[0], g[1], g[2], g[4] // 60, g[4] % 60, g[3]))
    w.append("")
    w.append("-- YOUR OPEN TASKS " + "-" * 53)
    if not mine:
        w.append("  none. Claim from UNCLAIMED below or report idle to LeBron.")
    for t in sorted(mine, key=lambda r: r["priority"]):
        w.append("  [%s] %s  %s" % (t["state"], t["task"], t["title"]))
        w.append("      acceptance: %s" % t["acceptance"])
        w.append("      artifact  : %s" % t["artifact"])
        w.append("      reviewer  : %s   gate: %s   idle: %dm"
                 % (t["reviewer"], t["gate"], age_min(t)))
        if t["note"]:
            w.append("      note      : %s" % t["note"])
    if review:
        w.append("")
        w.append("-- AWAITING YOUR REVIEW " + "-" * 48)
        for t in review:
            w.append("  %s %s  (built by %s) -> %s"
                     % (t["task"], t["title"], t["owner"], t["artifact"]))
    if free:
        w.append("")
        w.append("-- UNCLAIMED " + "-" * 59)
        for t in sorted(free, key=lambda r: r["priority"]):
            w.append("  %s [%s] %s   (claim: cadops claim %s --agent \"%s\")"
                     % (t["task"], t["priority"], t["title"], t["task"], agent))
    w.append("")
    w.append("-- HOW YOU REPORT " + "-" * 54)
    w.append("  python3 ops/cadops.py claim <TASK> --agent \"%s\"" % agent)
    w.append("  python3 ops/cadops.py state <TASK> --to RUNNING --agent \"%s\"" % agent)
    w.append("  python3 ops/cadops.py state <TASK> --to REVIEW  --agent \"%s\" --artifact <path>" % agent)
    w.append("  python3 ops/cadops.py log --agent \"%s\" --task <TASK> \\" % agent)
    w.append("        --attempt \"<ten words>\" --outcome done|partial|dead|blocked \\")
    w.append("        --minutes <n> --artifact <path> --next \"<what you learned>\"")
    w.append("  A dead end logged is a contribution. Logging nothing is the only failure.")
    w.append("")
    w.append("-- DOCTRINE " + "-" * 60)
    for d in DOCTRINE:
        w.append("  " + d)
    w.append("=" * 72)
    print("\n".join(w))
    return 0


def cmd_next(a):
    """LeBron's view: what needs a decision right now."""
    tasks = fold()
    g = next_gate()
    print("=" * 72)
    if g:
        print("NEXT GATE: %s %s (owner %s) in %dh%02dm - %s" % (g[0], g[1], g[2], g[4] // 60, g[4] % 60, g[3]))
    print("=" * 72)
    def show(head, rows, why):
        if rows:
            print("\n%s  -- %s" % (head, why))
            for t in rows:
                print("  %-26s %-9s %-14s %s" % (t["task"], t["priority"], t["owner"], t["title"]))
    v = tasks.values()
    show("BLOCKED ON A HUMAN", [t for t in v if t["state"] == "BLOCKED_HUMAN"], "founders must decide; nothing else unblocks it")
    show("WAITING ON A REVIEWER", [t for t in v if t["state"] == "REVIEW"], "done but unsigned; cannot be cited yet")
    show("UNOWNED", [t for t in v if t["state"] == "READY"], "no accountable owner")
    show("STALE >45m", [t for t in v if t["state"] in LIVE and age_min(t) > 45], "stall gate: re-scope or state what done looks like")
    show("BLOCKED TECHNICAL", [t for t in v if t["state"] == "BLOCKED_TECHNICAL"], "route around or escalate")
    idle = [n for n in ROSTER if not any(t["owner"] == n and t["state"] in LIVE for t in v)]
    if idle:
        print("\nIDLE CAPACITY  -- unassigned agents burning the clock")
        for n in idle:
            print("  %-16s %-14s %s" % (n, ROSTER[n][0], ROSTER[n][1]))
    print()
    return 0


def cmd_gate(a):
    g = next_gate()
    if not g:
        print("no gate ahead")
        return 0
    hhmm, name, owner, cond, mins = g
    tasks = [t for t in fold().values() if t["gate"] == name and t["state"] not in TERMINAL]
    print("GATE %s %s - owner %s - %dh%02dm out" % (hhmm, name, owner, mins // 60, mins % 60))
    print("acceptance: %s" % cond)
    print("-" * 72)
    if not tasks:
        print("nothing outstanding against this gate.")
        return 0
    for t in sorted(tasks, key=lambda r: r["priority"]):
        print("  [%-18s] %-26s %-14s %s" % (t["state"], t["task"], t["owner"], t["title"]))
    unsigned = [t for t in tasks if t["state"] != "REVIEW" or t["reviewer"] == "-"]
    print("-" * 72)
    print("%d open against this gate." % len(tasks))
    return 1 if tasks else 0
