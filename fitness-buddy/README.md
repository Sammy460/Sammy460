# Fitness Buddy

A Claude plugin that acts as your personal training buddy.

## What it does

| Skill | Ask things like | What happens |
|---|---|---|
| `workout-plan` | "Make me a 4-day plan to build muscle", "What do I do today?", "Swap deadlifts" | Builds a progressive plan that fits your goal, schedule and equipment, and saves it |
| `workout-log` | "Bench 3x8 at 60kg", "I ran 5k in 27 min", "Show my PRs", "How's my progress?" | Logs sets and cardio, spots personal records, reports progress and weekly volume |
| `nutrition` | "Set my macros", "How much protein do I need?", "Give me a high-protein day of meals" | Calculates calorie and macro targets, suggests meals, optional food log |
| `check-in` | "Check in", "What's my streak?", "How am I doing this week?" | 1-minute daily check-in, readiness-based training advice, streaks and weekly review |

## Your data

Everything is stored as plain files in a `fitness-buddy/` folder inside your working folder:

- `profile.md`: your goal, stats, equipment, targets and current plan
- `plans/`: saved training plans
- `log.csv`: every set you log
- `checkins.csv`: daily check-ins
- `food.csv`: food log (only if you use it)

Nothing is sent anywhere. You can open or edit the files yourself.

## Install

Claude Code:

```
/plugin marketplace add Sammy460/Sammy460
/plugin install fitness-buddy@sammy460
```

Cowork: install the packaged `fitness-buddy.plugin` file.

## Disclaimer

Fitness Buddy gives general fitness and nutrition guidance, not medical advice. Check with a doctor before starting a new program, especially with injuries or health conditions.
