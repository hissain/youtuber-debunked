import os
import json
import logging
import datetime
from typing import Optional, List, Dict, Any
from ytdebunk.schema import DebunkReport, DebunkScript, ScriptSegment, PersonaType
import ytdebunk.settings as settings

logger = logging.getLogger(__name__)

PERSONA_PROFILES = {
    PersonaType.SKEPTIC.value: {
        "name": "The Witty Skeptic",
        "description": "Engaging, mildly satirical, sharp, conversational, punchy. Exposes logical fallacies and factual leaps with witty comparisons while keeping the tone entertaining.",
        "en_style": (
            "You are The Witty Skeptic debunker. Use punchy, humorous, and relatable analogies. "
            "Highlight the absurdity of ungrounded assertions with smart wit. Keep the audience hooked with conversational phrasing."
        ),
        "bn_style": (
            "তুমি একজন তীক্ষ্ণ এবং রসবোধসম্পন্ন চলিত বাংলা ডিবংকার (The Witty Skeptic)। "
            "কথোপকথনের স্বাভাবিক চলিত ভাষায় যুক্তিহীন দাবিগুলোর অসঙ্গতি তুলে ধরো। "
            "স্বাভাবিক ট্রানজিশন ব্যবহার করো (যেমন: 'একটু দাঁড়ান!', 'শুনলেন কি বললেন?', 'আসলে বাস্তবতা সম্পূর্ণ ভিন্ন')।"
        )
    },
    PersonaType.JOURNALIST.value: {
        "name": "The Analytical Fact-Checker",
        "description": "Calm, objective, rigorous, authoritative, journalistic. Emphasizes empirical evidence, official records, scientific consensus, and verified statistics.",
        "en_style": (
            "You are The Analytical Fact-Checker. Speak in a calm, precise, objective, and authoritative tone. "
            "Present verifiable facts, peer-reviewed data, and official documentation clearly and methodically."
        ),
        "bn_style": (
            "তুমি একজন বস্তুনিষ্ঠ এবং অনুসন্ধানী ফ্যাক্ট-চেকার (The Analytical Fact-Checker)। "
            "শান্ত, তথ্যভিত্তিক এবং প্রমাণনির্ভর চলিত ভাষায় বক্তব্য তুলে ধরো। "
            "যথাযথ তথ্যসূত্র, পরিসংখ্যান এবং বাস্তব প্রমাণের দিকে নজর দাও।"
        )
    },
    PersonaType.EDUCATOR.value: {
        "name": "The Educational Mentor",
        "description": "Warm, patient, pedagogical, clear, encouraging. Explains the underlying principles step-by-step so the viewer understands why the mistake was made and what the truth is.",
        "en_style": (
            "You are The Educational Mentor. Use a patient, warm, and instructional tone. "
            "Explain why the misconception seems appealing initially, then guide the viewer through the real science or logical principle step-by-step."
        ),
        "bn_style": (
            "তুমি একজন শিক্ষণীয় পথপ্রদর্শক (The Educational Mentor)। "
            "সহজ, প্রাঞ্জল ও ধৈর্যশীল চলিত বাংলায় কেন ধারণাটি ভুল এবং এর পেছনের আসল বৈজ্ঞানিক বা বাস্তব কারণটি কী, তা ধাপে ধাপে বুঝিয়ে বলো।"
        )
    }
}

