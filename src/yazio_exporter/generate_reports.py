"""
Generate analysis summary and LLM-ready prompt from exported data.

Produces two files:
- analysis.md: Pre-computed statistics and metrics
- llm_prompt.txt: Compact data + prompt for pasting into any LLM
"""

import statistics
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from typing import Any

MIN_CALORIES = 800
TOP_FOODS_COUNT = 30
MAX_DAILY_ROWS = 400


# ── Shared helpers ────────────────────────────────────────────────


def _extract_daily_records(
    days_data: dict[str, Any],
    weight_data: dict[str, float],
    products_data: dict[str, Any],
    start: str,
    end: str,
) -> list[dict[str, Any]]:
    """Build compact daily records from raw export data."""
    records = []
    for date_str in sorted(days_data.keys()):
        if date_str < start or date_str > end:
            continue

        day_info = days_data[date_str]
        summary = day_info.get("daily_summary", {})
        meals = summary.get("meals", {})

        kcal = 0
        protein = 0
        carbs = 0
        fat = 0
        for m in meals.values():
            n = m.get("nutrients", {})
            kcal += n.get("energy.energy", 0) or 0
            protein += n.get("nutrient.protein", 0) or 0
            carbs += n.get("nutrient.carb", 0) or 0
            fat += n.get("nutrient.fat", 0) or 0

        w = weight_data.get(date_str)
        consumed = day_info.get("consumed", {}).get("products", [])

        dt = datetime.strptime(date_str, "%Y-%m-%d")
        dow = dt.strftime("%a")

        meal_cals = {}
        for mname, mdata in meals.items():
            meal_cals[mname] = mdata.get("nutrients", {}).get("energy.energy", 0) or 0

        goals = summary.get("goals", {})

        records.append(
            {
                "date": date_str,
                "dow": dow,
                "weekday": dt.weekday(),
                "kcal": round(kcal),
                "protein": round(protein),
                "carbs": round(carbs),
                "fat": round(fat),
                "weight": round(w, 1) if w else None,
                "products": consumed,
                "tracked": kcal >= MIN_CALORIES,
                "meal_cals": meal_cals,
                "cal_goal": goals.get("energy.energy", 0) or 0,
            }
        )

    return records


def _detect_active_range(days_data: dict[str, Any]) -> tuple[str | None, str | None]:
    """Find first and last date with meaningful tracking."""
    tracked = []
    for date_str, day_info in days_data.items():
        meals = day_info.get("daily_summary", {}).get("meals", {})
        total = sum((m.get("nutrients", {}).get("energy.energy", 0) or 0) for m in meals.values())
        if total >= MIN_CALORIES:
            tracked.append(date_str)
    if not tracked:
        return None, None
    tracked.sort()
    return tracked[0], tracked[-1]


def _get_products_map(products_data: dict[str, Any]) -> dict[str, Any]:
    """Normalize products data (may be nested under 'products' key)."""
    if "products" in products_data and isinstance(products_data["products"], dict):
        return products_data["products"]
    return products_data


def _food_stats(
    tracked_records: list[dict[str, Any]],
    products: dict[str, Any],
    count: int = TOP_FOODS_COUNT,
) -> list[dict[str, Any]]:
    """Aggregate food frequency and calorie contribution."""
    freq: Counter = Counter()
    total_cal: dict[str, float] = defaultdict(float)
    total_prot: dict[str, float] = defaultdict(float)

    for r in tracked_records:
        for p in r["products"]:
            pid = p.get("product_id", "")
            amount = p.get("amount", 0) or 0
            freq[pid] += 1
            prod = products.get(pid, {})
            nutr = prod.get("nutrients", {})
            total_cal[pid] += (nutr.get("energy.energy", 0) or 0) * amount
            total_prot[pid] += (nutr.get("nutrient.protein", 0) or 0) * amount

    rows = []
    for pid, cnt in freq.most_common(count):
        prod = products.get(pid, {})
        rows.append(
            {
                "name": prod.get("name", "unknown")[:50],
                "count": cnt,
                "total_kcal": round(total_cal[pid]),
                "total_protein": round(total_prot[pid]),
                "category": prod.get("category", "?"),
            }
        )
    return rows


