# Fitness Buddy data files

All data lives in a `fitness-buddy/` folder inside the user's current working folder. Create the folder and any missing file on first write. Never delete user data; append or edit in place.

## `profile.md`
Markdown with these headings. Fill only what the user has told you; mark unknowns `?`.

```
# Profile
- Name:
- Age:
- Sex:
- Height:
- Weight:            (with unit and date measured)
- Units:             metric | imperial
- Goal:              strength | hypertrophy | fat loss | endurance | general fitness
- Experience:        beginner | intermediate | advanced
- Days per week:
- Session length:    (minutes)
- Equipment:         full gym | home dumbbells | bodyweight | ...
- Injuries / limits:
- Diet preferences:  (vegetarian, allergies, dislikes)

# Targets
- Calories:
- Protein / Carbs / Fat (g):

# Current plan
- File: plans/<plan-file>.md
- Started:
```

## `plans/<YYYY-MM-DD>-<slug>.md`
One file per plan. Week overview table, then one section per day listing exercise, sets x reps, target load or RPE, rest, and notes. End with a progression rule.

## `log.csv`
One row per working set. Header:

```
date,session,exercise,set,reps,weight,unit,rpe,notes
```

- `date`: YYYY-MM-DD
- `session`: day label from the plan (e.g. `Upper A`) or `cardio`, `ad-hoc`
- Cardio: put duration in minutes in `reps`, distance in `weight`, unit `km`/`mi`
- Bodyweight sets: `weight` 0, unit `bw`

## `checkins.csv`
One row per day. Header:

```
date,sleep_h,energy_1to5,soreness_1to5,mood_1to5,bodyweight,trained,steps,notes
```

`trained` is `yes`/`no`/`rest`. Planned rest days count toward the streak.

## `food.csv` (optional, only if the user tracks food)
```
date,meal,item,calories,protein_g,carbs_g,fat_g
```