def _generate_template_fallback_script(
    report: DebunkReport,
    persona: str = "skeptic",
    language: str = "en"
) -> DebunkScript:
    """
    Deterministic template-based script generator used when Gemini API token is absent or during offline runs.
    Guarantees that a valid, persona-aligned DebunkScript is always created.
    """
    title = report.video_title or "this video"
    lang = language.lower()
    is_bn = (lang == "bn")

    # Persona-specific hooks and outros
    if persona == PersonaType.SKEPTIC.value:
        if is_bn:
            hook = f"ইন্টারনেটে কত কথাই না শোনা যায়! কিন্তু {title}-এর এই ভিডিওতে যা দাবি করা হয়েছে, তা কি আসলেই সত্যি? চলুন একটু তলিয়ে দেখা যাক!"
            outro = "সবশেষে কথা একটাই—যা-ই দেখবেন, যাচাই না করে বিশ্বাস করবেন না। নিজের বিচারবুদ্ধি ব্যবহার করুন এবং তথ্যের পেছনে ছুটুন!"
        else:
            hook = f"Hold on a second! Before you buy into the claims made in {title}, we need to talk. Are these facts, or just creative fiction? Let's break it down."
            outro = "Remember, extraordinary claims require extraordinary evidence. Always question the premise before sharing! Stay sharp and stay skeptical."
    elif persona == PersonaType.JOURNALIST.value:
        if is_bn:
            hook = f"{title}-এ উত্থাপিত মূল দাবিগুলোর বস্তুনিষ্ঠ সত্যতা যাচাই করতে আমরা তথ্যানুসন্ধান চালিয়েছি। আসুন প্রমাণের ভিত্তিতে বিষয়টি পরীক্ষা করি।"
            outro = "তথ্যানুসন্ধান ও স্বাধীন তথ্যের আলোকে এই ছিল আমাদের বিশ্লেষণ। নির্ভরযোগ্য তথ্যসূত্রের ওপর ভরসা রাখুন এবং ভুল তথ্য প্রতিরোধ করুন।"
        else:
            hook = f"In this investigative report, we evaluate the veracity of the factual assertions made in {title} against verified documentation and peer-reviewed data."
            outro = "Our factual review demonstrates the importance of verifying sources. Consult the cited references below for complete documentation."
    else:  # EDUCATOR
        if is_bn:
            hook = f"অনেক সময় কিছু তথ্য আমাদের কাছে খুব বিশ্বাসযোগ্য মনে হয়। কিন্তু {title}-এর দাবিগুলো কি বৈজ্ঞানিক সত্যের সাথে মেলে? চলুন সহজভাবে শিখে নেওয়া যাক।"
            outro = "ভুল ধারণা দূর করার সেরা উপায় হলো শেখার আগ্রহ রাখা। নতুন কিছু জানতে এবং সঠিক তথ্যে সমৃদ্ধ হতে আমাদের সাথেই থাকুন।"
        else:
            hook = f"Welcome! Today we are taking a closer look at {title} to understand the fascinating science and principles behind these widespread claims."
            outro = "Critical thinking is a muscle that gets stronger the more we practice. Keep asking questions and keep learning!"

    segments: List[ScriptSegment] = []
    for idx, claim in enumerate(report.claims, start=1):
        original_quote = claim.original_quote or claim.claim_text
        counter = claim.counter_argument or claim.evidence_summary

        if is_bn:
            if persona == PersonaType.SKEPTIC.value:
                rebuttal = f"প্রথমেই দাবি করা হয়েছে: '{claim.claim_text}'। শুনুন, শুনতে ভালো লাগলেও আসল সত্য হলো: {counter}"
            elif persona == PersonaType.JOURNALIST.value:
                rebuttal = f"দাবি #{idx}-এ বলা হয়েছে: '{claim.claim_text}'। সরকারি ও বৈজ্ঞানিক তথ্য বিশ্লেষণ করে দেখা গেছে: {counter}"
            else:
                rebuttal = f"আসুন এই বিষয়টি বোঝা যাক: '{claim.claim_text}'। অনেকের কাছে এটা সত্যি মনে হতে পারে, কিন্তু বাস্তব তথ্য হলো: {counter}"
            cue = f"দাবি #{idx} স্কোরকার্ড প্রদর্শন ({claim.veracity})"
        else:
            if persona == PersonaType.SKEPTIC.value:
                rebuttal = f"The speaker boldly claims that '{claim.claim_text}'. But here's the catch: {counter}"
            elif persona == PersonaType.JOURNALIST.value:
                rebuttal = f"Regarding claim #{idx}—'{claim.claim_text}'—our empirical review reveals: {counter}"
            else:
                rebuttal = f"Let's look at why someone might believe '{claim.claim_text}'. While intuitive, actual evidence demonstrates: {counter}"
            cue = f"Show claim #{idx} badge ({claim.veracity})"

        segments.append(
            ScriptSegment(
                segment_id=idx,
                claim_id=claim.id,
                timestamp_start=claim.timestamp_start,
                timestamp_end=claim.timestamp_end,
                speaker_quote=original_quote,
                rebuttal_text=rebuttal,
                visual_cue=cue
            )
        )

    script = DebunkScript(
        video_url=report.video_url,
        video_title=report.video_title,
        language=language,
        persona=persona,
        hook=hook,
        segments=segments,
        outro=outro
    )
    script.full_narration = script.get_full_narration()
    return script