# ── Analysis summary ──────────────────────────────────────────────


def generate_analysis(
    days_data: dict[str, Any],
    weight_data: dict[str, float],
    products_data: dict[str, Any],
    profile_data: dict[str, Any],
) -> str:
    """
    Generate a pre-computed analysis summary (Markdown).

    This computes all the numbers so it can be used as a quick reference
    or pasted into an LLM alongside the prompt for richer context.
    """
    start, end = _detect_active_range(days_data)
    if not start:
        return "# No tracked data found\n"

    products = _get_products_map(products_data)
    records = _extract_daily_records(days_data, weight_data, products, start, end)
    tracked = [r for r in records if r["tracked"]]

    if not tracked:
        return "# No tracked days found (all below 800 kcal)\n"

    total_days = len(records)
    weight_in_range = {r["date"]: r["weight"] for r in records if r["weight"]}

    # ── Profile ──
    height = profile_data.get("body_height", 175)
    diet = profile_data.get("diet", {})

    # ── Weight stats ──
    first_w = next((r["weight"] for r in records if r["weight"]), None)
    last_w = next((r["weight"] for r in reversed(records) if r["weight"]), None)
    all_weights = [w for w in weight_in_range.values()]
    min_w = min(all_weights) if all_weights else 0
    min_w_date = next((d for d, w in sorted(weight_in_range.items()) if w == min_w), "?")
    elapsed_days = (datetime.strptime(end, "%Y-%m-%d") - datetime.strptime(start, "%Y-%m-%d")).days
    weeks = elapsed_days / 7

    # ── Calorie stats ──
    cals = [r["kcal"] for r in tracked]
    prots = [r["protein"] for r in tracked]
    carbs_list = [r["carbs"] for r in tracked]
    fats = [r["fat"] for r in tracked]

    avg_cal = statistics.mean(cals)
    med_cal = statistics.median(cals)
    std_cal = statistics.stdev(cals) if len(cals) > 1 else 0

    # Macro split
    avg_p, avg_c, avg_f = statistics.mean(prots), statistics.mean(carbs_list), statistics.mean(fats)
    total_macro_cal = avg_p * 4 + avg_c * 4 + avg_f * 9
    prot_pct = (avg_p * 4 / total_macro_cal * 100) if total_macro_cal else 0
    carb_pct = (avg_c * 4 / total_macro_cal * 100) if total_macro_cal else 0
    fat_pct = (avg_f * 9 / total_macro_cal * 100) if total_macro_cal else 0

    # Goal adherence
    under_goal = sum(1 for r in tracked if r["cal_goal"] > 0 and r["kcal"] <= r["cal_goal"])
    with_goal = sum(1 for r in tracked if r["cal_goal"] > 0)

    # Monthly breakdown
    monthly_cals: dict[str, list[int]] = defaultdict(list)
    monthly_weights: dict[str, list[float]] = defaultdict(list)
    for r in tracked:
        monthly_cals[r["date"][:7]].append(r["kcal"])
    for d, w in weight_in_range.items():
        monthly_weights[d[:7]].append(w)

    # Day of week
    dow_cals: dict[int, list[int]] = defaultdict(list)
    for r in tracked:
        dow_cals[r["weekday"]].append(r["kcal"])
    dow_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

    weekday_avg = statistics.mean([r["kcal"] for r in tracked if r["weekday"] < 5])
    weekend_avg = (
        statistics.mean([r["kcal"] for r in tracked if r["weekday"] >= 5])
        if any(r["weekday"] >= 5 for r in tracked)
        else 0
    )

    # TDEE estimate
    weight_lost = (first_w - last_w) if first_w and last_w else 0
    total_deficit = weight_lost * 7700
    skipped_count = total_days - len(tracked)
    total_intake = sum(cals) + skipped_count * 300
    adj_avg_intake = total_intake / elapsed_days if elapsed_days else 0
    tdee = adj_avg_intake + (total_deficit / elapsed_days) if elapsed_days else 0

    # Food stats
    foods = _food_stats(tracked, products, 20)

    # Protein per kg
    avg_weight = statistics.mean(all_weights) if all_weights else 80
    prot_per_kg = avg_p / avg_weight if avg_weight else 0

    # Streaks
    dates_sorted = sorted([r["date"] for r in tracked])
    max_streak = 1
    cur_streak = 1
    for i in range(1, len(dates_sorted)):
        prev = datetime.strptime(dates_sorted[i - 1], "%Y-%m-%d")
        curr = datetime.strptime(dates_sorted[i], "%Y-%m-%d")
        if (curr - prev).days == 1:
            cur_streak += 1
            max_streak = max(max_streak, cur_streak)
        else:
            cur_streak = 1

    # ── Build output ──
    lines = []
    a = lines.append

    a("# Nutrition Data Analysis")
    a("")
    a("## Overview")
    a(f"- Period: {start} to {end} ({elapsed_days} days, {len(tracked)} tracked)")
    a(
        f"- Weight: {first_w} kg -> {last_w} kg (lost {weight_lost:.1f} kg, {weight_lost / weeks:.2f} kg/week)"
        if first_w and last_w
        else "- No weight data"
    )
    bmi_start = first_w / (height / 100) ** 2 if first_w else 0
    bmi_end = last_w / (height / 100) ** 2 if last_w else 0
    a(f"- BMI: {bmi_start:.1f} -> {bmi_end:.1f}")
    a(f"- All-time low: {min_w:.1f} kg ({min_w_date})")
    a(f"- Tracking consistency: {len(tracked)}/{total_days} days ({len(tracked) / total_days * 100:.0f}%)")
    a(f"- Longest tracking streak: {max_streak} days")
    a(f"- Estimated TDEE: ~{tdee:.0f} kcal")

    a("")
    a("## Calories")
    a(f"- Average: {avg_cal:.0f} kcal (median {med_cal:.0f}, std dev {std_cal:.0f})")
    if with_goal:
        a(f"- Under goal: {under_goal}/{with_goal} days ({under_goal / with_goal * 100:.0f}%)")
    a("")
    a("| Month | Avg kcal | Days |")
    a("|---|---|---|")
    for m in sorted(monthly_cals.keys()):
        a(f"| {m} | {statistics.mean(monthly_cals[m]):.0f} | {len(monthly_cals[m])} |")

    a("")
    a("## Weight by Month")
    a("| Month | Avg | Min | Max |")
    a("|---|---|---|---|")
    for m in sorted(monthly_weights.keys()):
        vals = monthly_weights[m]
        a(f"| {m} | {statistics.mean(vals):.1f} | {min(vals):.1f} | {max(vals):.1f} |")

    a("")
    a("## Macros")
    a(f"- Protein: {avg_p:.0f}g avg ({prot_pct:.0f}% of cal, {prot_per_kg:.2f} g/kg)")
    a(f"- Carbs: {avg_c:.0f}g avg ({carb_pct:.0f}% of cal)")
    a(f"- Fat: {avg_f:.0f}g avg ({fat_pct:.0f}% of cal)")
    p_pct = diet.get("protein_percentage", "?")
    c_pct = diet.get("carb_percentage", "?")
    f_pct = diet.get("fat_percentage", "?")
    a(f"- Goal split: P {p_pct}% / C {c_pct}% / F {f_pct}%")

    a("")
    a("## Day of Week")
    a("| Day | Avg kcal | Count |")
    a("|---|---|---|")
    for i in range(7):
        if dow_cals[i]:
            a(f"| {dow_names[i]} | {statistics.mean(dow_cals[i]):.0f} | {len(dow_cals[i])} |")
    a(f"\nWeekday avg: {weekday_avg:.0f} / Weekend avg: {weekend_avg:.0f}")

    a("")
    a("## Top Foods")
    a("| Food | Times | Total kcal | Category |")
    a("|---|---|---|---|")
    for f in foods:
        a(f"| {f['name']} | {f['count']} | {f['total_kcal']} | {f['category']} |")

    a("")
    a("## Extreme Days")
    sorted_by_cal = sorted(tracked, key=lambda x: x["kcal"])
    a("### Lowest")
    for r in sorted_by_cal[:5]:
        a(f"- {r['date']}: {r['kcal']} kcal (P:{r['protein']}g C:{r['carbs']}g F:{r['fat']}g)")
    a("### Highest")
    for r in sorted_by_cal[-5:]:
        a(f"- {r['date']}: {r['kcal']} kcal (P:{r['protein']}g C:{r['carbs']}g F:{r['fat']}g)")

    a("")
    return "\n".join(lines)


