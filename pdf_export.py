"""Render a generated plan as a printable PDF — every day, minus the step-by-step instructions."""
from datetime import date
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.platypus import (KeepTogether, Paragraph, SimpleDocTemplate, Spacer, Table,
                                TableStyle)

from core import group_by_day
from i18n import t

ACCENT = colors.HexColor("#2f5d62")
MUTED = colors.HexColor("#5a5a5a")
RULE = colors.HexColor("#d5dbdb")

# The built-in Helvetica fonts cover WinAnsi only — swap the few characters that fall
# outside it. Korean text instead switches to a CJK font (see _korean_font_name below),
# which doesn't need this substitution.
UNSUPPORTED = {"→": "->", "←": "<-", "≥": ">=", "≤": "<=", "–": "-", "…": "...",
               "’": "'", "‘": "'", "“": '"', "”": '"'}

# One of reportlab's built-in CJK fonts — no font file to ship, just font metrics.
KOREAN_FONT = "HYSMyeongJo-Medium"
_korean_font_registered = False


def _korean_font_name() -> str:
    global _korean_font_registered
    if not _korean_font_registered:
        pdfmetrics.registerFont(UnicodeCIDFont(KOREAN_FONT))
        _korean_font_registered = True
    return KOREAN_FONT


def clean(text, language: str = "en") -> str:
    text = str(text if text is not None else "")
    if language == "ko":
        return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    for character, replacement in UNSUPPORTED.items():
        text = text.replace(character, replacement)
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def styles(language: str = "en") -> dict:
    base = getSampleStyleSheet()
    # The bundled CJK font ships one weight only, so bold styles fall back to it too.
    body_font = _korean_font_name() if language == "ko" else "Helvetica"
    bold_font = _korean_font_name() if language == "ko" else "Helvetica-Bold"
    return {
        "title": ParagraphStyle("PlanTitle", parent=base["Title"], fontSize=20, leading=24,
                                alignment=TA_LEFT, textColor=ACCENT, spaceAfter=2,
                                fontName=bold_font),
        "subtitle": ParagraphStyle("PlanSubtitle", parent=base["Normal"], fontSize=9.5,
                                   leading=13, textColor=MUTED, fontName=body_font),
        "day": ParagraphStyle("PlanDay", parent=base["Heading2"], fontSize=13, leading=16,
                              textColor=ACCENT, spaceBefore=10, spaceAfter=4, fontName=bold_font),
        "cell": ParagraphStyle("PlanCell", parent=base["Normal"], fontSize=8.5, leading=11,
                               fontName=body_font),
        "name": ParagraphStyle("PlanName", parent=base["Normal"], fontSize=9.5, leading=12,
                               fontName=bold_font),
        "small": ParagraphStyle("PlanSmall", parent=base["Normal"], fontSize=7.5, leading=10,
                                textColor=MUTED, fontName=body_font),
        "header": ParagraphStyle("PlanHeader", parent=base["Normal"], fontSize=8, leading=10,
                                 fontName=bold_font, textColor=colors.white),
    }


def prescription(exercise: dict, language: str = "en") -> str:
    iterations = exercise.get("iterations", {})
    sets = iterations.get("sets", "")
    if iterations.get("duration_seconds"):
        volume = t("prescription_duration", lang=language, sets=sets,
                   seconds=iterations["duration_seconds"])
    else:
        volume = t("prescription_reps", lang=language, sets=sets, reps=iterations.get("reps", ""))
    tempo = iterations.get("tempo")
    return (f"{volume}<br/><font size=7 color='#5a5a5a'>tempo {clean(tempo, language)}</font>"
            if tempo else volume)


def exercise_cell(exercise: dict, style: dict, language: str = "en") -> list:
    """Name, then the detail lines that aren't step-by-step instructions."""
    parts = [Paragraph(clean(exercise.get("name"), language), style["name"])]
    meta = " · ".join(filter(None, [clean(exercise.get("category"), language),
                                    clean(exercise.get("difficulty", ""), language).title(),
                                    clean(exercise.get("movement_pattern"), language)]))
    if meta:
        parts.append(Paragraph(meta, style["small"]))
    labels = (t("pdf_easier", lang=language), t("pdf_harder", lang=language))
    for label, key in zip(labels, ("easier_variation", "harder_variation")):
        if exercise.get(key):
            parts.append(Paragraph(f"<b>{label}:</b> {clean(exercise[key], language)}", style["small"]))
    tips = "; ".join(clean(tip, language).rstrip(".") for tip in exercise.get("safety_tips", []))
    if tips:
        parts.append(Paragraph(f"<b>{t('pdf_safety', lang=language)}:</b> {tips}", style["small"]))
    return parts


def day_table(exercises: list[dict], style: dict, language: str = "en") -> Table:
    header = [Paragraph(text, style["header"]) for text in (
        t("pdf_header_exercise", lang=language), t("pdf_header_sets_reps", lang=language),
        t("pdf_header_rest", lang=language), t("pdf_header_equipment", lang=language),
        t("pdf_header_targets", lang=language),
    )]
    rows = [header]
    for exercise in exercises:
        equipment = (", ".join(clean(item, language) for item in exercise.get("equipment", []))
                    or t("pdf_none", lang=language))
        optional = ", ".join(clean(item, language) for item in exercise.get("optional_equipment", []))
        if optional:
            equipment += (f"<br/><font size=7 color='#5a5a5a'>"
                          f"{t('pdf_optional', lang=language, items=optional)}</font>")
        rest = exercise.get("iterations", {}).get("rest_seconds", "")
        rest_text = f"{rest}초" if language == "ko" else f"{rest} s"
        rows.append([
            exercise_cell(exercise, style, language),
            Paragraph(prescription(exercise, language), style["cell"]),
            Paragraph(rest_text, style["cell"]),
            Paragraph(equipment, style["cell"]),
            Paragraph(", ".join(clean(m, language) for m in exercise.get("target_muscles", [])),
                      style["cell"]),
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


def build_plan_pdf(plan: dict, subtitle: str = "", language: str = "en") -> bytes:
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        leftMargin=15 * mm, rightMargin=15 * mm, topMargin=15 * mm, bottomMargin=15 * mm,
        title="HomeFit training plan", author="HomeFit",
    )
    style = styles(language)
    story = [Paragraph(t("pdf_title", lang=language), style["title"])]
    header_line = t("pdf_generated", lang=language, date=date.today().isoformat())
    if subtitle:
        header_line += f" &middot; {clean(subtitle, language)}"
    story += [Paragraph(header_line, style["subtitle"]), Spacer(1, 4)]

    for day, exercises in group_by_day(plan.get("exercises", []), language=language).items():
        count = t("pdf_exercise_count", lang=language, n=len(exercises),
                  plural="" if len(exercises) == 1 else "s")
        story.append(KeepTogether([
            Paragraph(f"{clean(day, language)} <font size=9 color='#5a5a5a'>&middot; {count}</font>",
                      style["day"]),
            day_table(exercises, style, language),
        ]))

    story += [
        Spacer(1, 10),
        Paragraph(t("pdf_disclaimer", lang=language), style["small"]),
    ]
    doc.build(story)
    return buffer.getvalue()
