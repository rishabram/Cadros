#!/usr/bin/env python3
"""cadops - Cadros operating instrumentation.

Implements the rules in "Cadros Monitoring and Improvement Loop":
  - nine-field agent telemetry log (append-only)
  - 45-minute stall gate
  - six-line wave check
  - run records with frozen-input hashes
  - freeze guard (byte-identical re-execution check)
  - deck verification scan (every number -> run_id -> status label)

Standard library only. No network. Nothing here touches the engine.
"""

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timedelta, timezone

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(ROOT, "data")
TELEMETRY = os.path.join(DATA, "telemetry.log")
OPEN = os.path.join(DATA, "open.tsv")
RUNS = os.path.join(DATA, "runs.jsonl")
FIGURES = os.path.join(DATA, "deck_figures.tsv")
FREEZE = os.path.join(DATA, "freeze.json")
WAVES = os.path.join(DATA, "waves.tsv")

OUTCOMES = ("done", "partial", "dead", "blocked", "handoff")
LABELS = ("PASS", "MISS", "INPUTS", "QUARANTINED", "INVALID", "HELD")
BLOCKING_LABELS = ("INPUTS", "QUARANTINED", "INVALID")
STALL_MINUTES = 45

SEP = " | "


# ---------- time helpers ----------

def now():
    return datetime.now().astimezone()


