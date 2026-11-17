import os
import textwrap
import logging
from typing import Tuple, Optional, List, Dict
from PIL import Image, ImageDraw, ImageFont
import ytdebunk.settings as settings

logger = logging.getLogger(__name__)

# Modern theme color palette (HEX & RGB)
COLOR_BG = (15, 23, 42)          # Deep Slate #0F172A
COLOR_CARD = (30, 41, 59)        # Card Background #1E293B
COLOR_BORDER = (51, 65, 85)      # Card Border #334155
COLOR_PRIMARY = (56, 189, 248)   # Sky Blue #38BDF8
COLOR_TEXT_WHITE = (248, 250, 252) # Slate 50
COLOR_TEXT_MUTED = (148, 163, 184) # Slate 400
COLOR_TEXT_GOLD = (251, 191, 36) # Amber 400

VERACITY_COLORS = {
    "False": (239, 68, 68),          # Red 500
    "Misleading": (249, 115, 22),    # Orange 500
    "Unsubstantiated": (100, 116, 139), # Slate 500
    "Mostly True": (16, 185, 129),   # Emerald 500
    "True": (34, 197, 94),           # Green 500
    "Half True": (234, 179, 8)       # Yellow 500
}

def get_dimensions(aspect_ratio: str = "landscape") -> Tuple[int, int]:
    """
    Returns (width, height) resolution for video canvas.
    """
    if (aspect_ratio or "").lower() in ["vertical", "portrait", "shorts", "9:16"]:
        return (720, 1280)
    return (1280, 720)

def is_bengali_text(text: Optional[str]) -> bool:
    """
    Checks if a string contains any Bengali Unicode characters (U+0980 - U+09FF).
    """
    if not text:
        return False
    return any('\u0980' <= ch <= '\u09ff' for ch in str(text))

BENGALI_FONT_CANDIDATES = [
    # Windows Bengali Fonts
    "C:/Windows/Fonts/kalpurush.ttf",
    "kalpurush.ttf",
    "C:/Windows/Fonts/Siyamrupali.ttf",
    "Siyamrupali.ttf",
    "C:/Windows/Fonts/Nirmala.ttc",
    "Nirmala.ttc",
    "C:/Windows/Fonts/vrinda.ttf",
    "C:/Windows/Fonts/vrindab.ttf",
    "C:/Windows/Fonts/shonar.ttf",
    # Linux Bengali Fonts
    "/usr/share/fonts/truetype/noto/NotoSansBengali-Regular.ttf",
    "/usr/share/fonts/opentype/noto/NotoSansBengali-Regular.otf",
    "/usr/share/fonts/truetype/lohit-bengali/Lohit-Bengali.ttf",
    "/usr/share/fonts/truetype/freefont/FreeSerif.ttf",
    # macOS Bengali Fonts
    "/System/Library/Fonts/KohinoorBangla.ttc",
    "/Library/Fonts/Bangla MN.ttc",
    "/Library/Fonts/Bangla Sangam MN.ttc"
]

STANDARD_FONT_CANDIDATES = [
    "arial.ttf", "segoeui.ttf", "calibri.ttf", "tahoma.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/System/Library/Fonts/Helvetica.ttc"
]

def _get_font(size: int, language: str = "en", text: Optional[str] = None):
    """
    Attempts to load a standard scalable TTF font or falls back to PIL default font.
    If Bengali text or language is detected, prioritizes Unicode Bengali fonts.
    """
    is_bn = (language or "").lower() in ["bn", "bengali", "bangla"] or is_bengali_text(text)
    if is_bn:
        font_candidates = BENGALI_FONT_CANDIDATES + STANDARD_FONT_CANDIDATES
    else:
        font_candidates = STANDARD_FONT_CANDIDATES + BENGALI_FONT_CANDIDATES

    for font_name in font_candidates:
        try:
            return ImageFont.truetype(font_name, size)
        except Exception:
            continue
    return ImageFont.load_default()

def _draw_rounded_rectangle(draw: ImageDraw.ImageDraw, box, radius=16, fill=None, outline=None, width=1):
    """
    Draws a rounded rectangle on the given ImageDraw context.
    """
    try:
        draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)
    except AttributeError:
        # Fallback for older PIL
        draw.rectangle(box, fill=fill, outline=outline, width=width)

