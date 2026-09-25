"""Turn a doctor-prescribed training plan (free text) into structured exercises.

The output uses exactly the fields of plan.json and is written to generated_plan.json.
"""
import json
import re
from pathlib import Path

from core import DATA_DIR, call_openai, exercise_media_catalog
from i18n import get_language

TEMPLATE_PATH = DATA_DIR / "plan.json"
GENERATED_PLAN_PATH = DATA_DIR / "generated_plan.json"

PLAN_SYSTEM_PROMPT = """You are a certified strength & conditioning coach who turns prescribed
rehabilitation plans into concrete, well-specified exercises.
Rules:
- Pick whatever exercise best carries out the prescription. Do not restrict yourself to any
  particular setting or kit — standard gym, clinic and rehab equipment are all fair game.
  The user swaps equipment for what they actually have in a later step.
- Write as if the person trains in a clinic gym. Where an exercise wants load, support or a
  surface, name the equipment a physiotherapist would reach for — exercise mat, resistance band,
  ankle weight, dumbbell, bench, step, wall, foam roller — in "equipment". Leave "equipment"
  empty only when the exercise truly needs nothing at all.
- Safety first: respect the stated injuries and limitations, and say how to set the movement up
  so it stays controlled.
- For "easier_variation" and "harder_variation": check whether the person's stated injury or
  limitation actually bears on this exercise. If it does, make the easier variation the safer
  regression for that specific injury (less range of motion, less load, more support) and the
  harder variation a progression that still respects it. If the injury has no bearing on this
  exercise, ignore it here and give an ordinary progression/regression instead.
- Respond with ONLY a valid JSON object that follows the schema you are given. No markdown."""

PLAN_SCHEMA = """{
  "exercises": [
    {
      "id": str,                       // kebab-case, unique
      "day": int,                      // 1-based training day
      "name": str,
      "category": str,                 // e.g. "Lower body", "Mobility"
      "movement_pattern": str,
      "target_muscles": [str],
      "equipment": [str],              // what the exercise calls for; [] for bodyweight only
      "optional_equipment": [str],     // items that make it better but aren't required
      "equipment_replacement": {str: [str]},  // optional: equipment item -> other items that work
      "difficulty": "beginner" | "intermediate" | "advanced",
      "iterations": {
        "sets": int, "reps": int | null, "duration_seconds": int | null,
        "rest_seconds": int, "tempo": str
      },
      "instructions": [str],
      "safety_tips": [str],
      "easier_variation": str,
      "harder_variation": str
    }
  ]
}"""

MEDIA_MATCH_SYSTEM_PROMPT = """You match training-plan exercises to stock demonstration images from a
fixed catalogue.
Rules:
- Only match an exercise to a catalogue entry that shows the SAME movement: same joint action,
  same equipment or setup — not just the same body part or category.
- Slugs are IDs, not text: copy them exactly as given, never translate or alter them.
- Use null when nothing in the catalogue genuinely depicts the exercise's movement — a loose or
  partial match is worse than no image at all.
- Respond with ONLY a valid JSON object that follows the schema you are given. No markdown."""

MEDIA_MATCH_SCHEMA = """{
  "matches": [
    {"id": str, "media": str | null}
  ]
}"""

REQUIRED_LIST_FIELDS = ["target_muscles", "equipment", "optional_equipment",
                        "instructions", "safety_tips"]
REQUIRED_TEXT_FIELDS = {
    "name": "Exercise",
    "category": "General",
    "movement_pattern": "General",
    "difficulty": "beginner",
    "easier_variation": "Reduce the range of motion or the number of reps.",
    "harder_variation": "Add a pause at the hardest point, or add one set.",
}


def load_template_example() -> str:
    with TEMPLATE_PATH.open(encoding="utf-8") as template_file:
        return template_file.read()


def describe_injuries(injuries_text: str) -> str:
    return (injuries_text or "").strip() or "none reported"


