"""HomeFit UI translations — English and Korean, toggled from the Settings popover.

`t(key, **kwargs)` looks up `key` for the active language (read from session state,
set by the Settings popover in core.py) and `.format(**kwargs)`s it if placeholders
are given. Falls back to English, then to the key itself, so a missing translation
never crashes the page.
"""
import streamlit as st

DEFAULT_LANGUAGE = "en"
LANGUAGES = {"en": "English", "ko": "한국어"}

STRINGS = {
    "en": {
        # nav / page titles
        "nav_welcome": "Welcome",
        "nav_start": "Start",
        "nav_chat": "Chat",
        "nav_plan": "Your plan",

        # shared
        "disclaimer": "Not medical advice. Stop if you feel pain, and check that furniture is "
                      "stable before loading it.",
        "couldnt_build_plan": "Couldn't build the plan: {error}",

        # settings popover
        "settings_button": "⚙ Settings",
        "settings_header": "Settings",
        "settings_language_label": "Language",
        "settings_api_key_label": "OpenAI API key",
        "settings_api_key_help": "Leave blank to use OPENAI_API_KEY from env or secrets.",
        "settings_model_label": "Model",
        "settings_model_help": "Any chat model that supports JSON mode.",
        "settings_demo_label": "Demo mode (no API calls)",
        "settings_test_button": "Test API connection",
        "settings_test_success": "API call succeeded. Output was also printed in the Streamlit "
                                 "console.",
        "settings_test_error": "API test failed: {error}",

        # daily plan / equipment substitution (core.py)
        "day_label": "Day {n}",
        "no_plan_exercises": "This plan has no exercises yet.",
        "instructions_heading": "Instructions",
        "equipment_heading": "Equipment",
        "equipment_click_hint": "Click on missing pieces of equipment",
        "no_equipment_needed": "No equipment needed",
        "using_instead_caption": "Using instead: {items}",
        "substitute_info": "You can substitute this equipment with this at home instead:",
        "finding_substitutes_spinner": "Finding substitutes for {item}…",
        "updating_instructions_spinner": "Updating instructions…",
        "couldnt_fetch_substitutes": "Couldn't fetch substitutes: {error}",
        "couldnt_adapt_instructions": "Couldn't adapt instructions: {error}",
        "using_chosen_success": "Using **{chosen}** instead of **{original}**.",
        "reset_equipment_button": "Reset to original equipment",
        "targets_label": "**Targets:** {muscles}",
        "variations_info": "**Easier variation:** {easier}\n\n**Harder variation:** {harder}",
        "prescription_reps": "{sets} sets x {reps} reps",
        "prescription_duration": "{sets} sets x {seconds} seconds",
        "exercise_label": "{name}  ·  {prescription}  ·  Rest {rest} s",
        "exercise_demo_caption": "Exercise demo",
        "movement_video_caption": "Movement video",

        # 0_Welcome.py
        "welcome_intro": "HomeFit turns the training plan your doctor prescribed into a home "
                         "workout you can actually do — using whatever equipment you already have.",
        "welcome_how_it_works": "How it works",
        "welcome_steps": (
            "1. **Tell us what's injured** — paste the plan your doctor prescribed, or talk it "
            "through with our AI coach if you don't have one yet.\n"
            "2. **We turn it into home exercises** matched to your equipment, injuries, and goals.\n"
            "3. **Swap out anything you don't have** — HomeFit suggests household substitutes on "
            "the spot."
        ),
        "welcome_get_started_button": "Get started →",
        "welcome_chat_button": "Or chat with our AI coach →",

        # 1_Start.py
        "start_intro": "Tell us what's injured and what your doctor prescribed. We'll turn it "
                       "into home exercises you can actually do.",
        "start_injuries_subheader": "1 · Your injuries",
        "start_injuries_label": "What injuries or limitations do you have?",
        "start_injuries_placeholder": "e.g. left knee — ACL repair 3 months ago, no deep flexion "
                                      "past 90°; stiff lower back",
        "start_plan_subheader": "2 · The plan your doctor prescribed",
        "start_plan_label": "Paste or type it as free text",
        "start_plan_placeholder": """e.g. 3 sessions per week for 6 weeks, post-ACL reconstruction (3 months out).

Day 1 — Quads & glutes
1. Seated knee extensions — 3 x 12 reps, 60 s rest between sets
2. Glute bridges — 3 x 15 reps, 45 s rest
3. Wall sits — 3 x 30 s hold, 60 s rest

Day 2 — Hip mobility & core
1. Standing hip circles — 2 x 10 reps each direction, 30 s rest
2. Dead bug — 3 x 30 s hold, 30 s rest
3. Side-lying clamshells — 3 x 15 reps each side, 30 s rest

Day 3 — Posterior chain (no loaded spinal flexion)
1. Prone hamstring curls — 3 x 12 reps, 45 s rest
2. Bird dog — 3 x 30 s hold each side, 30 s rest
3. Standing calf raises — 3 x 15 reps, 45 s rest""",
        "start_build_button": "Build my plan →",
        "start_open_saved_button": "Open my saved plan",
        "start_error_no_plan": "Add the prescribed training plan first — that's what the "
                               "exercises are built from.",
        "start_spinner_building": "Turning your prescribed plan into home exercises…",

        # 1_Chat.py
        "chat_intro": "Tell us about your injury a little at a time, back and forth — we'll turn "
                      "the conversation into a home training plan.",
        "chat_input_placeholder": "Tell me what's going on…",
        "chat_greeting_online": "Hi! What's injured, and how long ago did it happen?",
        "chat_demo_prompts": [
            "Let's figure out your home plan. First — what's injured, and how long ago did it "
            "happen?",
            "Got it. What does it stop you from doing right now, and has a doctor given you any "
            "restrictions or a plan already?",
            "Thanks. How many days a week can you train, and what's your main goal — regaining "
            "strength, reducing pain, or getting back to a sport?",
            "I think I have enough to build a plan — hit \"Build my plan\" below whenever you're "
            "ready.",
        ],
        "chat_build_button": "Build my plan from this conversation →",
        "chat_spinner_building": "Turning your conversation into a plan…",
        "chat_from_chat_plan_text": "(From chat) See the conversation above for context.",
        "chat_from_chat_plan_text_fallback": "(From chat) See the conversation above.",

        # 2_Your_plan.py
        "plan_title": "Your plan",
        "plan_warning_no_plan": "No plan yet. Start by telling us about your injuries and what "
                                "your doctor prescribed.",
        "plan_go_to_start_button": "← Go to the start page",
        "plan_built_from_caption": "Built from your intake on {date}",
        "plan_injuries_suffix": " · Injuries: {injuries}",
        "plan_pdf_subtitle": "Injuries: {injuries}",
        "plan_prescribed_expander": "The plan your doctor prescribed",
        "plan_daily_subheader": "Daily plan",
        "plan_daily_intro": "Choose a day to see your exercises. Select an exercise to open its "
                            "instructions and media.",
        "plan_edit_button": "← Edit injuries / prescribed plan",
        "plan_download_button": "Download plan PDF",

        # pdf_export.py
        "pdf_title": "Your training plan",
        "pdf_generated": "Generated {date}",
        "pdf_header_exercise": "Exercise",
        "pdf_header_sets_reps": "Sets x reps",
        "pdf_header_rest": "Rest",
        "pdf_header_equipment": "Equipment",
        "pdf_header_targets": "Targets",
        "pdf_optional": "optional: {items}",
        "pdf_easier": "Easier",
        "pdf_harder": "Harder",
        "pdf_safety": "Safety",
        "pdf_none": "None",
        "pdf_exercise_count": "{n} exercise{plural}",
        "pdf_disclaimer": "Not medical advice. Stop if you feel pain, and check that furniture "
                          "is stable before loading it.",

        # demo-mode canned content (core.py) — shown as-is, with no API calls
        "demo_substitutes": [
            {"item": "Backpack loaded with books",
             "why_it_works": "Gives adjustable resistance you likely already own."},
            {"item": "Large water jug or bottle",
             "why_it_works": "A graspable, weighted stand-in with a similar shape."},
            {"item": "Bath towel",
             "why_it_works": "Can be looped, gripped, or padded to change leverage without "
                             "added weight."},
        ],
        "demo_adapted_fallback": "(Demo) Perform {name} using {substitute} instead of "
                                 "{original}, following the same movement pattern as the "
                                 "original.",
        "demo_adapted_safety_tip": "(Demo) Check that the {substitute} is stable and secure "
                                   "before loading it.",
        "curated_substitute_why": "Curated substitute — matches the same setup and movement.",
    },
    "ko": {
        "nav_welcome": "시작 화면",
        "nav_start": "입력",
        "nav_chat": "채팅",
        "nav_plan": "내 운동 계획",

        "disclaimer": "의학적 조언이 아닙니다. 통증이 느껴지면 즉시 중단하고, 가구를 사용하기 전에 "
                      "안정적인지 확인하세요.",
        "couldnt_build_plan": "계획을 만들지 못했습니다: {error}",

        "settings_button": "⚙ 설정",
        "settings_header": "설정",
        "settings_language_label": "언어",
        "settings_api_key_label": "OpenAI API 키",
        "settings_api_key_help": "비워두면 환경 변수나 secrets의 OPENAI_API_KEY를 사용합니다.",
        "settings_model_label": "모델",
        "settings_model_help": "JSON 모드를 지원하는 채팅 모델이면 무엇이든 가능합니다.",
        "settings_demo_label": "데모 모드 (API 호출 없음)",
        "settings_test_button": "API 연결 테스트",
        "settings_test_success": "API 호출에 성공했습니다. 결과는 Streamlit 콘솔에도 출력되었습니다.",
        "settings_test_error": "API 테스트에 실패했습니다: {error}",

        "day_label": "{n}일차",
        "no_plan_exercises": "이 계획에는 아직 운동이 없습니다.",
        "instructions_heading": "운동 방법",
        "equipment_heading": "장비",
        "equipment_click_hint": "없는 장비를 클릭하세요",
        "no_equipment_needed": "필요한 장비 없음",
        "using_instead_caption": "대신 사용 중: {items}",
        "substitute_info": "집에 있는 이런 물건으로 이 장비를 대신할 수 있습니다:",
        "finding_substitutes_spinner": "{item}의 대체 물건을 찾는 중…",
        "updating_instructions_spinner": "운동 방법을 업데이트하는 중…",
        "couldnt_fetch_substitutes": "대체 물건을 찾지 못했습니다: {error}",
        "couldnt_adapt_instructions": "운동 방법을 조정하지 못했습니다: {error}",
        "using_chosen_success": "**{original}** 대신 **{chosen}**을(를) 사용 중입니다.",
        "reset_equipment_button": "원래 장비로 되돌리기",
        "targets_label": "**대상 근육:** {muscles}",
        "variations_info": "**쉬운 변형:** {easier}\n\n**어려운 변형:** {harder}",
        "prescription_reps": "{sets}세트 x {reps}회",
        "prescription_duration": "{sets}세트 x {seconds}초",
        "exercise_label": "{name} · {prescription} · 휴식 {rest}초",
        "exercise_demo_caption": "운동 사진",
        "movement_video_caption": "동작 영상",

        "welcome_intro": "홈핏은 의사가 처방한 재활 운동 계획을 집에 있는 장비만으로 실제로 할 수 있는 "
                         "홈트레이닝으로 바꿔줍니다.",
        "welcome_how_it_works": "이용 방법",
        "welcome_steps": (
            "1. **부상 부위를 알려주세요** — 의사가 처방한 계획을 붙여넣거나, 아직 없다면 AI 코치와 "
            "대화로 정리해보세요.\n"
            "2. **보유한 장비, 부상, 목표에 맞춰** 홈트레이닝으로 바꿔드립니다.\n"
            "3. **없는 장비는 즉시 교체** — 홈핏이 그 자리에서 집에 있는 대체 물건을 제안합니다."
        ),
        "welcome_get_started_button": "시작하기 →",
        "welcome_chat_button": "AI 코치와 채팅하기 →",

        "start_intro": "부상 부위와 의사가 처방한 계획을 알려주세요. 실제로 할 수 있는 홈트레이닝으로 "
                       "바꿔드립니다.",
        "start_injuries_subheader": "1 · 부상 정보",
        "start_injuries_label": "어떤 부상이나 제약이 있나요?",
        "start_injuries_placeholder": "예: 왼쪽 무릎 — 3개월 전 전방십자인대 재건술, 90도 이상 깊게 "
                                      "굽히기 어려움; 허리 뻣뻣함",
        "start_plan_subheader": "2 · 의사가 처방한 계획",
        "start_plan_label": "자유 형식으로 붙여넣거나 입력하세요",
        "start_plan_placeholder": """예: 전방십자인대 재건술 후 3개월, 6주간 주 3회.

1일차 — 대퇴사두근 & 둔근
1. 앉아서 무릎 펴기 — 3세트 x 12회, 세트 간 휴식 60초
2. 힙 브릿지 — 3세트 x 15회, 휴식 45초
3. 월 시트 — 3세트 x 30초 유지, 휴식 60초

2일차 — 고관절 가동성 & 코어
1. 서서 고관절 돌리기 — 방향당 2세트 x 10회, 휴식 30초
2. 데드 버그 — 3세트 x 30초 유지, 휴식 30초
3. 옆으로 누워 조개 운동 — 좌우 3세트 x 15회, 휴식 30초

3일차 — 후면 사슬 (척추 굴곡 부하 금지)
1. 엎드려 햄스트링 컬 — 3세트 x 12회, 휴식 45초
2. 버드 독 — 좌우 3세트 x 30초 유지, 휴식 30초
3. 서서 종아리 들기 — 3세트 x 15회, 휴식 45초""",
        "start_build_button": "내 계획 만들기 →",
        "start_open_saved_button": "저장된 계획 열기",
        "start_error_no_plan": "먼저 처방받은 운동 계획을 입력하세요 — 여기서 운동을 만듭니다.",
        "start_spinner_building": "처방받은 계획을 홈트레이닝으로 바꾸는 중…",

        "chat_intro": "부상에 대해 조금씩 주고받으며 알려주세요 — 대화 내용을 홈트레이닝 계획으로 "
                      "바꿔드립니다.",
        "chat_input_placeholder": "지금 상황을 알려주세요…",
        "chat_greeting_online": "안녕하세요! 어디를 다치셨고, 언제 다치셨나요?",
        "chat_demo_prompts": [
            "홈트레이닝 계획을 세워볼게요. 먼저 — 어디를 다치셨고, 언제 다치셨나요?",
            "알겠습니다. 지금 하기 어려운 동작은 무엇이고, 의사로부터 받은 제약 사항이나 계획이 "
            "있나요?",
            "감사합니다. 일주일에 며칠 훈련할 수 있고, 주된 목표는 무엇인가요 — 근력 회복, 통증 "
            "완화, 아니면 스포츠 복귀인가요?",
            "계획을 만들 만큼 충분한 정보를 얻은 것 같아요 — 준비되면 아래 \"내 계획 만들기\"를 "
            "눌러주세요.",
        ],
        "chat_build_button": "이 대화로 내 계획 만들기 →",
        "chat_spinner_building": "대화 내용을 계획으로 바꾸는 중…",
        "chat_from_chat_plan_text": "(채팅으로 작성됨) 자세한 내용은 위 대화를 참고하세요.",
        "chat_from_chat_plan_text_fallback": "(채팅으로 작성됨) 위 대화를 참고하세요.",

        "plan_title": "내 운동 계획",
        "plan_warning_no_plan": "아직 계획이 없습니다. 부상 정보와 의사가 처방한 계획을 먼저 "
                                "알려주세요.",
        "plan_go_to_start_button": "← 입력 화면으로 이동",
        "plan_built_from_caption": "{date}에 입력한 정보로 생성됨",
        "plan_injuries_suffix": " · 부상 정보: {injuries}",
        "plan_pdf_subtitle": "부상 정보: {injuries}",
        "plan_prescribed_expander": "의사가 처방한 계획",
        "plan_daily_subheader": "일별 계획",
        "plan_daily_intro": "요일을 선택해 운동을 확인하세요. 운동을 선택하면 방법과 미디어가 "
                            "열립니다.",
        "plan_edit_button": "← 부상 정보 / 처방 계획 수정",
        "plan_download_button": "PDF로 계획 다운로드",

        "pdf_title": "내 운동 계획",
        "pdf_generated": "생성일 {date}",
        "pdf_header_exercise": "운동",
        "pdf_header_sets_reps": "세트 x 횟수",
        "pdf_header_rest": "휴식",
        "pdf_header_equipment": "장비",
        "pdf_header_targets": "대상 근육",
        "pdf_optional": "선택: {items}",
        "pdf_easier": "쉬운 변형",
        "pdf_harder": "어려운 변형",
        "pdf_safety": "안전 수칙",
        "pdf_none": "없음",
        "pdf_exercise_count": "운동 {n}개",
        "pdf_disclaimer": "의학적 조언이 아닙니다. 통증이 느껴지면 즉시 중단하고, 가구를 사용하기 "
                          "전에 안정적인지 확인하세요.",

        "demo_substitutes": [
            {"item": "책이 든 배낭",
             "why_it_works": "이미 가지고 있을 만한 물건으로 무게를 조절할 수 있습니다."},
            {"item": "큰 물통이나 생수병",
             "why_it_works": "비슷한 모양에 손으로 잡기 좋은 무게감 있는 대체품입니다."},
            {"item": "목욕 수건",
             "why_it_works": "고리로 감거나 쥐거나 덧대어 무게 추가 없이 레버리지를 바꿀 수 "
                             "있습니다."},
        ],
        "demo_adapted_fallback": "(데모) {original} 대신 {substitute}을(를) 사용해 {name}을(를) "
                                 "원래와 같은 동작 패턴으로 수행하세요.",
        "demo_adapted_safety_tip": "(데모) {substitute}이(가) 안정적이고 고정되어 있는지 확인한 "
                                   "후 하중을 싣으세요.",
        "curated_substitute_why": "엄선된 대체 물건 — 같은 구성과 동작을 그대로 유지합니다.",
    },
}


def get_language() -> str:
    """The active language code.

    Checks the Settings popover's own widget key first, since Streamlit updates it
    immediately on the rerun the widget itself triggers — before app.py rebuilds the
    (title-translated) page list, which runs ahead of the popover. Falls back to the
    plain session_state entry the popover also writes on every page load, which is
    what pages other than app.py rely on.
    """
    return st.session_state.get(
        "settings_language", st.session_state.get("language", DEFAULT_LANGUAGE)
    )


def set_language(language: str) -> None:
    st.session_state["language"] = language


def t(key: str, lang: str | None = None, **kwargs) -> str:
    """The translated string for `key`, `.format(**kwargs)`-ed.

    Uses the active session language unless `lang` is given explicitly — e.g. by
    pdf_export.py, which renders outside of a live widget interaction and is passed
    the language it should use rather than reading session state itself.
    """
    language = lang or get_language()
    text = STRINGS.get(language, {}).get(key)
    if text is None:
        text = STRINGS[DEFAULT_LANGUAGE].get(key, key)
    return text.format(**kwargs) if kwargs else text
