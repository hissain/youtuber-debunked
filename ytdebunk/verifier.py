import os
import json
import logging
import datetime
from typing import List, Dict, Optional, Any
from ytdebunk.schema import DebunkReport, ClaimVerification, ClaimType, VeracityRating, FallacyType
import ytdebunk.settings as settings

logger = logging.getLogger(__name__)

try:
    from ddgs import DDGS
except ImportError:
    try:
        from duckduckgo_search import DDGS  # type: ignore
    except ImportError:
        DDGS = None

def search_ddg(query: str, max_results: int = 3) -> List[Dict[str, str]]:
    """
    Executes a zero-cost web search using DDGS to retrieve live fact-checking evidence.
    Returns a list of dicts with 'title', 'href', and 'snippet'.
    Gracefully returns an empty list if offline or on rate limiting.
    """
    results: List[Dict[str, str]] = []
    if not query or not query.strip() or DDGS is None:
        return results

    try:
        with DDGS() as ddgs:
            raw_results = list(ddgs.text(query.strip(), max_results=max_results))
            for item in raw_results:
                results.append({
                    "title": item.get("title", ""),
                    "href": item.get("href", ""),
                    "snippet": item.get("body", item.get("snippet", ""))
                })
    except Exception as e:
        logger.debug(f"[ytdebunk-verifier] DuckDuckGo search query '{query}' warning: {e}")
    
    return results

def ground_evidence_for_text(text: str, language: str = "en", max_queries: int = 3) -> List[Dict[str, str]]:
    """
    Extracts key searchable phrases or claims from the transcript and retrieves live web evidence.
    """
    evidence: List[Dict[str, str]] = []
    # Extract significant non-trivial sentences or segments for search grounding
    sentences = [s.strip() for s in text.replace('।', '.').split('.') if len(s.strip().split()) >= 4]
    candidate_queries = sentences[:max_queries]

    for q in candidate_queries:
        # Truncate query to 8 words for optimal search retrieval
        short_q = " ".join(q.split()[:8])
        results = search_ddg(short_q, max_results=2)
        evidence.extend(results)

    return evidence