# ── LLM prompt ────────────────────────────────────────────────────

_LLM_INSTRUCTIONS = """\
You are a sports nutritionist reviewing a client's food diary. \
Your job is to find what they CANNOT see themselves.

# Rules
- Do NOT restate averages or summarize the CSV. The client can read numbers.
- Every claim must cite specific dates or date ranges from the data.
- Be blunt. If something is bad, say it directly.

# What to look for
1. **Binge-recovery cycles**: after days >2500 kcal, does the client compensate \
the next day or spiral into multi-day overeating? Cite the actual sequences.
2. **Plateau mechanics**: find periods where weight stalled. What was the calorie \
intake during stalls vs during steady loss? Calculate the threshold.
3. **TDEE**: compute from (total weight change x 7700 kcal/kg) / days + avg intake. \
This is their real maintenance — compare it to their app's calorie goal.
4. **Trigger patterns**: do binges cluster on certain weekdays? After low-calorie \
days? After specific foods?
5. **Protein reality check**: at their weight, is protein intake adequate for \
muscle preservation in a deficit? (target: 1.6-2.0 g/kg). How often do they \
actually hit that vs fall short?
6. **Food crutches**: is there a food they lean on too heavily? What happens to \
their macros on days with vs without it?
7. **Monthly character**: describe each month in ONE sentence — what made it \
different from the others.
8. **The single biggest lever**: if they could change ONE habit, what would make \
the most impact? Back it with numbers from their data.

# Output format
Start with a 2-sentence verdict on the overall journey.
Then give 8-12 numbered insights (each must reference specific data).
End with exactly 3 recommendations ranked by impact.

Do not pad with generic nutrition advice. Only say things THIS data supports.\
"""