def generate_debunk_script(
    report: DebunkReport,
    persona: str = PersonaType.SKEPTIC.value,
    key: Optional[str] = None,
    language: Optional[str] = None,
    verbose: bool = False,
    logger: Optional[logging.Logger] = None
) -> DebunkScript:
    """
    Transforms a structured DebunkReport into a captivating, persona-driven spoken script
    for a virtual debunker character.
    Supports Skeptic, Journalist, and Educator personas in both English and Bengali.
    """
    log = logger or logging.getLogger(__name__)
    persona_key = persona.lower() if persona else PersonaType.SKEPTIC.value
    if persona_key not in PERSONA_PROFILES:
        persona_key = PersonaType.SKEPTIC.value

    lang = language or report.language or "en"
    token = key or os.getenv("GEMINI_API_KEY") or os.getenv("GENAI_API_KEY")

    if verbose:
        log.info(f"[ytdebunk-scriptwriter] Generating debunker script with persona '{persona_key}' (Language: {lang})...")

    # If no token is available, seamlessly use high-quality template-based generator
    if not token:
        if verbose:
            log.info("[ytdebunk-scriptwriter] No Gemini token provided. Using deterministic persona template generator.")
        script = _generate_template_fallback_script(report, persona=persona_key, language=lang)
        script.save()
        return script

    profile = PERSONA_PROFILES[persona_key]
    style_instruction = profile["bn_style"] if lang == "bn" else profile["en_style"]

    claims_summary = []
    for c in report.claims:
        claims_summary.append({
            "claim_id": c.id,
            "timestamp_start": c.timestamp_start or "00:00",
            "timestamp_end": c.timestamp_end or "00:30",
            "quote": c.original_quote,
            "claim_text": c.claim_text,
            "veracity": c.veracity,
            "is_fallacious": c.is_fallacious,
            "fallacy_type": c.fallacy_type,
            "evidence": c.evidence_summary,
            "counter_argument": c.counter_argument or c.evidence_summary
        })

    system_prompt = (
        f"You are a master YouTube debunker scriptwriter writing for persona: '{profile['name']}'.\n"
        f"{style_instruction}\n\n"
        "Your task: Convert the provided verified claims into a cohesive, spoken script for a video debunking voiceover.\n"
        "Requirements:\n"
        "1. Hook: Catchy, punchy opening hook introducing the topic.\n"
        "2. Segments: For each claim, write a direct spoken rebuttal referencing the speaker's claim, exposing the flaw/evidence, and include visual cues.\n"
        "3. Outro: Strong closing remark encouraging critical thinking.\n"
        "4. Return ONLY a valid JSON object matching the requested schema without markdown backticks."
    )

    schema_instruction = f"""
Return a single JSON object strictly matching this schema:
{{
  "video_url": {json.dumps(report.video_url)},
  "video_title": {json.dumps(report.video_title)},
  "language": "{lang}",
  "persona": "{persona_key}",
  "hook": "Spoken opening hook text",
  "segments": [
    {{
      "segment_id": 1,
      "claim_id": 1,
      "timestamp_start": "00:10",
      "timestamp_end": "00:30",
      "speaker_quote": "Exact quote being rebutted",
      "rebuttal_text": "Spoken debunker rebuttal narration",
      "visual_cue": "Visual direction e.g. Display 'FALSE' badge and citation"
    }}
  ],
  "outro": "Spoken closing remarks",
  "created_at": "{datetime.datetime.now(datetime.timezone.utc).isoformat()}"
}}
"""

    user_prompt = f"""
Executive Summary: {report.summary}
Overall Veracity Score: {report.overall_veracity_score}%
Claims to Debunk:
{json.dumps(claims_summary, ensure_ascii=False, indent=2)}

Write the full spoken script in {'Bengali (চলিত বাংলা)' if lang == 'bn' else 'English'}.
{schema_instruction}
"""

    response_text = ""
    try:
        from google import genai
        client = genai.Client(api_key=token)
        try:
            resp = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=f"{system_prompt}\n\n{user_prompt}",
            )
            response_text = resp.text or ""
        except Exception:
            resp = client.models.generate_content(
                model="gemini-1.5-flash",
                contents=f"{system_prompt}\n\n{user_prompt}",
            )
            response_text = resp.text or ""
    except Exception as e_genai:
        if verbose:
            log.info(f"[ytdebunk-scriptwriter] google.genai error ({e_genai}), attempting google.generativeai...")
        try:
            import google.generativeai as legacy_genai
            legacy_genai.configure(api_key=token)
            model = legacy_genai.GenerativeModel("gemini-1.5-flash")
            resp = model.generate_content(f"{system_prompt}\n\n{user_prompt}")
            response_text = resp.text or ""
        except Exception as e_legacy:
            if verbose:
                log.warning(f"[ytdebunk-scriptwriter] LLM generation failed ({e_legacy}). Using template fallback.")
            script = _generate_template_fallback_script(report, persona=persona_key, language=lang)
            script.save()
            return script

    try:
        script = DebunkScript.from_json_string(response_text)
    except Exception as e_parse:
        if verbose:
            log.warning(f"[ytdebunk-scriptwriter] JSON parsing failed ({e_parse}). Falling back to template script.")
        script = _generate_template_fallback_script(report, persona=persona_key, language=lang)

    script.full_narration = script.get_full_narration()
    script.save()

    if verbose:
        log.info(f"[ytdebunk-scriptwriter] Debunker script generated with {len(script.segments)} segments.")

    return script
