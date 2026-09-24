"""Shared HomeFit helpers: OpenAI access, equipment substitution, plan rendering."""
import functools
import json
import os
from pathlib import Path

import streamlit as st
from openai import OpenAI
from PIL import Image, ImageChops

from i18n import LANGUAGES, get_language, set_language, t

APP_DIR = Path(__file__).parent
ASSETS_DIR = APP_DIR / "assets"   # images and video
DATA_DIR = APP_DIR / "data"       # json catalogues, generated plans, the sqlite file
LOGO_PATH = ASSETS_DIR / "logo.png"
LOGO_MARK_PATH = ASSETS_DIR / "logo_mark.png"
DEFAULT_MODEL = "gpt-6-luna"

EXERCISE_MEDIA_DIRS = (ASSETS_DIR / "exercises", ASSETS_DIR / "stretches")
DEFAULT_EXERCISE_IMAGE = ASSETS_DIR / "exercise.png"
DEFAULT_EXERCISE_GIF = ASSETS_DIR / "default.gif"
MEDIA_FILE_SUFFIXES = {".png", ".jpg", ".jpeg", ".gif"}

# ---------------------------------------------------------------- constants
COMMON_EQUIPMENT = [
    "Sturdy chair (no wheels)", "Dining table", "Couch / sofa", "Bed", "Stairs / step",
    "Wall", "Door frame", "Backpack (can be loaded with books)", "Water jugs / bottles",
    "Towel", "Broomstick / mop handle", "Pillow / cushion", "Laundry detergent bottle",
    "Resistance band", "Dumbbells", "Yoga mat", "Kettlebell", "Pull-up bar",
]

SYSTEM_PROMPT = """You are a certified strength & conditioning coach who designs safe home workouts.
Rules:
- Use ONLY the equipment the user lists, plus bodyweight, the floor and a wall.
- Match the movement pattern and primary muscles of any exercise you replace.
- Safety first: never use furniture with wheels, glass, folding/unstable items, or anything that
  could tip. Tell the user how to check stability. Respect stated injuries/limitations.
- Scale sets/reps to the user's fitness level and goal.
- Respond with ONLY a valid JSON object that follows the schema you are given. No markdown."""

SUBSTITUTE_SCHEMA = """{
  "substitutes": [
    {"item": str, "why_it_works": str}
  ]
}"""

ADAPT_SCHEMA = """{
  "equipment": [str],
  "instructions": [str],
  "safety_tips": [str]
}"""

CHAT_INTAKE_SYSTEM_PROMPT = """You are a friendly certified physiotherapist-coach helping someone
describe an injury so HomeFit can build them a safe home training plan.
Rules:
- Ask one focused question at a time — don't overwhelm them with a list.
- Cover: what's injured and how it happened, current pain/limitations, any doctor-given
  restrictions or plan already in hand, training days per week, and their main goal.
- Once you have enough to work with, say so plainly and tell them to click "Build my plan"."""

INTAKE_EXTRACT_SCHEMA = """{
  "injuries_text": str,
  "plan_text": str
}"""


def chat_demo_prompts() -> list[str]:
    """Canned assistant turns for the Chat page's offline/demo conversation."""
    return t("chat_demo_prompts")


def demo_substitutes() -> dict:
    return {"substitutes": t("demo_substitutes")}


# ---------------------------------------------------------------- branding
def logo_mark() -> Image.Image:
    """The house mark cropped out of the logo lockup — the wordmark is unreadable tab-sized.

    Cached next to the logo and rebuilt whenever logo.png is newer.
    """
    if (not LOGO_MARK_PATH.exists()
            or LOGO_MARK_PATH.stat().st_mtime < LOGO_PATH.stat().st_mtime):
        logo = Image.open(LOGO_PATH).convert("RGBA")
        mark = logo.crop((0, 0, logo.width, int(logo.height * 0.62)))  # drop the wordmark
        flattened = Image.new("RGB", mark.size, "white")
        flattened.paste(mark, mask=mark.split()[3])
        margin = ImageChops.difference(flattened, Image.new("RGB", mark.size, "white")).getbbox()
        if margin:
            mark = mark.crop(margin)
        mark.save(LOGO_MARK_PATH)
    return Image.open(LOGO_MARK_PATH)