def generate_llm_prompt(
    days_data: dict[str, Any],
    weight_data: dict[str, float],
    products_data: dict[str, Any],
    profile_data: dict[str, Any],
) -> str:
    """
    Generate a paste-ready LLM prompt with compact data.

    The output is a single text file that a user can copy-paste into
    any LLM (ChatGPT, DeepSeek, Claude, Gemini) for analysis.
    """
    start, end = _detect_active_range(days_data)
    if not start:
        return "No tracked data found.\n"

    products = _get_products_map(products_data)
    records = _extract_daily_records(days_data, weight_data, products, start, end)
    tracked = [r for r in records if r["tracked"]]

    if not tracked:
        return "No tracked days found.\n"

    # ── Profile section ──
    sex = profile_data.get("sex", "unknown")
    height = profile_data.get("body_height", "?")
    dob = profile_data.get("date_of_birth", "")
    goal = profile_data.get("goal", "unknown")
    diet = profile_data.get("diet", {})
    p = diet.get("protein_percentage", "?")
    c = diet.get("carb_percentage", "?")
    f_goal = diet.get("fat_percentage", "?")
    macro_goal = f"P {p}% / C {c}% / F {f_goal}%"
    target_rate = profile_data.get("weight_change_per_week", "?")

    age = "?"
    if dob:
        try:
            born = datetime.strptime(dob, "%Y-%m-%d")
            age = (datetime.now() - born).days // 365
        except ValueError:
            pass

    total_days = len(records)
    first_weight = next((r["weight"] for r in records if r["weight"]), None)
    last_weight = next((r["weight"] for r in reversed(records) if r["weight"]), None)

    lines = []
    a = lines.append

    a(_LLM_INSTRUCTIONS)
    a("")
    a("# Client Profile")
    a(f"- Sex: {sex}, Age: {age}, Height: {height}cm")
    a(f"- Goal: {goal} weight (target {target_rate} kg/week)")
    a(f"- Macro goal: {macro_goal}")
    a(f"- Tracking period: {start} to {end} ({total_days} days, {len(tracked)} tracked)")
    if first_weight and last_weight:
        a(f"- Weight: {first_weight} kg -> {last_weight} kg")
    a("")

    # ── Daily or weekly data ──
    use_weekly = len(tracked) > MAX_DAILY_ROWS

    if use_weekly:
        a("# Weekly Data")
        a("(averaged per tracked day in that week)")
        a("week_start,avg_kcal,avg_protein_g,avg_carbs_g,avg_fat_g,weight_kg,tracked/total")
        weekly = _weekly_aggregate(records)
        for w in weekly:
            wt = w["weight"] if w["weight"] else ""
            a(
                f"{w['week']},{w['avg_kcal']},{w['avg_protein']},{w['avg_carbs']},"
                f"{w['avg_fat']},{wt},{w['tracked']}/{w['total']}"
            )
    else:
        a("# Daily Data")
        a("(days <800 kcal marked SKIP = barely/not tracked)")
        a("date,day,kcal,protein_g,carbs_g,fat_g,weight_kg")
        for r in records:
            wt = r["weight"] if r["weight"] else ""
            if not r["tracked"]:
                a(f"{r['date']},{r['dow']},SKIP,,,,{wt}")
            else:
                a(f"{r['date']},{r['dow']},{r['kcal']},{r['protein']},{r['carbs']},{r['fat']},{wt}")

    a("")

    # ── Top foods ──
    foods = _food_stats(tracked, products)
    a(f"# Top {len(foods)} Most Eaten Foods")
    a("food_name,times_eaten,total_kcal,total_protein_g,category")
    for f in foods:
        name = f["name"].replace(",", ";")
        a(f"{name},{f['count']},{f['total_kcal']},{f['total_protein']},{f['category']}")

    return "\n".join(lines)


