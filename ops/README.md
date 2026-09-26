# Cadros ops — instrumentation for progress, telemetry, and gates

Implements the rules in the Drive document **Cadros Monitoring and Improvement Loop**.
Standard library Python only. No network calls. Nothing here touches the engine.

    ops/cadops.py       the CLI
    ops/watch.sh        stall-gate watcher (interval loop)
    ops/data/           append-only state (telemetry.log, runs.jsonl, deck_figures.tsv, freeze.json)
    .claude/commands/   /verify /wave /logwork /freeze

## The four things it automates

| Problem | Command | What it produces |
| --- | --- | --- |
| A number in the deck no one can trace | `cadops verify` | every figure next to its run_id, label, inputs hash; exits non-zero if any figure is UNSOURCED or DO NOT CITE |
| An agent lane burning an hour on a dead branch | `cadops log` / `start` / `end` | one nine-field line per task, `dead` explicitly safe to log |
| A lane grinding on something under-specified | `cadops stall` (or `ops/watch.sh`) | fires at 45 minutes, writes the line itself, asks what "done" looks like |
| The engine moving during a freeze | `cadops freeze --check` | re-hashes the frozen inputs and fails the gate if a byte moved |

## Daily use

    python3 ops/cadops.py start  --agent "D-Wade" --task CADROS-... --attempt "mix-prior blend under gates"
    python3 ops/cadops.py end    --agent "D-Wade" --outcome done --artifact e291d6c --next "moves zero picks"
    python3 ops/cadops.py log    --agent "TMac Worker 4" --attempt "searched records for 2nd AF parcel" \
                                 --outcome dead --minutes 35 --next "no second parcel exists"
    python3 ops/cadops.py wave --hours 8 --mark "wave 3"
    python3 ops/cadops.py verify
    python3 ops/cadops.py status

`start` opens a lane so the stall gate can see it. `log` is for work already finished.
`end` computes the minutes itself.

## Before a demo or gate

    python3 ops/cadops.py run RUN-<date>-<name> --label PASS --commit <sha> \
        --inputs <paths...> --ranking-mode baseline --artifact <link>
    python3 ops/cadops.py freeze --inputs <paths...> --commit <sha> \
        --baseline-run RUN-<date>-<name> --label "gate-2000"
    python3 ops/cadops.py verify        # must exit 0
    python3 ops/cadops.py freeze --check # must say INTACT

From the moment the freeze is set, no change to ranking, scoring, or generation. Instrumentation,
CI, dashboard, and deck work continue. A code assistant pointed at the engine inside the freeze
window has broken the gate, and `freeze --check` will say so.

## Status labels (closed list)

`PASS` `MISS` `INPUTS` `QUARANTINED` `INVALID` `HELD`

`INPUTS` is not an engine miss and never counts as one. `HELD` means the result is real and the
change was deliberately not adopted. Unknown never passes.

## Design notes

- **Append-only.** `telemetry.log` and `runs.jsonl` are never edited. A wrong line is corrected by
  a new line, not a rewrite.
- **`dead` is a contribution.** Dead entries are never counted against a lane. A lane with zero
  dead entries over a long stretch is under-reporting, not excelling.
- **Run ids are never reused.** `cadops run` refuses a duplicate.
- **The wave check is six lines.** If it grows, the format is wrong, not the wave.
- **No daemons installed.** `ops/watch.sh` runs in the foreground in a terminal you can close.