def verify_claims(
    transcription: str,
    key: Optional[str] = None,
    language: str = "en",
    video_url: Optional[str] = None,
    video_title: Optional[str] = None,
    enable_web_search: bool = True,
    verbose: bool = False,
    logger: Optional[logging.Logger] = None
) -> DebunkReport:
    """
    Performs structured claim extraction, logical fallacy identification,
    and agentic web search grounding using Gemini 2.0 / 1.5 Flash.
    Returns a typed DebunkReport and exports to JSON and Markdown.
    """
    log = logger or logging.getLogger(__name__)

    token = key or os.getenv("GEMINI_API_KEY") or os.getenv("GENAI_API_KEY")
    if not token:
        raise ValueError("Gemini API key is required for claim verification and debunk analysis. Provide --token or set GEMINI_API_KEY.")

    if verbose:
        log.info(f"[ytdebunk-verifier] Starting structured claim verification for language={language}...")

    # Step 1: Agentic Web Evidence Grounding
    web_evidence: List[Dict[str, str]] = []
    if enable_web_search:
        if verbose:
            log.info("[ytdebunk-verifier] Gathering live web search evidence via zero-cost grounding...")
        web_evidence = ground_evidence_for_text(transcription, language=language)
        if verbose:
            log.info(f"[ytdebunk-verifier] Retrieved {len(web_evidence)} live search evidence snippets.")

    evidence_context = ""
    if web_evidence:
        evidence_lines = [
            f"- [{e['title']}]({e['href']}): {e['snippet']}"
            for e in web_evidence
        ]
        evidence_context = "\n### Retrieved Web Evidence & Sources:\n" + "\n".join(evidence_lines) + "\n"

    # Step 2: Build Structured Verification Prompt
    system_prompt = (
        "You are an elite, objective, evidence-grounded investigative fact-checker and debunker.\n"
        "Your role is to analyze the provided video transcript, extract every substantive factual claim or argument,\n"
        "evaluate each claim's veracity against established empirical reality and provided web evidence,\n"
        "detect any formal or informal logical fallacies, and provide punchy, reasoned counter-arguments.\n"
        "You MUST return ONLY a valid, parseable JSON object matching the requested schema without markdown backticks."
    )

    schema_instruction = f"""
Return a single JSON object conforming strictly to this schema:
{{
  "video_url": {json.dumps(video_url)},
  "video_title": {json.dumps(video_title)},
  "language": "{language}",
  "summary": "Comprehensive 2-4 sentence executive overview of the video arguments, veracity, and logical integrity.",
  "overall_veracity_score": 65.5,  // float from 0.0 (completely false/fraudulent) to 100.0 (entirely verified)
  "claims": [
    {{
      "id": 1,
      "timestamp_start": "00:10",  // or null if unknown
      "timestamp_end": "00:25",    // or null if unknown
      "original_quote": "Exact quote from transcript",
      "claim_text": "Distilled factual/logical proposition",
      "claim_type": "Factual",  // Factual, Statistical, Causal, Historical, Scientific, Legal, Opinion, Logical, Other
      "veracity": "Misleading",  // True, Mostly True, Half True, Misleading, False, Unsubstantiated
      "confidence_score": 0.85,  // float 0.0 to 1.0
      "is_fallacious": true,
      "fallacy_type": "Straw Man",  // e.g. Straw Man, Ad Hominem, False Dilemma, Hasty Generalization, or None
      "fallacy_explanation": "Explanation of the flawed reasoning",
      "evidence_summary": "Factual counter-evidence explaining reality",
      "sources": ["https://example.com/source"],
      "counter_argument": "Direct, punchy rebuttal for the debunker"
    }}
  ],
  "fallacies_found": ["Straw Man"],
  "created_at": "{datetime.datetime.now(datetime.timezone.utc).isoformat()}"
}}
"""

    user_prompt = f"""
Transcript to analyze ({language}):
\"\"\"
{transcription}
\"\"\"
{evidence_context}

Analyze the transcript thoroughly. Extract between 2 and 6 key claims made by the speaker.
{schema_instruction}
"""

    response_text = ""

    # Step 3: Invoke Gemini API (supports both modern google.genai and legacy google.generativeai)
    try:
        from google import genai
        client = genai.Client(api_key=token)
        # Use gemini-2.5-flash or gemini-1.5-flash
        model_name = "gemini-2.5-flash"
        try:
            resp = client.models.generate_content(
                model=model_name,
                contents=f"{system_prompt}\n\n{user_prompt}",
            )
            response_text = resp.text or ""
        except Exception:
            # Fallback to gemini-1.5-flash
            resp = client.models.generate_content(
                model="gemini-1.5-flash",
                contents=f"{system_prompt}\n\n{user_prompt}",
            )
            response_text = resp.text or ""
    except Exception as e_genai:
        if verbose:
            log.info(f"[ytdebunk-verifier] google.genai unavailable or error ({e_genai}), falling back to google.generativeai...")
        try:
            import google.generativeai as legacy_genai
            legacy_genai.configure(api_key=token)
            model = legacy_genai.GenerativeModel("gemini-1.5-flash")
            resp = model.generate_content(f"{system_prompt}\n\n{user_prompt}")
            response_text = resp.text or ""
        except Exception as e_legacy:
            raise RuntimeError(f"Failed to query Gemini API: {e_legacy}") from e_legacy

    # Step 4: Parse into typed DebunkReport
    report = DebunkReport.from_json_string(response_text)

    # Backfill missing claim timestamps from subtitles if available
    subtitles_file = getattr(settings, 'SUBTITLES_JSON_FILE', os.path.join(settings.OUTPUT_DIRECTORY, 'subtitles.json'))
    if os.path.exists(subtitles_file) and report.claims:
        try:
            with open(subtitles_file, "r", encoding="utf-8") as sf:
                sub_data = json.load(sf)
            from ytdebunk.videomaker import match_quote_to_subtitles
            from ytdebunk.timeline import format_seconds_to_timestamp
            for claim in report.claims:
                if not claim.timestamp_start or not claim.timestamp_end:
                    s_sec, e_sec = match_quote_to_subtitles(claim.original_quote or claim.claim_text, sub_data)
                    if e_sec > s_sec:
                        claim.timestamp_start = format_seconds_to_timestamp(s_sec)
                        claim.timestamp_end = format_seconds_to_timestamp(e_sec)
        except Exception as e_subs:
            if verbose:
                log.debug(f"[ytdebunk-verifier] Could not backfill timestamps from subtitles: {e_subs}")

    # Attach sources from web grounding if claims lack sources
    if web_evidence and report.claims:
        evidence_urls = [e['href'] for e in web_evidence if e.get('href')]
        for claim in report.claims:
            if not claim.sources and evidence_urls:
                claim.sources = evidence_urls[:2]

    # Step 5: Save reports to output directory
    report.save()

    if verbose:
        log.info(f"[ytdebunk-verifier] Generated DebunkReport with {len(report.claims)} claims, score: {report.overall_veracity_score}%.")

    return report