def render_header(pages: list, current) -> None:
    """Logo on the left, one nav button per page beside it, settings on the right."""
    st.markdown(
        """
        <style>
        div[class*="st-key-header_nav"] div[data-testid="stButton"] button {
            padding: 0.3rem 0.9rem;
            font-size: 0.95rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    brand_col, settings_col = st.columns([6, 1], vertical_alignment="center")
    with brand_col:
        # One flex row: logo, then the page buttons immediately to its right.
        with st.container(key="header_nav", horizontal=True, horizontal_alignment="left",
                          vertical_alignment="center", gap="medium"):
            st.image(str(LOGO_PATH), width=230)
            for page in pages:
                is_current = page.title == getattr(current, "title", None)
                if st.button(page.title, key=f"nav_{page.title}", width="content",
                             type="primary" if is_current else "secondary") and not is_current:
                    st.switch_page(page)
    with settings_col:
        st.session_state["settings"] = render_settings()


def current_settings() -> tuple[str | None, str, bool]:
    """The API key, model and demo flag chosen in the header's Settings popover."""
    return st.session_state.get("settings", (resolve_api_key(), DEFAULT_MODEL, False))


# ---------------------------------------------------------------- OpenAI
def resolve_api_key(sidebar_key: str = "") -> str | None:
    if sidebar_key and sidebar_key.strip():
        return sidebar_key.strip()
    try:
        secret_key = st.secrets.get("OPENAI_API_KEY", "")
        if secret_key and secret_key.strip():
            return secret_key.strip()
    except Exception:  # no secrets.toml present
        pass
    environment_key = os.getenv("OPENAI_API_KEY")
    return environment_key.strip() if environment_key and environment_key.strip() else None


def localize_system_prompt(system_prompt: str) -> str:
    """Append a language directive when the user has switched the UI to Korean."""
    if get_language() == "ko":
        return system_prompt + (
            "\n\nRespond entirely in Korean (한국어), including any free-text inside the JSON "
            "fields you return (names, categories, instructions, tips, descriptions). Leave "
            "any fixed enum value exactly as specified in the schema (e.g. \"beginner\", "
            "\"intermediate\", \"advanced\") untranslated."
        )
    return system_prompt


def call_openai(api_key: str, model: str, user_prompt: str,
                system_prompt: str = SYSTEM_PROMPT) -> dict:
    client = OpenAI(api_key=api_key)
    resp = client.chat.completions.create(
        model=model,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": localize_system_prompt(system_prompt)},
            {"role": "user", "content": user_prompt},
        ],
    )
    return json.loads(resp.choices[0].message.content)


def call_openai_chat(api_key: str, model: str, messages: list[dict]):
    """Plain-text streaming completion (no JSON mode) for the chat intake page."""
    if messages and messages[0].get("role") == "system":
        messages = [dict(messages[0], content=localize_system_prompt(messages[0]["content"]))] \
            + messages[1:]
    client = OpenAI(api_key=api_key)
    return client.chat.completions.create(model=model, messages=messages, stream=True)


def build_intake_extract_prompt(transcript: str) -> str:
    return (
        "Here is a conversation between a user and a coach figuring out a home training plan "
        f"after an injury:\n\"\"\"\n{transcript}\n\"\"\"\n\n"
        "Summarize it into two fields:\n"
        "- injuries_text: the injuries/limitations the user described, in their own words.\n"
        "- plan_text: a training plan you'd prescribe given the conversation, written the way a "
        "doctor or physiotherapist would hand it over (days per week, focus per day, sets/reps "
        "or hold times).\n\n"
        f"Return JSON with this schema:\n{INTAKE_EXTRACT_SCHEMA}"
    )


def extract_intake_from_chat(api_key: str, model: str, messages: list[dict]) -> dict:
    transcript = "\n".join(f"{m['role']}: {m['content']}" for m in messages)
    return call_openai(api_key, model, build_intake_extract_prompt(transcript))


def run_api_test(api_key: str | None, model: str) -> dict:
    if not api_key:
        raise ValueError("No OpenAI API key was resolved")
    print(f"[HomeFit API test] sending request with model={model!r}", flush=True)
    result = call_openai(
        api_key,
        model,
        'Return exactly this JSON object: {"status": "ok", "message": "API connection works"}',
    )
    print(f"[HomeFit API test] response={json.dumps(result, ensure_ascii=True)}", flush=True)
    return result