def build_plan_prompt(injuries_text: str, plan_text: str) -> str:
    return (
        "A doctor or physiotherapist prescribed this training plan, written as free text:\n"
        f"\"\"\"\n{plan_text.strip()}\n\"\"\"\n\n"
        "The person describes their injuries / limitations as:\n"
        f"{describe_injuries(injuries_text)}\n\n"
        "Convert the prescribed plan into concrete home exercises. Keep the prescribed "
        "structure (days, focus, volume) wherever the text states it, and fill in sensible "
        "details where it does not. Never include a movement that loads an injured area in a "
        "way the plan does not ask for.\n\n"
        "Spell out what each exercise needs in \"equipment\" — the user swaps those items for "
        "what they have at home in a later step, so name them plainly rather than designing "
        "around any particular set of gear.\n\n"
        "For each exercise's \"easier_variation\" and \"harder_variation\", look up the injuries "
        "described above and check whether this particular exercise touches them. Where it does, "
        "tailor both variations to that injury; where it doesn't, give a normal progression or "
        "regression instead of forcing an injury reference that doesn't apply.\n\n"
        "Return JSON with this schema:\n" + PLAN_SCHEMA + "\n\n"
        "Here is a complete, correctly formatted example entry:\n" + load_template_example()
    )


def slugify(text: str, fallback: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", str(text).lower()).strip("-")
    return slug or fallback


def as_list(value) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value] if value.strip() else []
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    return [str(value)]


def as_int(value, default: int | None) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def normalize_exercise(raw: dict, index: int) -> dict:
    """Coerce one model-produced exercise into the plan.json shape."""
    exercise = {
        "id": slugify(raw.get("id") or raw.get("name") or "", f"exercise-{index + 1}"),
        "day": as_int(raw.get("day"), 1) or 1,
    }
    for field, default in REQUIRED_TEXT_FIELDS.items():
        value = raw.get(field)
        exercise[field] = str(value).strip() if value not in (None, "") else default
    if exercise["difficulty"].lower() not in {"beginner", "intermediate", "advanced"}:
        exercise["difficulty"] = "beginner"
    else:
        exercise["difficulty"] = exercise["difficulty"].lower()

    for field in REQUIRED_LIST_FIELDS:
        exercise[field] = as_list(raw.get(field))
    if not exercise["instructions"]:
        exercise["instructions"] = ["Follow the movement as prescribed, slowly and under control."]

    replacements = raw.get("equipment_replacement")
    exercise["equipment_replacement"] = (
        {str(key): as_list(value) for key, value in replacements.items()}
        if isinstance(replacements, dict) else {}
    )

    raw_iterations = raw.get("iterations") if isinstance(raw.get("iterations"), dict) else {}
    reps = as_int(raw_iterations.get("reps"), None)
    duration = as_int(raw_iterations.get("duration_seconds"), None)
    if reps is None and duration is None:
        reps = 10
    exercise["iterations"] = {
        "sets": as_int(raw_iterations.get("sets"), 3) or 3,
        "reps": reps,
        "duration_seconds": duration,
        "rest_seconds": as_int(raw_iterations.get("rest_seconds"), 60) or 60,
        "tempo": str(raw_iterations.get("tempo") or "controlled"),
    }
    return exercise


def normalize_plan(data: dict) -> dict:
    raw_exercises = data.get("exercises")
    if not isinstance(raw_exercises, list) or not raw_exercises:
        raise ValueError("The model returned no exercises")

    exercises, seen_ids = [], set()
    for index, raw in enumerate(raw_exercises):
        if not isinstance(raw, dict):
            continue
        exercise = normalize_exercise(raw, index)
        base_id, suffix = exercise["id"], 2
        while exercise["id"] in seen_ids:
            exercise["id"] = f"{base_id}-{suffix}"
            suffix += 1
        seen_ids.add(exercise["id"])
        exercises.append(exercise)

    if not exercises:
        raise ValueError("The model returned no usable exercises")
    exercises.sort(key=lambda item: item["day"])
    return {"exercises": exercises}


# Bundled catalogue exercise id -> media slug in assets/exercises. Demo mode only uses the
# exercises listed here, so every exercise in an offline plan has a real photo/GIF.
DEMO_EXERCISE_MEDIA = {
    "chair-squat": "bodyweight-squat",
    "backpack-push-up": "push-up",
    "chair-dips": "chair-tricep-dip",
    "couch-split-squat": "lunge",
    "couch-hip-thrust": "glute-bridge",
    "stair-calf-raise": "calf-raise",
}


