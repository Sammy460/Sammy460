---
name: workout-plan
description: >
  This skill should be used when the user asks to "make me a workout plan",
  "build a training program", "plan my week of workouts", "I want to get stronger / build muscle / lose fat",
  "adjust my plan", "swap an exercise", or asks what workout to do today. Builds and saves
  personalized, progressive training plans from the user's goal, level, schedule and equipment.
metadata:
  version: "0.1.0"
---

# Workout Plan

Build a training plan that fits the user's real constraints, save it, and keep it current.

## 1. Load context

1. Read `fitness-buddy/profile.md` if it exists. Data layout: `references/data-format.md`.
2. Read the last 2 weeks of `fitness-buddy/log.csv` and `fitness-buddy/checkins.csv` if present.
3. Collect only missing essentials, in one AskUserQuestion call if possible:
   - Goal (strength, hypertrophy, fat loss, endurance, general fitness)
   - Experience (beginner < 6 months consistent training, intermediate, advanced)
   - Days per week and minutes per session
   - Equipment available
   - Injuries or movements to avoid
4. Save new answers to `profile.md`.

## 2. Choose a structure

Pick the split from days per week. Full rules and templates: `references/programming.md`.

| Days | Default split |
|------|---------------|
| 2 | Full body A / B |
| 3 | Full body A / B / C, or Upper / Lower / Full |
| 4 | Upper / Lower x2 |
| 5 | Upper / Lower / Push / Pull / Legs |
| 6 | Push / Pull / Legs x2 |

Adjust for goal:
- Strength: compound lifts first, 3-6 reps, RPE 7-9, rest 2-4 min.
- Hypertrophy: 6-15 reps, 10-20 hard sets per muscle per week, rest 1-2.5 min.
- Fat loss: hypertrophy-style lifting to keep muscle, plus 2-3 cardio sessions or a daily step target.
- Endurance: 3+ cardio sessions with one long, one tempo or interval, plus 2 short strength sessions.
- General fitness: 2-3 full-body sessions plus 150 min/week moderate cardio.

Fit every session in the stated time. Count about 2-3 min per working set including rest, plus 5-10 min warm-up.

## 3. Write the plan

Save to `fitness-buddy/plans/<YYYY-MM-DD>-<slug>.md` with:
1. Summary line: goal, split, weeks, sessions per week.
2. Week overview table (day, session name, focus).
3. One section per session: warm-up, then a table of exercise | sets x reps | load or RPE | rest | notes.
4. Progression rule (see `references/programming.md`), and a deload every 4-6 weeks for intermediate and advanced lifters.
5. Substitutions for each main lift, so the user can swap when equipment is busy.

Update the `Current plan` section in `profile.md`.

## 4. Present it

Show the week overview and the first session in chat. Point to the saved file for the rest. Ask whether to change anything before the user starts.

## Adjusting an existing plan

- "Swap X": offer 2-3 alternatives that hit the same muscles and movement pattern, respecting equipment and injuries. Edit the plan file.
- "What do I do today?": find the next session in the plan that has no log entries since the last occurrence, and show it with suggested loads from the log (last weight + progression rule).
- Stalled 3 sessions on a lift, or check-ins show low energy and high soreness for 3+ days: suggest a deload or a variation.

## Safety

- Do not program around pain. If the user reports sharp pain, numbness, chest pain, dizziness or a new injury, tell them to stop that movement and see a qualified professional.
- For beginners, older adults, pregnancy, or known heart, joint or metabolic conditions, recommend clearing the plan with a doctor or physio.
- Present the plan as general fitness guidance, not medical advice.