def parse_ts(s):
    s = s.strip()
    for fmt in ("%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(s, fmt).astimezone()
        except ValueError:
            pass
    try:
        return datetime.fromisoformat(s).astimezone()
    except ValueError:
        raise SystemExit("bad timestamp: %s (use 2026-09-25T09:10)" % s)


def fmt_ts(dt):
    return dt.strftime("%Y-%m-%dT%H:%M %Z") or dt.strftime("%Y-%m-%dT%H:%M")


def minutes_between(a, b):
    return int(round((b - a).total_seconds() / 60.0 / 5.0) * 5)


# ---------- io helpers ----------

def ensure():
    os.makedirs(DATA, exist_ok=True)
    for p in (TELEMETRY, OPEN, RUNS, WAVES):
        if not os.path.exists(p):
            open(p, "a").close()


def append(path, line):
    with open(path, "a") as fh:
        fh.write(line.rstrip("\n") + "\n")


def read_lines(path):
    if not os.path.exists(path):
        return []
    with open(path) as fh:
        return [l.rstrip("\n") for l in fh if l.strip()]


def clean(s):
    return (s or "-").replace("|", "/").replace("\t", " ").strip() or "-"


def cap_words(s, n=10):
    w = clean(s).split()
    return " ".join(w[:n])


# ---------- telemetry ----------

def entry_line(ts, minutes, agent, task, attempt, outcome, artifact, nxt, gate):
    return SEP.join([
        fmt_ts(ts), str(minutes), clean(agent), clean(task),
        cap_words(attempt), outcome, clean(artifact), clean(nxt), clean(gate),
    ])


def parse_entry(line):
    parts = [p.strip() for p in line.split("|")]
    if len(parts) != 9:
        return None
    keys = ["ts", "minutes", "agent", "task", "attempt", "outcome", "artifact", "next", "gate"]
    d = dict(zip(keys, parts))
    try:
        d["minutes"] = int(d["minutes"])
    except ValueError:
        d["minutes"] = 0
    d["_ts"] = parse_ts(d["ts"].rsplit(" ", 1)[0]) if d["ts"] else now()
    return d


def cmd_log(a):
    ensure()
    if a.outcome not in OUTCOMES:
        raise SystemExit("outcome must be one of: %s" % ", ".join(OUTCOMES))
    ts = parse_ts(a.started) if a.started else now()
    line = entry_line(ts, a.minutes, a.agent, a.task, a.attempt, a.outcome,
                      a.artifact, a.next, a.gate)
    append(TELEMETRY, line)
    _close_open(a.agent, a.task)
    print(line)
    if a.outcome == "dead":
        print("logged as dead - that is a contribution, it stops the next lane repeating it")


def cmd_start(a):
    ensure()
    ts = parse_ts(a.started) if a.started else now()
    _close_open(a.agent, a.task)
    append(OPEN, "\t".join([clean(a.agent), clean(a.task), cap_words(a.attempt),
                            fmt_ts(ts), ""]))
    print("open: %s / %s since %s" % (a.agent, a.task, fmt_ts(ts)))


def _open_rows():
    rows = []
    for l in read_lines(OPEN):
        p = l.split("\t")
        while len(p) < 5:
            p.append("")
        rows.append(p[:5])
    return rows


def _write_open(rows):
    with open(OPEN, "w") as fh:
        for r in rows:
            fh.write("\t".join(r) + "\n")


def _close_open(agent, task):
    rows = _open_rows()
    keep = [r for r in rows if not (r[0] == clean(agent) and r[1] == clean(task))]
    if len(keep) != len(rows):
        _write_open(keep)


def cmd_end(a):
    ensure()
    rows = _open_rows()
    match = [r for r in rows if r[0] == clean(a.agent) and (a.task is None or r[1] == clean(a.task))]
    if not match:
        raise SystemExit("no open entry for %s%s" % (a.agent, "" if a.task is None else " / " + a.task))
    r = match[-1]
    started = parse_ts(r[3].rsplit(" ", 1)[0])
    mins = max(5, minutes_between(started, now()))
    if a.outcome not in OUTCOMES:
        raise SystemExit("outcome must be one of: %s" % ", ".join(OUTCOMES))
    line = entry_line(started, mins, r[0], r[1], a.attempt or r[2], a.outcome,
                      a.artifact, a.next, a.gate)
    append(TELEMETRY, line)
    _write_open([x for x in rows if x is not r])
    print(line)


def cmd_stall(a):
    """45-minute stall gate. Safe to run on an interval."""
    ensure()
    rows = _open_rows()
    fired = []
    t = now()
    for r in rows:
        started = parse_ts(r[3].rsplit(" ", 1)[0])
        age = minutes_between(started, t)
        last = parse_ts(r[4].rsplit(" ", 1)[0]) if r[4] else started
        since_last = minutes_between(last, t)
        if age >= STALL_MINUTES and since_last >= STALL_MINUTES:
            line = entry_line(started, age, r[0], r[1], r[2], "partial", "-",
                              "STALL: state what done looks like or re-scope", "stall")
            append(TELEMETRY, line)
            r[4] = fmt_ts(t)
            fired.append(line)
    _write_open(rows)
    if fired:
        print("stall gate fired on %d lane(s):" % len(fired))
        for f in fired:
            print("  " + f)
        return 1
    print("no stalls (%d lane(s) open, threshold %dm)" % (len(rows), STALL_MINUTES))
    return 0


# ---------- wave check ----------

def _entries_since(since):
    out = []
    for l in read_lines(TELEMETRY):
        e = parse_entry(l)
        if e and (since is None or e["_ts"] >= since):
            out.append(e)
    return out


def cmd_wave(a):
    ensure()
    since = None
    if a.since:
        since = parse_ts(a.since)
    elif a.hours:
        since = now() - timedelta(hours=a.hours)
    else:
        marks = read_lines(WAVES)
        if marks:
            since = parse_ts(marks[-1].split("\t")[0].rsplit(" ", 1)[0])
        else:
            since = now() - timedelta(hours=6)

    es = _entries_since(since)
    lanes = sorted({e["agent"] for e in es})
    total = sum(e["minutes"] for e in es)
    dead = [e for e in es if e["outcome"] == "dead"]
    dead_min = sum(e["minutes"] for e in dead)
    worst = max(dead, key=lambda e: e["minutes"], default=None)
    stalls = [e for e in es if e["gate"] == "stall"]
    open_tasks = {(r[0], r[1]) for r in _open_rows()}
    stall_open = [e for e in stalls if (e["agent"], e["task"]) in open_tasks]
    blocked = [e for e in es if e["outcome"] == "blocked" or (e["gate"] not in ("-", "stall") and e["gate"])]
    arts = {}
    for e in es:
        if e["artifact"] != "-":
            arts.setdefault(e["artifact"], set()).add(e["agent"])
    collisions = {k: v for k, v in arts.items() if len(v) > 1}

    print("WAVE CHECK  since %s" % fmt_ts(since))
    print("1. lanes: %d active (%s) | %d min logged" % (len(lanes), ", ".join(lanes) or "-", total))
    print("2. dead: %d min across %d line(s)%s" % (
        dead_min, len(dead),
        " | worst: %s %dm (%s)" % (worst["agent"], worst["minutes"], worst["attempt"]) if worst else ""))
    print("3. stalls: %d fired, %d still running" % (len(stalls), len(stall_open)))
    print("4. blocked on human: %s" % (
        ", ".join("%s %s (%dm)" % (e["agent"], e["gate"], e["minutes"]) for e in blocked) or "none"))
    print("5. shared artifacts: %s" % (
        "; ".join("%s <- %s" % (k, "+".join(sorted(v))) for k, v in collisions.items()) or "none"))

    if stall_open:
        rec = "re-scope the stalled lane(s): %s" % ", ".join(sorted({e["agent"] for e in stall_open}))
    elif blocked:
        rec = "clear the human queue first: %s" % ", ".join(sorted({e["gate"] for e in blocked}))
    elif collisions:
        rec = "re-assign - two lanes are editing the same artifact"
    elif dead_min > total * 0.4 and total:
        rec = "re-scope - more than 40%% of logged time is dead"
    else:
        rec = "continue"
    print("6. recommendation: %s" % rec)

    if a.mark:
        append(WAVES, "%s\t%s" % (fmt_ts(now()), a.mark))
        print("(wave boundary marked: %s)" % a.mark)
    return 0


# ---------- runs, freeze, verify ----------

def hash_paths(paths):
    h = hashlib.sha256()
    files = []
    for p in paths:
        if os.path.isdir(p):
            for base, _, names in os.walk(p):
                for n in sorted(names):
                    files.append(os.path.join(base, n))
        elif os.path.exists(p):
            files.append(p)
        else:
            raise SystemExit("input not found: %s" % p)
    for f in sorted(files):
        h.update(os.path.relpath(f, os.getcwd()).encode())
        with open(f, "rb") as fh:
            for chunk in iter(lambda: fh.read(1 << 16), b""):
                h.update(chunk)
    return h.hexdigest()[:16], len(files)


def cmd_hash(a):
    digest, n = hash_paths(a.paths)
    print("%s  (%d file(s))" % (digest, n))


def _runs():
    out = []
    for l in read_lines(RUNS):
        try:
            out.append(json.loads(l))
        except json.JSONDecodeError:
            pass
    return out


def cmd_run(a):
    ensure()
    if a.label not in LABELS:
        raise SystemExit("status label must be one of: %s" % ", ".join(LABELS))
    digest = a.inputs_hash
    if a.inputs:
        digest, _ = hash_paths(a.inputs)
    rec = {
        "run_id": a.run_id,
        "commit": a.commit or "-",
        "inputs_hash": digest or "-",
        "ranking_mode": a.ranking_mode or "-",
        "started": a.started or fmt_ts(now()),
        "finished": fmt_ts(now()),
        "status_label": a.label,
        "artifact": a.artifact or "-",
        "note": a.note or "",
    }
    if any(r["run_id"] == a.run_id for r in _runs()):
        raise SystemExit("run_id already recorded and run ids are never reused: %s" % a.run_id)
    append(RUNS, json.dumps(rec, sort_keys=True))
    print(json.dumps(rec, sort_keys=True))


def cmd_freeze(a):
    ensure()
    if a.check:
        if not os.path.exists(FREEZE):
            raise SystemExit("no freeze recorded")
        f = json.load(open(FREEZE))
        digest, n = hash_paths(f["inputs"])
        ok = digest == f["inputs_hash"]
        print("freeze %s (%s)" % (f["label"], f["at"]))
        print("  baseline run : %s" % f["baseline_run"])
        print("  commit       : %s" % f["commit"])
        print("  inputs_hash  : %s recorded / %s now (%d files)" % (f["inputs_hash"], digest, n))
        print("  VERDICT      : %s" % ("INTACT - inputs unchanged" if ok
                                       else "BROKEN - inputs moved since freeze; gate fails"))
        return 0 if ok else 1
    if not a.inputs:
        raise SystemExit("--inputs required to set a freeze")
    digest, n = hash_paths(a.inputs)
    rec = {"label": a.label or "freeze", "at": fmt_ts(now()), "commit": a.commit or "-",
           "baseline_run": a.baseline_run or "-", "inputs": a.inputs,
           "inputs_hash": digest, "files": n}
    json.dump(rec, open(FREEZE, "w"), indent=2, sort_keys=True)
    print("frozen: %s  inputs_hash=%s (%d files)" % (rec["label"], digest, n))
    print("engine changes are now defects until this freeze is lifted")


def cmd_verify(a):
    ensure()
    runs = {r["run_id"]: r for r in _runs()}
    rows = []
    for l in read_lines(FIGURES):
        if l.startswith("#"):
            continue
        p = [x.strip() for x in l.split("\t") if x.strip() != ""]
        while len(p) < 3:
            p.append("")
        rows.append(p[:3])

    blockers = 0
    warn = 0
    print("%-30s %-10s %-24s %-13s %-16s %s" % ("FIGURE", "VALUE", "RUN_ID", "LABEL", "INPUTS_HASH", "STATUS"))
    print("-" * 104)
    for fig, val, rid in rows:
        r = runs.get(rid)
        if not r:
            status, label, ih = "UNSOURCED - BLOCKS GATE", "-", "-"
            blockers += 1
        elif r["status_label"] in BLOCKING_LABELS:
            status, label, ih = "DO NOT CITE", r["status_label"], r["inputs_hash"]
            blockers += 1
        elif r["status_label"] == "HELD":
            status, label, ih = "CAUTION - not adopted", r["status_label"], r["inputs_hash"]
            warn += 1
        else:
            status, label, ih = "ok", r["status_label"], r["inputs_hash"]
        print("%-30s %-10s %-24s %-13s %-16s %s" % (fig[:30], val[:10], (rid or "-")[:24], label, ih, status))
    print("-" * 104)
    print("%d figure(s) | %d blocker(s) | %d caution(s)" % (len(rows), blockers, warn))
    if blockers:
        print("GATE FAILS: every deck number needs a run_id with a citable label.")
        return 1
    print("GATE PASSES: every deck number resolves to a recorded run.")
    return 0


def cmd_status(a):
    ensure()
    es = _entries_since(now() - timedelta(hours=24))
    print("telemetry : %d line(s) in last 24h, %d min logged" % (len(es), sum(e["minutes"] for e in es)))
    print("open lanes: %d" % len(_open_rows()))
    print("runs      : %d recorded" % len(_runs()))
    if os.path.exists(FREEZE):
        f = json.load(open(FREEZE))
        print("freeze    : %s at %s (baseline %s)" % (f["label"], f["at"], f["baseline_run"]))
    else:
        print("freeze    : none")


def main():
    p = argparse.ArgumentParser(prog="cadops", description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("log", help="append one nine-field telemetry line")
    s.add_argument("--agent", required=True)
    s.add_argument("--task", default="-")
    s.add_argument("--attempt", required=True, help="ten words or fewer")
    s.add_argument("--outcome", required=True, choices=OUTCOMES)
    s.add_argument("--minutes", type=int, required=True)
    s.add_argument("--artifact", default="-")
    s.add_argument("--next", default="-")
    s.add_argument("--gate", default="-")
    s.add_argument("--started")
    s.set_defaults(fn=cmd_log)

    s = sub.add_parser("start", help="open a lane (the stall gate watches it)")
    s.add_argument("--agent", required=True)
    s.add_argument("--task", default="-")
    s.add_argument("--attempt", required=True)
    s.add_argument("--started")
    s.set_defaults(fn=cmd_start)

    s = sub.add_parser("end", help="close an open lane and write its line")
    s.add_argument("--agent", required=True)
    s.add_argument("--task")
    s.add_argument("--outcome", required=True, choices=OUTCOMES)
    s.add_argument("--attempt")
    s.add_argument("--artifact", default="-")
    s.add_argument("--next", default="-")
    s.add_argument("--gate", default="-")
    s.set_defaults(fn=cmd_end)

    s = sub.add_parser("stall", help="45-minute stall gate; run on an interval")
    s.set_defaults(fn=cmd_stall)

    s = sub.add_parser("wave", help="six-line wave check")
    s.add_argument("--since")
    s.add_argument("--hours", type=float)
    s.add_argument("--mark", help="mark this moment as a wave boundary")
    s.set_defaults(fn=cmd_wave)

    s = sub.add_parser("run", help="record a run")
    s.add_argument("run_id")
    s.add_argument("--label", required=True, choices=LABELS)
    s.add_argument("--commit")
    s.add_argument("--inputs", nargs="*", help="paths to hash as the frozen input set")
    s.add_argument("--inputs-hash")
    s.add_argument("--ranking-mode")
    s.add_argument("--started")
    s.add_argument("--artifact")
    s.add_argument("--note")
    s.set_defaults(fn=cmd_run)

    s = sub.add_parser("hash", help="hash an input set")
    s.add_argument("paths", nargs="+")
    s.set_defaults(fn=cmd_hash)

    s = sub.add_parser("freeze", help="set or check the freeze guard")
    s.add_argument("--inputs", nargs="*")
    s.add_argument("--commit")
    s.add_argument("--baseline-run")
    s.add_argument("--label")
    s.add_argument("--check", action="store_true")
    s.set_defaults(fn=cmd_freeze)

    s = sub.add_parser("verify", help="deck verification scan")
    s.set_defaults(fn=cmd_verify)

    s = sub.add_parser("status", help="one-screen state")
    s.set_defaults(fn=cmd_status)

    a = p.parse_args()
    sys.exit(a.fn(a) or 0)


if __name__ == "__main__":
    main()