# ---------------------------------------------------------------- equipment substitution
def demo_adapted_instructions(exercise: dict, original_item: str, substitute_item: str) -> dict:
    adapted_steps = []
    replaced_any = False
    for step in exercise["instructions"]:
        if original_item in step:
            adapted_steps.append(step.replace(original_item, substitute_item))
            replaced_any = True
        else:
            adapted_steps.append(step)
    if not replaced_any:
        adapted_steps = [
            t("demo_adapted_fallback", name=exercise["name"], substitute=substitute_item,
              original=original_item)
        ] + adapted_steps
    return {
        "equipment": [substitute_item],
        "instructions": adapted_steps,
        "safety_tips": exercise["safety_tips"] + [
            t("demo_adapted_safety_tip", substitute=substitute_item)
        ],
    }


def build_substitute_prompt(exercise: dict, missing_item: str) -> str:
    return (
        f"The home exercise \"{exercise['name']}\" ({exercise['movement_pattern']}, targets "
        f"{', '.join(exercise['target_muscles'])}) normally uses this equipment: {missing_item}.\n"
        "The user doesn't have it at home.\n\n"
        "Suggest 3-4 common household items that could substitute for it, keeping the same "
        "movement pattern, resistance style, and safety profile. Avoid unstable, wheeled, glass, "
        "or folding items.\n\n"
        f"Return JSON with this schema:\n{SUBSTITUTE_SCHEMA}"
    )


def build_adapt_prompt(exercise: dict, original_item: str, substitute_item: str) -> str:
    return (
        f"Rewrite the setup for the home exercise \"{exercise['name']}\" so it uses "
        f"\"{substitute_item}\" instead of \"{original_item}\".\n\n"
        f"Original equipment: {', '.join(exercise['equipment'])}\n"
        "Original instructions:\n- " + "\n- ".join(exercise["instructions"]) +
        "\n\nOriginal safety tips:\n- " + "\n- ".join(exercise["safety_tips"]) +
        f"\n\nReturn JSON with this schema:\n{ADAPT_SCHEMA}"
    )


def get_substitutes(api_key: str | None, model: str, demo_mode: bool, exercise: dict,
                    missing_item: str) -> dict:
    curated = exercise.get("equipment_replacement", {}).get(missing_item)
    if curated:
        return {
            "substitutes": [
                {"item": item, "why_it_works": t("curated_substitute_why")}
                for item in curated
            ],
        }
    if demo_mode or not api_key:
        return demo_substitutes()
    return call_openai(api_key, model, build_substitute_prompt(exercise, missing_item))


def get_adapted_instructions(api_key: str | None, model: str, demo_mode: bool, exercise: dict,
                             original_item: str, substitute_item: str) -> dict:
    if demo_mode or not api_key:
        return demo_adapted_instructions(exercise, original_item, substitute_item)
    adapted = call_openai(api_key, model, build_adapt_prompt(exercise, original_item, substitute_item))
    instructions = adapted.get("instructions")
    if isinstance(instructions, str):
        instructions = [instructions]
    if not isinstance(instructions, list) or not all(isinstance(step, str) for step in instructions):
        raise ValueError("OpenAI returned no valid instructions for the substitute")
    adapted["instructions"] = instructions
    return adapted


# ---------------------------------------------------------------- settings popover
def render_settings() -> tuple[str | None, str, bool]:
    """Shared ⚙ Settings popover. Returns (api_key, model, demo_mode)."""
    import traceback

    # Streamlit drops widget state when you switch pages, so the widgets are seeded
    # from a plain session_state entry that survives navigation.
    saved = st.session_state.get("settings_values",
                                 {"api_key": "", "model": DEFAULT_MODEL, "demo": False})
    language_codes = list(LANGUAGES)

    with st.popover(t("settings_button"), width="stretch"):
        st.header(t("settings_header"))
        language = st.selectbox(
            t("settings_language_label"), language_codes,
            index=language_codes.index(get_language()),
            format_func=lambda code: LANGUAGES[code], key="settings_language",
        )
        set_language(language)
        key_input = st.text_input(t("settings_api_key_label"), type="password",
                                  key="settings_api_key", value=saved["api_key"],
                                  help=t("settings_api_key_help"))
        model = st.text_input(t("settings_model_label"), value=saved["model"],
                              key="settings_model", help=t("settings_model_help"))
        demo_mode = st.toggle(t("settings_demo_label"), value=saved["demo"],
                              key="settings_demo_mode")
        if st.button(t("settings_test_button"), key="settings_api_test"):
            try:
                test_result = run_api_test(resolve_api_key(key_input), model)
                st.success(t("settings_test_success"))
                st.json(test_result)
            except Exception as error:
                print(f"[HomeFit API test] error={error!r}", flush=True)
                traceback.print_exc()
                st.error(t("settings_test_error", error=error))

    st.session_state["settings_values"] = {"api_key": key_input, "model": model, "demo": demo_mode}
    return resolve_api_key(key_input), model, demo_mode


