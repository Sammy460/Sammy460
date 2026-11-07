---
name: nutrition
description: >
  This skill should be used when the user asks "how many calories should I eat",
  "set my macros", "how much protein do I need", "give me meal ideas", "make a meal plan",
  "what should I eat after training", or wants to log food. Sets calorie and macro targets
  from the user's profile and goal, suggests meals that hit them, and optionally tracks intake.
metadata:
  version: "0.1.0"
---

# Nutrition

Give simple, sustainable targets and practical meals. Accuracy within ~10% is fine; consistency matters more.

## 1. Set targets

1. Read `fitness-buddy/profile.md`. Data layout: `references/data-format.md`.
2. Need: age, sex, height, weight, activity level (training days per week plus daily steps or job type), goal, diet preferences. Ask only for what is missing.
3. Calculate with `references/nutrition-math.md`: BMR (Mifflin-St Jeor), then TDEE, then goal adjustment, then macros.
4. Show the result as a short table: calories, protein, carbs, fat, plus one line on how it was derived.
5. Save to the `Targets` section of `profile.md`.

## 2. Meal ideas and plans

- Respect diet preferences, allergies and dislikes from the profile.
- For a day plan: 3-4 meals plus optional snack, each with approximate calories and protein, and a total row. Hit protein within ±10 g and calories within ±100 kcal.
- Prefer common, cheap, quick foods. Give portions in the user's units.
- Pre-workout (1-3 h before): carbs plus some protein, low fat and fiber. Post-workout: 20-40 g protein plus carbs within a few hours.

## 3. Food tracking (only if the user wants it)

- Parse "had 2 eggs and toast" into rows with estimated macros. Append to `fitness-buddy/food.csv`.
- On request, show today's totals vs targets and what is left.
- State that numbers are estimates.

## 4. Adjust over time

Every 2-3 weeks, or when asked, compare average bodyweight from `checkins.csv` with the goal:
- Fat loss target: lose 0.5-1% bodyweight per week. Slower: cut 100-200 kcal. Faster with low energy: add 100-200 kcal.
- Muscle gain: gain 0.25-0.5% per week. Adjust the same way.
Use weekly averages, not single weigh-ins.

## Safety

- Never go below 1,200 kcal (women) or 1,500 kcal (men) without medical supervision.
- Do not give targets to anyone who says they are under 18, pregnant or breastfeeding, or has diabetes, kidney disease, or an eating disorder history. Suggest a registered dietitian or doctor instead, and offer general healthy-eating tips only.
- If the user shows signs of disordered eating (extreme restriction, purging, distress about food), respond with care, do not give deficit numbers, and point to professional support.
- Present all of this as general guidance, not medical advice.
