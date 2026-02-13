# yazio-exporter

Export all your [Yazio](https://www.yazio.com/) nutrition, body, and exercise data to JSON, CSV, or SQLite.

## Features

- **Full data coverage** — daily diary, consumed items (products + recipes), weight & body measurements, exercises, water intake, micronutrients (40+ vitamins & minerals), and user profile
- **Three output formats** — JSON (pretty-printed), CSV (one file per data type), SQLite (normalized with foreign keys and indexes)
- **Built-in analytics** — calorie stats, macro ratios, meal distribution, weight trend, calorie-weight correlation, top products
- **LLM-ready analysis** — generates a compact prompt you can paste into ChatGPT, Claude, DeepSeek, or Gemini for personalized nutrition insights
- **Auto-discovery** — scans your history automatically, no date range needed
- **Concurrent fetching** — parallel API calls (up to 10 workers) for fast exports
- **One-shot export** — `export-all` dumps everything in a single command

## Requirements

- Python 3.11+
- A Yazio account with email/password login

## Installation

### From PyPI (recommended)

```bash
pip install yazio-exporter
```

### With uv

```bash
uv tool install yazio-exporter
```

### With pipx

```bash
pipx install yazio-exporter
```

### From source

```bash
git clone https://github.com/aleksandr-bogdanov/yazio-exporter.git
cd yazio-exporter
uv sync
```

## Quick start

```bash
# One command — exports everything to output/
yazio-exporter export-all you@email.com yourpassword

# Regenerate reports from existing exports
yazio-exporter report -d output/

# Or step by step:
yazio-exporter login you@email.com yourpassword
yazio-exporter days
yazio-exporter weight
yazio-exporter nutrients
yazio-exporter products
yazio-exporter summary -w weight.json
yazio-exporter report
```

All commands have sensible defaults — `login` saves to `token.txt`, other commands read from it, and each writes to its natural filename (`days.json`, `weight.json`, etc.).

## CLI reference

### `login` — Authenticate and save token

```
yazio-exporter login EMAIL PASSWORD [-o token.txt]
```

| Flag            | Description                                     |
| --------------- | ----------------------------------------------- |
| `EMAIL`         | Yazio account email (positional)                |
| `PASSWORD`      | Yazio account password (positional)             |
| `-o, --output`  | Token output file (default: `token.txt`)        |

Token file is created with `0600` permissions.

### `profile` — Export user profile

```
yazio-exporter profile [-t token.txt] [-o profile.json] [--format json]
```

| Flag            | Description                                     |
| --------------- | ----------------------------------------------- |
| `-t, --token`   | Token file (default: `token.txt`)               |
| `-o, --output`  | Output file (default: `profile.json`)           |
| `--format`      | `json`, `csv`, or `sqlite` (default: `json`)    |

### `days` — Export daily diary data

```
yazio-exporter days [-t token.txt] [-o days.json] [-f 2024-01-01] [-e 2024-12-31]
```

| Flag              | Description                                                                           |
| ----------------- | ------------------------------------------------------------------------------------- |
| `-t, --token`     | Token file (default: `token.txt`)                                                     |
| `-o, --output`    | Output file (default: `days.json`)                                                    |
| `--format`        | `json`, `csv`, or `sqlite` (default: `json`)                                          |
| `-w, --what`      | Data types to export, comma-separated (default: `consumed,goals,exercises,water,daily_summary`) |
| `-f, --from-date` | Start date, YYYY-MM-DD (default: auto-discover)                                       |
| `-e, --end-date`  | End date, YYYY-MM-DD (default: today)                                                  |

Without `--from-date`/`--end-date`, auto-discovers all months with data.

### `weight` — Export weight and body measurements

```
yazio-exporter weight [-t token.txt] [-o weight.json] [-f 2024-01-01] [-e 2024-12-31]
```

| Flag              | Description                                     |
| ----------------- | ----------------------------------------------- |
| `-t, --token`     | Token file (default: `token.txt`)               |
| `-o, --output`    | Output file (default: `weight.json`)            |
| `--format`        | `json`, `csv`, or `sqlite` (default: `json`)    |
| `-f, --from-date` | Start date, YYYY-MM-DD (default: 365 days ago)  |
| `-e, --end-date`  | End date, YYYY-MM-DD (default: today)            |

### `nutrients` — Export nutrient history

```
yazio-exporter nutrients [-t token.txt] [-o nutrients.json] [-n vitamin.d,mineral.iron]
```

| Flag              | Description                                              |
| ----------------- | -------------------------------------------------------- |
| `-t, --token`     | Token file (default: `token.txt`)                        |
| `-o, --output`    | Output file (default: `nutrients.json`)                  |
| `--format`        | `json`, `csv`, or `sqlite` (default: `json`)             |
| `-n, --nutrients` | Specific nutrients, comma-separated (default: all)       |
| `-f, --from-date` | Start date, YYYY-MM-DD (default: 365 days ago)           |
| `-e, --end-date`  | End date, YYYY-MM-DD (default: today)                    |

**Available nutrients:**

- **Vitamins:** `vitamin.a`, `vitamin.b1`, `vitamin.b2`, `vitamin.b3`, `vitamin.b5`, `vitamin.b6`, `vitamin.b7`, `vitamin.b11`, `vitamin.b12`, `vitamin.c`, `vitamin.d`, `vitamin.e`, `vitamin.k`
- **Minerals:** `mineral.calcium`, `mineral.iron`, `mineral.potassium`, `mineral.magnesium`, `mineral.phosphorus`, `mineral.zinc`, `mineral.copper`, `mineral.manganese`, `mineral.selenium`, `mineral.iodine`, `mineral.fluoride`, `mineral.chlorine`, `mineral.choline`

### `products` — Resolve product details from days export

```
yazio-exporter products [-t token.txt] [-f days.json] [-o products.json]
```

| Flag              | Description                                     |
| ----------------- | ----------------------------------------------- |
| `-t, --token`     | Token file (default: `token.txt`)               |
| `-f, --from-file` | Days export JSON file (default: `days.json`)    |
| `-o, --output`    | Output file (default: `products.json`)          |
| `--format`        | `json`, `csv`, or `sqlite` (default: `json`)    |

### `summary` — Generate analytics and statistics

```
yazio-exporter summary [-f days.json] [-w weight.json] [-p products.json]
```

| Flag            | Description                                            |
| --------------- | ------------------------------------------------------ |
| `-f, --from-file` | Days export JSON file (default: `days.json`)        |
| `-w, --weight`  | Weight export JSON file                                |
| `-p, --products` | Products export JSON file                             |
| `--period`      | `daily`, `weekly`, or `monthly` (default: `daily`)     |
| `--format`      | `json`, `csv`, or `table` (default: `table`)           |

Outputs to stdout.

### `export-all` — Complete export pipeline

```
yazio-exporter export-all EMAIL PASSWORD [-o output/]
```

| Flag            | Description                                     |
| --------------- | ----------------------------------------------- |
| `EMAIL`         | Yazio account email (positional)                |
| `PASSWORD`      | Yazio account password (positional)             |
| `-o, --output`  | Output directory (default: `output/`)           |
| `--format`      | `json`, `csv`, or `sqlite` (default: `json`)    |

Creates the output directory and writes: `profile.json`, `days.json`, `weight.json`, `nutrients.json`, `products.json`, `summary.txt`, `analysis.md`, `llm_prompt.txt`.

### `report` — Generate analysis and LLM prompt from existing exports

```
yazio-exporter report [-d output/] [--start 2024-01-01] [--end 2024-12-31]
```

| Flag            | Description                                            |
| --------------- | ------------------------------------------------------ |
| `-d, --dir`     | Directory with exported JSON files (default: `output/`) |
| `--start`       | Start date filter, YYYY-MM-DD (optional)               |
| `--end`         | End date filter, YYYY-MM-DD (optional)                 |

Reads `days.json`, `weight.json`, `products.json`, and `profile.json` from the directory and generates `analysis.md` (pre-computed statistics) and `llm_prompt.txt` (paste-ready LLM prompt).

## LLM analysis

The `export-all` and `report` commands generate an `llm_prompt.txt` file — a compact, paste-ready prompt containing your nutrition data formatted for any LLM. Copy the contents and paste into ChatGPT, Claude, DeepSeek, or Gemini to get personalized insights:

```bash
# Generate from existing exports
yazio-exporter report -d output/

# Filter to a specific date range
yazio-exporter report -d output/ --start 2024-06-01 --end 2024-12-31

# Then paste llm_prompt.txt into your LLM of choice
cat output/llm_prompt.txt | pbcopy  # macOS
```

The prompt instructs the LLM to act as a sports nutritionist and analyze binge-recovery cycles, plateau mechanics, TDEE, trigger patterns, protein adequacy, food crutches, and more — all backed by your actual data.

An `analysis.md` file is also generated with pre-computed statistics (calorie averages, macro splits, weight trends, top foods) that you can reference directly or include alongside the LLM prompt for richer context.

## Output examples

### JSON (days)

```json
{
  "2024-01-15": {
    "consumed": {
      "products": [
        {"product_id": "abc-123", "amount": 150, "daytime": "breakfast"}
      ],
      "recipe_portions": [],
      "simple_products": []
    },
    "goals": {"data": {"energy": 2000, "protein": 120}},
    "exercises": {"training": [], "custom_training": [], "activity": null},
    "water": {"water_intake": 2500},
    "daily_summary": {"meals": {"breakfast": {"nutrients": {"energy.energy": 450}}}}
  }
}
```

### CSV (nutrients)

```csv
date,nutrient_id,value
2024-01-15,vitamin.d,15.2
2024-01-15,mineral.iron,8.5
2024-01-16,vitamin.d,12.0
```

### SQLite schema

```
days(date, energy, carb, protein, fat, energy_goal)
consumed_items(id, date, product_id, amount, energy)
products(product_id, name, category, energy_per_100g, carb_per_100g, protein_per_100g, fat_per_100g)
recipes(recipe_id, name, portion_count, energy_per_portion, ...)
weight_log(date, weight, body_fat, waist, hip, chest)
nutrient_daily(id, date, nutrient_id, value)
exercises(id, date, exercise_type, duration_minutes, calories_burned)
water_intake(date, water_ml)
goals(date, energy_goal, protein_goal, fat_goal, carb_goal, water_goal, ...)
daily_summary(date, total_energy, breakfast_energy, lunch_energy, dinner_energy, snack_energy)
users(id, email, start_weight, current_weight, goal, sex, activity_degree)
```

## Development

```bash
just setup          # uv sync --all-extras
just test           # run all tests
just test -v        # verbose
just lint           # ruff check src/ tests/
just fmt            # ruff format src/ tests/
just build          # uv build
just clean          # remove build artifacts
```

## License

MIT
