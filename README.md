# HomeFit

A Streamlit app that turns a doctor-prescribed rehab plan into a home workout you can
actually do — matched to your injuries and whatever equipment you have around the house,
with on-the-spot equipment substitution. Includes a chat-based intake as an alternative
to filling out the form by hand. Available in English and Korean (한국어).

## Setup

Requires Python 3.10+.

```bash
git clone https://github.com/arr10/physx.git
cd physx
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### OpenAI API key (optional)

An API key is only needed for live plan generation, equipment substitution, and the chat
intake — the app runs fully offline in **Demo mode** without one (see below).

Set it any one of these ways:

- Paste it into the ⚙ Settings popover in the app header, or
- Create `.streamlit/secrets.toml`:
  ```toml
  OPENAI_API_KEY = "sk-..."
  ```
- Or export it as an environment variable:
  ```bash
  export OPENAI_API_KEY="sk-..."
  ```

## Launching the demo

Run the app:

```bash
streamlit run app.py
```

**Demo mode** is on by default (toggle it in the ⚙ Settings popover in the header) — this runs the
whole flow (plan generation, equipment substitution, chat intake) with canned responses
and no API key or network calls required. Turn it off once you've added a real API key to
get live, LLM-generated plans.

The same Settings popover has a **Language** picker (English / 한국어) that switches the
whole UI, the bundled demo exercise catalogue, and the generated PDF. With a live API key,
it also tells the model to generate plans, substitutes, and chat replies in the selected
language.

## App flow

- **Welcome** — explains the concept.
- **Start** — describe your injuries and paste in the plan your doctor prescribed.
- **Chat** — a conversational alternative to Start; talk through your injury with an AI
  coach instead of filling out the form.
- **Your plan** — the generated home workout, grouped by day, with per-exercise equipment
  substitution. For each exercise, the LLM tries to match it to a demo photo and GIF from
  the bundled exercise/stretch library; if nothing fits, a default image and video are
  shown instead.