# ---------------------------------------------------------------- exercise media
@functools.lru_cache(maxsize=1)
def exercise_media_catalog() -> dict[str, dict]:
    """Map media slug -> {"label", "image", "gif"}, built from the downloaded exercise/stretch
    photos and GIFs in assets/exercises and assets/stretches."""
    catalog: dict[str, dict] = {}
    for directory in EXERCISE_MEDIA_DIRS:
        if not directory.is_dir():
            continue
        for file in sorted(directory.iterdir()):
            if not file.is_file() or file.suffix.lower() not in MEDIA_FILE_SUFFIXES:
                continue
            entry = catalog.setdefault(file.stem, {
                "label": file.stem.replace("-", " ").capitalize(), "image": None, "gif": None,
            })
            if file.suffix.lower() == ".gif":
                entry["gif"] = file
            else:
                entry["image"] = file
    return catalog


def exercise_media_paths(media_slug: str | None) -> tuple[Path, Path]:
    """Resolve a matched catalogue slug to (image_path, gif_path). Falls back to the generic
    defaults when there's no match, or for whichever half (still image or GIF) it lacks."""
    entry = exercise_media_catalog().get(media_slug or "", {})
    return entry.get("image") or DEFAULT_EXERCISE_IMAGE, entry.get("gif") or DEFAULT_EXERCISE_GIF


# ---------------------------------------------------------------- plan rendering
def group_by_day(exercises: list[dict], language: str | None = None) -> dict[str, list[dict]]:
    """Group plan exercises into {"Day 1": [...], ...}, keeping the given order.

    `language` defaults to the active session language; pdf_export.py passes it
    explicitly since a PDF is built for a specific language, not the live session.
    """
    days: dict[str, list[dict]] = {}
    for exercise in exercises:
        raw_day = exercise.get("day", 1)
        label = raw_day if isinstance(raw_day, str) else t("day_label", n=raw_day, lang=language)
        days.setdefault(label, []).append(exercise)
    return days