def demo_plan() -> dict:
    """Plan built from the bundled catalogue, so the flow works without an API key."""
    catalogue_name = "exercises.ko.json" if get_language() == "ko" else "exercises.json"
    with (DATA_DIR / catalogue_name).open(encoding="utf-8") as catalogue_file:
        catalogue = json.load(catalogue_file)["exercises"]
    with_media = [source for source in catalogue if source["id"] in DEMO_EXERCISE_MEDIA]
    exercises = []
    for index, source in enumerate(with_media):
        exercise = {key: value for key, value in source.items() if key != "replaces"}
        exercise["day"] = index // 2 + 1
        exercises.append(normalize_exercise(exercise, index))
    return {"exercises": exercises}


def build_media_match_prompt(exercises: list[dict], catalog: dict[str, dict]) -> str:
    catalog_lines = "\n".join(f"- {slug}: {entry['label']}" for slug, entry in catalog.items())
    exercise_lines = "\n".join(
        f"- id={exercise['id']}, name=\"{exercise['name']}\", category={exercise['category']}, "
        f"movement_pattern={exercise['movement_pattern']}"
        for exercise in exercises
    )
    return (
        "Catalogue of available demonstration images, one per slug:\n"
        f"{catalog_lines}\n\n"
        "Exercises from a training plan:\n"
        f"{exercise_lines}\n\n"
        "For each exercise, return its id and the single catalogue slug that best depicts its "
        "movement, or null if none genuinely do.\n\n"
        f"Return JSON with this schema:\n{MEDIA_MATCH_SCHEMA}"
    )


def match_exercise_media(api_key: str | None, model: str, demo_mode: bool,
                         exercises: list[dict]) -> dict[str, str | None]:
    """Exercise id -> best-matching media catalogue slug, chosen by the model.

    Offline (demo mode or no API key) this uses the fixed DEMO_EXERCISE_MEDIA mapping instead
    of calling the API; unmapped exercises fall back to the generic default image/GIF.
    """
    catalog = exercise_media_catalog()
    if demo_mode or not api_key:
        return {exercise["id"]: DEMO_EXERCISE_MEDIA[exercise["id"]] for exercise in exercises
                if DEMO_EXERCISE_MEDIA.get(exercise["id"]) in catalog}
    if not catalog:
        return {}
    try:
        raw = call_openai(api_key, model, build_media_match_prompt(exercises, catalog),
                          system_prompt=MEDIA_MATCH_SYSTEM_PROMPT)
    except Exception:
        return {}
    valid_ids = {exercise["id"] for exercise in exercises}
    matches: dict[str, str | None] = {}
    for row in raw.get("matches", []) if isinstance(raw, dict) else []:
        if isinstance(row, dict) and row.get("id") in valid_ids and row.get("media") in catalog:
            matches[row["id"]] = row["media"]
    return matches


def attach_exercise_media(api_key: str | None, model: str, demo_mode: bool, plan: dict) -> dict:
    """Set each exercise's "media" field to its matched catalogue slug, or None."""
    matches = match_exercise_media(api_key, model, demo_mode, plan["exercises"])
    for exercise in plan["exercises"]:
        exercise["media"] = matches.get(exercise["id"])
    return plan


def save_plan(plan: dict, path: Path = GENERATED_PLAN_PATH) -> Path:
    path.parent.mkdir(exist_ok=True)
    with path.open("w", encoding="utf-8") as plan_file:
        json.dump(plan, plan_file, ensure_ascii=False, indent=2)
    return path


def load_saved_plan(path: Path = GENERATED_PLAN_PATH) -> dict | None:
    if not path.exists():
        return None
    with path.open(encoding="utf-8") as plan_file:
        return json.load(plan_file)


def generate_plan(api_key: str | None, model: str, demo_mode: bool,
                  injuries_text: str, plan_text: str) -> dict:
    """Send the prescribed plan to GPT and return exercises in plan.json shape."""
    if demo_mode or not api_key:
        plan = demo_plan()
    else:
        raw = call_openai(api_key, model, build_plan_prompt(injuries_text, plan_text),
                          system_prompt=PLAN_SYSTEM_PROMPT)
        plan = normalize_plan(raw)
    return attach_exercise_media(api_key, model, demo_mode, plan)