def create_intro_card(
    video_title: str,
    persona: str = "skeptic",
    language: str = "en",
    aspect_ratio: str = "landscape",
    output_path: Optional[str] = None
) -> str:
    """
    Renders the opening studio title card.
    """
    w, h = get_dimensions(aspect_ratio)
    img = Image.new("RGB", (w, h), color=COLOR_BG)
    draw = ImageDraw.Draw(img)

    # Accent decorative bar on top
    draw.rectangle([0, 0, w, 8], fill=COLOR_PRIMARY)

    # Central Card
    margin_x = int(w * 0.08)
    margin_y = int(h * 0.12)
    card_box = [margin_x, margin_y, w - margin_x, h - margin_y]
    _draw_rounded_rectangle(draw, card_box, radius=20, fill=COLOR_CARD, outline=COLOR_BORDER, width=2)

    font_badge = _get_font(int(min(w, h) * 0.035), language=language)
    font_title = _get_font(int(min(w, h) * 0.055), language=language, text=video_title)
    font_sub = _get_font(int(min(w, h) * 0.035), language=language)

    # Top Studio Badge
    badge_text = "AI DEBUNKER STUDIO"
    draw.text((w // 2, margin_y + 40), badge_text, font=font_badge, fill=COLOR_PRIMARY, anchor="mm")

    # Video Title wrapped
    title = video_title or "Video Analysis"
    wrap_width = 30 if aspect_ratio == "vertical" else 45
    wrapped_lines = textwrap.wrap(title, width=wrap_width)[:3]
    y_offset = margin_y + 110
    for line in wrapped_lines:
        draw.text((w // 2, y_offset), line, font=font_title, fill=COLOR_TEXT_WHITE, anchor="mm")
        y_offset += int(min(w, h) * 0.07)

    # Persona host tag
    persona_label = f"Host: The {persona.capitalize()}"
    draw.text((w // 2, card_box[3] - 70), persona_label, font=font_sub, fill=COLOR_TEXT_GOLD, anchor="mm")
    draw.text((w // 2, card_box[3] - 35), "Automated Fact-Checking & Evidence Verification", font=font_badge, fill=COLOR_TEXT_MUTED, anchor="mm")

    out_file = output_path or os.path.join(getattr(settings, 'GRAPHICS_DIR', 'output/graphics'), "intro_card.png")
    os.makedirs(os.path.dirname(os.path.abspath(out_file)), exist_ok=True)
    img.save(out_file)
    return out_file

def create_claim_card(
    claim_id: int,
    quote: str,
    claim_text: str,
    veracity: str,
    fallacy: Optional[str] = None,
    aspect_ratio: str = "landscape",
    output_path: Optional[str] = None,
    language: str = "en"
) -> str:
    """
    Renders an original claim card with quotation and veracity badge.
    """
    w, h = get_dimensions(aspect_ratio)
    img = Image.new("RGB", (w, h), color=COLOR_BG)
    draw = ImageDraw.Draw(img)

    draw.rectangle([0, 0, w, 8], fill=COLOR_TEXT_GOLD)

    margin_x = int(w * 0.06)
    margin_y = int(h * 0.08)
    card_box = [margin_x, margin_y, w - margin_x, h - margin_y]
    _draw_rounded_rectangle(draw, card_box, radius=18, fill=COLOR_CARD, outline=COLOR_BORDER, width=2)

    sample_text = quote or claim_text or ""
    font_header = _get_font(int(min(w, h) * 0.038), language=language)
    font_quote = _get_font(int(min(w, h) * 0.045), language=language, text=sample_text)
    font_badge = _get_font(int(min(w, h) * 0.04), language=language)
    font_meta = _get_font(int(min(w, h) * 0.032), language=language, text=fallacy)

    # Header
    draw.text((margin_x + 30, margin_y + 35), f"ORIGINAL STATEMENT #{claim_id}", font=font_header, fill=COLOR_TEXT_GOLD, anchor="lm")

    # Veracity Pill Badge in top right
    veracity_color = VERACITY_COLORS.get(veracity, COLOR_PRIMARY)
    badge_w = 170
    badge_h = 36
    badge_x = card_box[2] - 30 - badge_w
    badge_y = margin_y + 18
    _draw_rounded_rectangle(draw, [badge_x, badge_y, badge_x + badge_w, badge_y + badge_h], radius=8, fill=veracity_color)
    draw.text((badge_x + badge_w // 2, badge_y + badge_h // 2), veracity.upper(), font=font_badge, fill=COLOR_TEXT_WHITE, anchor="mm")

    # Quoted text
    wrap_w = 28 if aspect_ratio == "vertical" else 44
    quote_text = f"\"{quote}\"" if quote else f"\"{claim_text}\""
    wrapped_lines = textwrap.wrap(quote_text, width=wrap_w)[:5]

    y = margin_y + 110
    for line in wrapped_lines:
        draw.text((margin_x + 40, y), line, font=font_quote, fill=COLOR_TEXT_WHITE, anchor="lm")
        y += int(min(w, h) * 0.065)

    # Fallacy or assertion badge
    if fallacy and fallacy.lower() not in ["none", ""]:
        fallacy_text = f"Logical Fallacy: {fallacy}"
        _draw_rounded_rectangle(draw, [margin_x + 30, card_box[3] - 70, card_box[2] - 30, card_box[3] - 25], radius=8, fill=(69, 10, 10), outline=(220, 38, 38), width=1)
        draw.text((w // 2, card_box[3] - 47), fallacy_text, font=font_meta, fill=(254, 202, 202), anchor="mm")

    out_file = output_path or os.path.join(getattr(settings, 'GRAPHICS_DIR', 'output/graphics'), f"claim_{claim_id}.png")
    os.makedirs(os.path.dirname(os.path.abspath(out_file)), exist_ok=True)
    img.save(out_file)
    return out_file

def create_rebuttal_card(
    claim_id: int,
    rebuttal_text: str,
    veracity: str,
    source: Optional[str] = None,
    visual_cue: Optional[str] = None,
    aspect_ratio: str = "landscape",
    output_path: Optional[str] = None,
    language: str = "en"
) -> str:
    """
    Renders the debunker character's rebuttal card with veracity badge and source citation.
    """
    w, h = get_dimensions(aspect_ratio)
    img = Image.new("RGB", (w, h), color=COLOR_BG)
    draw = ImageDraw.Draw(img)

    veracity_color = VERACITY_COLORS.get(veracity, COLOR_PRIMARY)
    draw.rectangle([0, 0, w, 8], fill=veracity_color)

    margin_x = int(w * 0.06)
    margin_y = int(h * 0.08)
    card_box = [margin_x, margin_y, w - margin_x, h - margin_y]
    _draw_rounded_rectangle(draw, card_box, radius=18, fill=COLOR_CARD, outline=COLOR_BORDER, width=2)

    font_header = _get_font(int(min(w, h) * 0.038), language=language)
    font_text = _get_font(int(min(w, h) * 0.044), language=language, text=rebuttal_text)
    font_badge = _get_font(int(min(w, h) * 0.04), language=language)
    font_citation = _get_font(int(min(w, h) * 0.032), language=language, text=source)

    # Header
    draw.text((margin_x + 30, margin_y + 35), f"DEBUNKER REBUTTAL #{claim_id}", font=font_header, fill=COLOR_PRIMARY, anchor="lm")

    # Veracity Badge
    badge_w = 170
    badge_h = 36
    badge_x = card_box[2] - 30 - badge_w
    badge_y = margin_y + 18
    _draw_rounded_rectangle(draw, [badge_x, badge_y, badge_x + badge_w, badge_y + badge_h], radius=8, fill=veracity_color)
    draw.text((badge_x + badge_w // 2, badge_y + badge_h // 2), veracity.upper(), font=font_badge, fill=COLOR_TEXT_WHITE, anchor="mm")

    # Rebuttal Body
    wrap_w = 28 if aspect_ratio == "vertical" else 46
    wrapped_lines = textwrap.wrap(rebuttal_text, width=wrap_w)[:6]

    y = margin_y + 110
    for line in wrapped_lines:
        draw.text((margin_x + 40, y), line, font=font_text, fill=COLOR_TEXT_WHITE, anchor="lm")
        y += int(min(w, h) * 0.065)

    # Citation / Source Footer
    if source:
        cite_text = f"Source: {source[:55]}..." if len(source) > 55 else f"Source: {source}"
        draw.text((margin_x + 40, card_box[3] - 40), cite_text, font=font_citation, fill=COLOR_TEXT_MUTED, anchor="lm")

    out_file = output_path or os.path.join(getattr(settings, 'GRAPHICS_DIR', 'output/graphics'), f"rebuttal_{claim_id}.png")
    os.makedirs(os.path.dirname(os.path.abspath(out_file)), exist_ok=True)
    img.save(out_file)
    return out_file

def create_scorecard_card(
    score: float,
    summary: str,
    fallacies: List[str],
    aspect_ratio: str = "landscape",
    output_path: Optional[str] = None,
    language: str = "en"
) -> str:
    """
    Renders the final veracity scorecard and executive verdict.
    """
    w, h = get_dimensions(aspect_ratio)
    img = Image.new("RGB", (w, h), color=COLOR_BG)
    draw = ImageDraw.Draw(img)

    score_color = (16, 185, 129) if score >= 70 else ((249, 115, 22) if score >= 40 else (239, 68, 68))
    draw.rectangle([0, 0, w, 8], fill=score_color)

    margin_x = int(w * 0.08)
    margin_y = int(h * 0.10)
    card_box = [margin_x, margin_y, w - margin_x, h - margin_y]
    _draw_rounded_rectangle(draw, card_box, radius=20, fill=COLOR_CARD, outline=COLOR_BORDER, width=2)

    font_header = _get_font(int(min(w, h) * 0.038), language=language)
    font_score = _get_font(int(min(w, h) * 0.12), language=language)
    font_verdict = _get_font(int(min(w, h) * 0.045), language=language)
    font_summary = _get_font(int(min(w, h) * 0.035), language=language, text=summary)

    # Top Header
    draw.text((w // 2, margin_y + 40), "FINAL FACT-CHECK VERDICT", font=font_header, fill=COLOR_PRIMARY, anchor="mm")

    # Big Score
    draw.text((w // 2, margin_y + 130), f"{score:.0f}%", font=font_score, fill=score_color, anchor="mm")
    verdict_text = "VERIFIED ACCURATE" if score >= 70 else ("PARTIALLY MISLEADING" if score >= 40 else "HIGHLY UNRELIABLE")
    draw.text((w // 2, margin_y + 195), verdict_text, font=font_verdict, fill=COLOR_TEXT_WHITE, anchor="mm")

    # Summary snippet
    wrap_w = 30 if aspect_ratio == "vertical" else 48
    wrapped = textwrap.wrap(summary, width=wrap_w)[:3]
    y = margin_y + 260
    for line in wrapped:
        draw.text((w // 2, y), line, font=font_summary, fill=COLOR_TEXT_MUTED, anchor="mm")
        y += int(min(w, h) * 0.055)

    # Call to action
    cta = "Think Critically • Demand Verification • Share Facts"
    draw.text((w // 2, card_box[3] - 40), cta, font=font_header, fill=COLOR_TEXT_GOLD, anchor="mm")

    out_file = output_path or os.path.join(getattr(settings, 'GRAPHICS_DIR', 'output/graphics'), "scorecard.png")
    os.makedirs(os.path.dirname(os.path.abspath(out_file)), exist_ok=True)
    img.save(out_file)
    return out_file

def generate_all_graphics(
    report,
    script,
    aspect_ratio: str = "landscape",
    output_dir: Optional[str] = None
) -> Dict[str, str]:
    """
    Renders all graphics cards required by the timeline sheet.
    Returns mapping of card keys to image file paths.
    """
    out_dir = output_dir or getattr(settings, 'GRAPHICS_DIR', os.path.join(settings.OUTPUT_DIRECTORY, 'graphics'))
    os.makedirs(out_dir, exist_ok=True)
    cards = {}

    lang = getattr(script, 'language', None) or getattr(report, 'language', None) or "en"

    # 1. Intro Card
    cards["intro"] = create_intro_card(
        video_title=report.video_title or script.video_title or "Debunk Studio",
        persona=script.persona,
        language=lang,
        aspect_ratio=aspect_ratio,
        output_path=os.path.join(out_dir, "intro_card.png")
    )

    # 2. Claim and Rebuttal Cards
    segments_by_claim = {s.claim_id: s for s in script.segments if s.claim_id is not None}

    for idx, claim in enumerate(report.claims, start=1):
        seg = segments_by_claim.get(claim.id)
        if seg is None and idx <= len(script.segments):
            seg = script.segments[idx - 1]

        claim_key = f"claim_{claim.id}"
        cards[claim_key] = create_claim_card(
            claim_id=claim.id,
            quote=claim.original_quote,
            claim_text=claim.claim_text,
            veracity=claim.veracity,
            fallacy=claim.fallacy_type,
            aspect_ratio=aspect_ratio,
            output_path=os.path.join(out_dir, f"claim_{claim.id}.png"),
            language=lang
        )

        rebuttal_key = f"rebuttal_{claim.id}"
        rebuttal_text = seg.rebuttal_text if seg else (claim.counter_argument or claim.evidence_summary)
        source_url = claim.sources[0] if claim.sources else None
        cue = seg.visual_cue if seg else None

        cards[rebuttal_key] = create_rebuttal_card(
            claim_id=claim.id,
            rebuttal_text=rebuttal_text,
            veracity=claim.veracity,
            source=source_url,
            visual_cue=cue,
            aspect_ratio=aspect_ratio,
            output_path=os.path.join(out_dir, f"rebuttal_{claim.id}.png"),
            language=lang
        )

    # 3. Final Scorecard Card
    cards["outro"] = create_scorecard_card(
        score=report.overall_veracity_score,
        summary=report.summary,
        fallacies=report.fallacies_found,
        aspect_ratio=aspect_ratio,
        output_path=os.path.join(out_dir, "scorecard.png"),
        language=lang
    )

    return cards