def render_day_picker(days: list[str]) -> str:
    if "selected_day" not in st.session_state or st.session_state["selected_day"] not in days:
        st.session_state["selected_day"] = days[0]

    st.markdown(
        """
        <style>
        div[class*="st-key-day_picker"] div[data-testid="stButton"] button {
            aspect-ratio: 1 / 1;
            width: 100%;
            max-width: 3.6rem;
            min-height: 0;
            padding: 0;
            font-size: 0.8rem;
            font-weight: 600;
            white-space: nowrap;
        }
        div[class*="st-key-day_picker"] div[data-testid="stHorizontalBlock"] {
            gap: 0.4rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    with st.container(key="day_picker"):
        # One narrow column per day plus a filler, so the squares stay the same
        # small size and sit together whether there are 3 days or 7.
        cols = st.columns([1] * len(days) + [max(1, 10 - len(days))], gap="small")
        for col, day in zip(cols, days):
            is_selected = day == st.session_state["selected_day"]
            if col.button(day, key=f"day_btn_{day}", width="stretch",
                          type="primary" if is_selected else "secondary"):
                st.session_state["selected_day"] = day
                st.rerun()

    return st.session_state["selected_day"]


def render_daily_plan(exercises: list[dict], api_key: str | None, model: str, demo_mode: bool):
    """Render a plan (exercises in plan.json shape) with a day picker and substitutions."""
    days_map = group_by_day(exercises)
    if not days_map:
        st.info(t("no_plan_exercises"))
        return
    selected_day = render_day_picker(list(days_map))
    st.session_state.setdefault("substitutions", {})

    st.markdown(
        """
        <style>
        div[class*="st-key-equip_row_"] div[data-testid="stButton"] button {
            width: auto;
            aspect-ratio: unset;
            padding: 0.05rem 0.55rem;
            font-size: 0.95rem;
            font-weight: 400;
            min-height: 1.6rem;
            line-height: 1.5;
            border-radius: 0.4rem;
        }
        div[class*="st-key-equip_row_"] div[data-testid="stHorizontalBlock"] {
            gap: 0.5rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    for exercise in days_map[selected_day]:
        exercise_id = exercise["id"]
        iterations = exercise["iterations"]
        if iterations.get("duration_seconds"):
            prescription = t("prescription_duration", sets=iterations["sets"],
                             seconds=iterations["duration_seconds"])
        else:
            prescription = t("prescription_reps", sets=iterations["sets"], reps=iterations["reps"])
        exercise_label = t("exercise_label", name=exercise["name"], prescription=prescription,
                           rest=iterations["rest_seconds"])

        sub_state = st.session_state["substitutions"].get(exercise_id)
        active_equipment = exercise["equipment"]
        active_instructions = exercise["instructions"]
        active_safety_tips = exercise["safety_tips"]
        if sub_state and sub_state.get("adapted"):
            active_equipment = sub_state["adapted"].get("equipment") or active_equipment
            if "instructions" in sub_state["adapted"]:
                active_instructions = sub_state["adapted"]["instructions"]
            active_safety_tips = sub_state["adapted"].get("safety_tips") or active_safety_tips

        with st.expander(exercise_label):
            st.caption(f"{exercise['category']} · {exercise['difficulty'].title()}")
            media_col, details_col = st.columns([1, 2])
            with media_col:
                image_path, gif_path = exercise_media_paths(exercise.get("media"))
                st.image(image_path, caption=t("exercise_demo_caption"))
                st.image(gif_path, caption=t("movement_video_caption"))
            with details_col:
                st.markdown(f"**{t('instructions_heading')}**")
                st.markdown("\n".join(f"{i}. {step}" for i, step in enumerate(active_instructions, 1)))

                st.markdown(f"**{t('equipment_heading')}**")
                st.caption(t("equipment_click_hint"))
                swapped_item = sub_state.get("original_item") if sub_state else None
                if exercise["equipment"]:
                    with st.container(key=f"equip_row_{exercise_id}"):
                        equip_cols = st.columns(len(exercise["equipment"]))
                        for col, item in zip(equip_cols, exercise["equipment"]):
                            crossed_out = item == swapped_item
                            label = f"~~{item}~~" if crossed_out else item
                            if col.button(label, key=f"equip_btn_{exercise_id}_{item}"):
                                if crossed_out:  # clicking it again brings the item back
                                    del st.session_state["substitutions"][exercise_id]
                                else:
                                    st.session_state["substitutions"][exercise_id] = {
                                        "original_item": item, "options": None, "chosen": None, "adapted": None,
                                    }
                                st.rerun()
                    if sub_state and sub_state.get("chosen"):
                        st.caption(t("using_instead_caption", items=", ".join(active_equipment)))
                else:
                    st.caption(t("no_equipment_needed"))

                sub_state = st.session_state["substitutions"].get(exercise_id)
                if sub_state and sub_state.get("original_item") and not sub_state.get("chosen"):
                    original_item = sub_state["original_item"]
                    if sub_state["options"] is None:
                        with st.spinner(t("finding_substitutes_spinner", item=original_item)):
                            try:
                                sub_state["options"] = get_substitutes(
                                    api_key, model, demo_mode, exercise, original_item
                                ).get("substitutes", [])
                            except Exception as e:
                                st.error(t("couldnt_fetch_substitutes", error=e))
                                sub_state["options"] = []

                    st.info(t("substitute_info"))
                    for opt in sub_state["options"]:
                        opt_label = opt.get("item", "")
                        if not opt_label:
                            continue
                        if st.button(opt_label, key=f"sub_opt_{exercise_id}_{opt_label}"):
                            updated_state = st.session_state["substitutions"][exercise_id]
                            updated_state["chosen"] = opt_label
                            with st.spinner(t("updating_instructions_spinner")):
                                try:
                                    adapted = get_adapted_instructions(
                                        api_key, model, demo_mode, exercise, original_item, opt_label
                                    )
                                    if isinstance(adapted.get("instructions"), str):
                                        adapted["instructions"] = [adapted["instructions"]]
                                    updated_state["adapted"] = adapted
                                except Exception as e:
                                    st.error(t("couldnt_adapt_instructions", error=e))
                                    updated_state["adapted"] = None
                            st.rerun()
                        if opt.get("why_it_works"):
                            st.caption(opt["why_it_works"])

                if sub_state and sub_state.get("chosen"):
                    st.success(t("using_chosen_success", chosen=sub_state["chosen"],
                                 original=sub_state["original_item"]))
                    if st.button(t("reset_equipment_button"), key=f"reset_{exercise_id}"):
                        del st.session_state["substitutions"][exercise_id]
                        st.rerun()

                st.markdown(t("targets_label", muscles=", ".join(exercise["target_muscles"])))
                for safety_tip in active_safety_tips:
                    st.warning(safety_tip, icon="⚠️")
                st.info(t("variations_info", easier=exercise["easier_variation"],
                         harder=exercise["harder_variation"]))
