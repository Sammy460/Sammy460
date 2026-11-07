---
name: workout-log
description: >
  This skill should be used when the user says "log my workout", "I did 3x8 bench at 60kg",
  "record today's session", "I ran 5k", "how's my progress", "show my PRs", "what did I lift last time",
  or pastes a workout to save. Records sets, reps, load and cardio, and reports progress,
  personal records and weekly volume.
metadata:
  version: "0.1.0"
---

# Workout Log

Turn whatever the user types into clean log rows, then reflect progress back.

## Logging

1. Parse free text into one row per set. Data layout: `references/data-format.md`.
   - `3x8 @ 60kg` = 3 rows, reps 8, weight 60, unit kg.
   - `8, 8, 7 @ 60` = 3 rows with those reps.
   - `ran 5k in 27 min` = session `cardio`, exercise `run`, reps 27, weight 5, unit km.
   - No date given: use today. "Yesterday": today minus 1.
   - No unit given: use the `Units` value in `profile.md`; if unknown, ask once and save it.
2. Normalize exercise names to the names used in the current plan or earlier log rows (e.g. "bench" = "Bench Press").
3. If anything is ambiguous (which exercise, which unit), ask before writing.
4. Append rows to `fitness-buddy/log.csv`, creating it with the header if missing.
5. Confirm with a compact summary: exercises, total sets, and any new PR.

## Personal records

After each log, check every logged exercise against its history:
- **Heaviest weight** for any reps.
- **Best estimated 1RM** with Epley: `weight x (1 + reps / 30)`, only for sets of 10 reps or fewer.
- **Rep PR** at a given weight.
- Cardio: longest distance, fastest pace.

Call out new PRs plainly, e.g. "New PR: Squat 100 kg x 5 (e1RM 117 kg)."

## Progress reports

On "how's my progress" or similar, read `log.csv` and report:
1. Sessions completed vs planned for the last 4 weeks (planned from the current plan file).
2. For each main lift: best e1RM 4 weeks ago vs now, and the change.
3. Weekly hard sets per muscle group for the last week. Flag groups under 10 sets for a hypertrophy goal.
4. Lifts with no progress in 3+ sessions, with one concrete suggestion each (deload 10%, change rep range, or swap variation).

Keep the report short: a table plus 2-3 takeaways. Offer a chart only if the user asks.

## Last time lookup

On "what did I do last time on X": show the most recent session's sets for X and the suggested next target using the plan's progression rule.
