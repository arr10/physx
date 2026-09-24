"""Render a generated plan as a printable PDF — every day, minus the step-by-step instructions."""
from datetime import date
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (KeepTogether, Paragraph, SimpleDocTemplate, Spacer, Table,
                                TableStyle)

from core import group_by_day

ACCENT = colors.HexColor("#2f5d62")
MUTED = colors.HexColor("#5a5a5a")
RULE = colors.HexColor("#d5dbdb")

# The built-in fonts cover WinAnsi only — swap the few characters that fall outside it.
UNSUPPORTED = {"→": "->", "←": "<-", "≥": ">=", "≤": "<=", "–": "-", "…": "...",
               "’": "'", "‘": "'", "“": '"', "”": '"'}


def clean(text) -> str:
    text = str(text if text is not None else "")
    for character, replacement in UNSUPPORTED.items():
        text = text.replace(character, replacement)
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def styles() -> dict:
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle("PlanTitle", parent=base["Title"], fontSize=20, leading=24,
                                alignment=TA_LEFT, textColor=ACCENT, spaceAfter=2),
        "subtitle": ParagraphStyle("PlanSubtitle", parent=base["Normal"], fontSize=9.5,
                                   leading=13, textColor=MUTED),
        "day": ParagraphStyle("PlanDay", parent=base["Heading2"], fontSize=13, leading=16,
                              textColor=ACCENT, spaceBefore=10, spaceAfter=4),
        "cell": ParagraphStyle("PlanCell", parent=base["Normal"], fontSize=8.5, leading=11),
        "name": ParagraphStyle("PlanName", parent=base["Normal"], fontSize=9.5, leading=12,
                               fontName="Helvetica-Bold"),
        "small": ParagraphStyle("PlanSmall", parent=base["Normal"], fontSize=7.5, leading=10,
                                textColor=MUTED),
        "header": ParagraphStyle("PlanHeader", parent=base["Normal"], fontSize=8, leading=10,
                                 fontName="Helvetica-Bold", textColor=colors.white),
    }


def prescription(exercise: dict) -> str:
    iterations = exercise.get("iterations", {})
    sets = iterations.get("sets", "")
    if iterations.get("duration_seconds"):
        volume = f"{sets} x {iterations['duration_seconds']} s"
    else:
        volume = f"{sets} x {iterations.get('reps', '')}"
    tempo = iterations.get("tempo")
    return f"{volume}<br/><font size=7 color='#5a5a5a'>tempo {clean(tempo)}</font>" if tempo else volume


def exercise_cell(exercise: dict, style: dict) -> list:
    """Name, then the detail lines that aren't step-by-step instructions."""
    parts = [Paragraph(clean(exercise.get("name")), style["name"])]
    meta = " · ".join(filter(None, [clean(exercise.get("category")),
                                    clean(exercise.get("difficulty", "")).title(),
                                    clean(exercise.get("movement_pattern"))]))
    if meta:
        parts.append(Paragraph(meta, style["small"]))
    for label, key in (("Easier", "easier_variation"), ("Harder", "harder_variation")):
        if exercise.get(key):
            parts.append(Paragraph(f"<b>{label}:</b> {clean(exercise[key])}", style["small"]))
    tips = "; ".join(clean(tip).rstrip(".") for tip in exercise.get("safety_tips", []))
    if tips:
        parts.append(Paragraph(f"<b>Safety:</b> {tips}", style["small"]))
    return parts


def day_table(exercises: list[dict], style: dict) -> Table:
    header = [Paragraph(text, style["header"])
              for text in ("Exercise", "Sets x reps", "Rest", "Equipment", "Targets")]
    rows = [header]
    for exercise in exercises:
        equipment = ", ".join(clean(item) for item in exercise.get("equipment", [])) or "None"
        optional = ", ".join(clean(item) for item in exercise.get("optional_equipment", []))
        if optional:
            equipment += f"<br/><font size=7 color='#5a5a5a'>optional: {optional}</font>"
        rows.append([
            exercise_cell(exercise, style),
            Paragraph(prescription(exercise), style["cell"]),
            Paragraph(f"{exercise.get('iterations', {}).get('rest_seconds', '')} s", style["cell"]),
            Paragraph(equipment, style["cell"]),
            Paragraph(", ".join(clean(m) for m in exercise.get("target_muscles", [])), style["cell"]),
        ])

    table = Table(rows, colWidths=[62 * mm, 22 * mm, 13 * mm, 40 * mm, 33 * mm], repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), ACCENT),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("LINEBELOW", (0, 1), (-1, -2), 0.4, RULE),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f4f7f7")]),
        ("BOX", (0, 0), (-1, -1), 0.6, RULE),
    ]))
    return table


def build_plan_pdf(plan: dict, subtitle: str = "") -> bytes:
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        leftMargin=15 * mm, rightMargin=15 * mm, topMargin=15 * mm, bottomMargin=15 * mm,
        title="HomeFit training plan", author="HomeFit",
    )
    style = styles()
    story = [Paragraph("Your training plan", style["title"])]
    header_line = f"Generated {date.today().isoformat()}"
    if subtitle:
        header_line += f" &middot; {clean(subtitle)}"
    story += [Paragraph(header_line, style["subtitle"]), Spacer(1, 4)]

    for day, exercises in group_by_day(plan.get("exercises", [])).items():
        count = f"{len(exercises)} exercise{'s' if len(exercises) != 1 else ''}"
        story.append(KeepTogether([
            Paragraph(f"{clean(day)} <font size=9 color='#5a5a5a'>&middot; {count}</font>",
                      style["day"]),
            day_table(exercises, style),
        ]))

    story += [
        Spacer(1, 10),
        Paragraph("Not medical advice. Stop if you feel pain, and check that furniture is stable "
                  "before loading it.", style["small"]),
    ]
    doc.build(story)
    return buffer.getvalue()