def _weekly_aggregate(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Collapse daily records into weekly summaries."""
    weeks: dict[str, dict] = defaultdict(
        lambda: {
            "kcal": [],
            "protein": [],
            "carbs": [],
            "fat": [],
            "weight_start": None,
            "weight_end": None,
            "tracked": 0,
            "total": 0,
        }
    )

    for r in records:
        dt = datetime.strptime(r["date"], "%Y-%m-%d")
        week_start = dt - timedelta(days=dt.weekday())
        key = week_start.strftime("%Y-%m-%d")
        w = weeks[key]
        w["total"] += 1
        if r["tracked"]:
            w["tracked"] += 1
            w["kcal"].append(r["kcal"])
            w["protein"].append(r["protein"])
            w["carbs"].append(r["carbs"])
            w["fat"].append(r["fat"])
        if r["weight"]:
            if w["weight_start"] is None:
                w["weight_start"] = r["weight"]
            w["weight_end"] = r["weight"]

    def avg(lst):
        return round(sum(lst) / len(lst)) if lst else 0

    rows = []
    for week_start in sorted(weeks.keys()):
        w = weeks[week_start]
        if not w["kcal"]:
            continue
        rows.append(
            {
                "week": week_start,
                "avg_kcal": avg(w["kcal"]),
                "avg_protein": avg(w["protein"]),
                "avg_carbs": avg(w["carbs"]),
                "avg_fat": avg(w["fat"]),
                "weight": w["weight_end"],
                "tracked": w["tracked"],
                "total": w["total"],
            }
        )

    return rows
