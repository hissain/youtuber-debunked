import os
import re
import json
import datetime
from enum import Enum
from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field
import ytdebunk.settings as settings

class ClaimType(str, Enum):
    FACTUAL = "Factual"
    STATISTICAL = "Statistical"
    CAUSAL = "Causal"
    HISTORICAL = "Historical"
    SCIENTIFIC = "Scientific"
    LEGAL = "Legal"
    OPINION = "Opinion"
    LOGICAL = "Logical"
    OTHER = "Other"

class VeracityRating(str, Enum):
    TRUE = "True"
    MOSTLY_TRUE = "Mostly True"
    HALF_TRUE = "Half True"
    MISLEADING = "Misleading"
    FALSE = "False"
    UNSUBSTANTIATED = "Unsubstantiated"

class FallacyType(str, Enum):
    NONE = "None"
    STRAW_MAN = "Straw Man"
    AD_HOMINEM = "Ad Hominem"
    FALSE_DILEMMA = "False Dilemma"
    HASTY_GENERALIZATION = "Hasty Generalization"
    SLIPPERY_SLOPE = "Slippery Slope"
    CIRCULAR_REASONING = "Circular Reasoning"
    APPEAL_TO_EMOTION = "Appeal to Emotion"
    APPEAL_TO_AUTHORITY = "Appeal to Authority"
    RED_HERRING = "Red Herring"
    CHERRY_PICKING = "Cherry Picking"
    POST_HOC = "Post Hoc (False Cause)"
    OTHER = "Other"

class PersonaType(str, Enum):
    SKEPTIC = "skeptic"
    JOURNALIST = "journalist"
    EDUCATOR = "educator"

class ClaimVerification(BaseModel):
    id: int = Field(description="Unique numeric identifier for the claim")
    timestamp_start: Optional[str] = Field(default=None, description="Start timestamp in MM:SS or HH:MM:SS")
    timestamp_end: Optional[str] = Field(default=None, description="End timestamp in MM:SS or HH:MM:SS")
    original_quote: str = Field(description="Direct or transcribed quote from the video")
    claim_text: str = Field(description="Concise factual or logical assertion distilled from the quote")
    claim_type: str = Field(default=ClaimType.FACTUAL.value, description="Category of the claim")
    veracity: str = Field(default=VeracityRating.UNSUBSTANTIATED.value, description="Truthfulness assessment based on evidence")
    confidence_score: float = Field(default=0.8, ge=0.0, le=1.0, description="Confidence in assessment (0.0 to 1.0)")
    is_fallacious: bool = Field(default=False, description="Whether flawed logical reasoning was detected")
    fallacy_type: Optional[str] = Field(default=None, description="Specific logical fallacy name if applicable")
    fallacy_explanation: Optional[str] = Field(default=None, description="Explanation of why this reasoning is flawed")
    evidence_summary: str = Field(description="Objective factual counter-evidence and context")
    sources: List[str] = Field(default_factory=list, description="Authoritative citation URLs or reference sources")
    counter_argument: Optional[str] = Field(default=None, description="Suggested rebuttal point for virtual debunker")

class DebunkReport(BaseModel):
    video_url: Optional[str] = Field(default=None, description="Source YouTube video URL")
    video_title: Optional[str] = Field(default=None, description="Title of the analyzed video if available")
    language: str = Field(default="en", description="Language of analysis ('en' or 'bn')")
    summary: str = Field(description="Executive summary of the video claims, reliability, and reasoning errors")
    overall_veracity_score: float = Field(default=50.0, ge=0.0, le=100.0, description="Overall truthfulness score from 0 (completely false) to 100 (fully truthful)")
    claims: List[ClaimVerification] = Field(default_factory=list, description="List of individual verified claims")
    fallacies_found: List[str] = Field(default_factory=list, description="Unique logical fallacies identified across the video")
    created_at: str = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat(), description="ISO UTC timestamp of report generation")

    @classmethod
    def from_json_string(cls, json_str: str) -> "DebunkReport":
        """
        Parses a DebunkReport from raw LLM output, automatically stripping markdown code blocks.
        """
        cleaned = json_str.strip()
        # Remove markdown code fences if present (e.g. ```json ... ```)
        if "```" in cleaned:
            match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', cleaned)
            if match:
                cleaned = match.group(1).strip()
        
        data = json.loads(cleaned)
        return cls.model_validate(data)

    def to_json(self, indent: int = 2) -> str:
        """
        Serializes the report to a formatted JSON string.
        """
        return self.model_dump_json(indent=indent)

    def to_markdown(self) -> str:
        """
        Renders a comprehensive, publication-ready Markdown Debunk Report.
        """
        lines = []
        title = self.video_title or self.video_url or "Analyzed Video"
        lines.append(f"# AI Debunk Studio Report: {title}")
        lines.append("")
        lines.append(f"- **Generated:** `{self.created_at}`")
        lines.append(f"- **Language:** `{self.language}`")
        lines.append(f"- **Overall Veracity Score:** **{self.overall_veracity_score:.1f}%**")
        
        if self.fallacies_found:
            fallacy_list = ", ".join(f"`{f}`" for f in self.fallacies_found)
            lines.append(f"- **Logical Fallacies Detected:** {fallacy_list}")
        else:
            lines.append("- **Logical Fallacies Detected:** *None detected*")
            
        lines.append("")
        lines.append("## Executive Summary")
        lines.append(self.summary)
        lines.append("")

        if self.claims:
            lines.append("## Claims & Veracity Breakdown")
            lines.append("")
            lines.append("| # | Timestamp | Distilled Claim | Veracity | Fallacy | Confidence |")
            lines.append("|---|---|---|---|---|---|")
            for c in self.claims:
                ts = f"{c.timestamp_start or '00:00'} - {c.timestamp_end or '--:--'}" if (c.timestamp_start or c.timestamp_end) else "N/A"
                fallacy = c.fallacy_type or "None"
                conf = f"{int(c.confidence_score * 100)}%"
                # Sanitize table cell text
                claim_disp = c.claim_text.replace("|", "/")
                lines.append(f"| {c.id} | {ts} | {claim_disp} | **{c.veracity}** | {fallacy} | {conf} |")

            lines.append("")
            lines.append("## Deep-Dive Analysis")
            for c in self.claims:
                lines.append(f"### Claim #{c.id}: \"{c.claim_text}\"")
                if c.timestamp_start or c.timestamp_end:
                    lines.append(f"- **Timestamp:** `{c.timestamp_start or '00:00'}` to `{c.timestamp_end or '--:--'}`")
                lines.append(f"- **Original Quote:** > *\"{c.original_quote}\"*")
                lines.append(f"- **Veracity Rating:** `{c.veracity}` (Confidence: {int(c.confidence_score * 100)}%)")
                lines.append(f"- **Claim Category:** `{c.claim_type}`")
                
                if c.is_fallacious and c.fallacy_type:
                    lines.append(f"- **Logical Fallacy:** `{c.fallacy_type}`")
                    if c.fallacy_explanation:
                        lines.append(f"  - *Reasoning:* {c.fallacy_explanation}")

                lines.append(f"- **Evidence Summary:** {c.evidence_summary}")

                if c.sources:
                    lines.append("- **Sources & Citations:**")
                    for s in c.sources:
                        lines.append(f"  - [{s}]({s})")

                if c.counter_argument:
                    lines.append(f"- **Counter-Argument:** {c.counter_argument}")
                lines.append("")

        return "\n".join(lines)

    def save(self, json_path: Optional[str] = None, md_path: Optional[str] = None):
        """
        Saves report to disk as JSON and Markdown.
        """
        os.makedirs(settings.OUTPUT_DIRECTORY, exist_ok=True)
        j_path = json_path or getattr(settings, 'DEBUNK_REPORT_JSON', os.path.join(settings.OUTPUT_DIRECTORY, 'debunk_report.json'))
        m_path = md_path or getattr(settings, 'DEBUNK_REPORT_MD', os.path.join(settings.OUTPUT_DIRECTORY, 'debunk_report.md'))

        with open(j_path, "w", encoding="utf-8") as f:
            f.write(self.to_json(indent=2))

        with open(m_path, "w", encoding="utf-8") as f:
            f.write(self.to_markdown())

class ScriptSegment(BaseModel):
    segment_id: int = Field(description="Sequential segment index")
    claim_id: Optional[int] = Field(default=None, description="Linked claim ID from DebunkReport")
    timestamp_start: Optional[str] = Field(default=None, description="Original claim start timestamp")
    timestamp_end: Optional[str] = Field(default=None, description="Original claim end timestamp")
    speaker_quote: Optional[str] = Field(default=None, description="Original speaker quote being addressed")
    rebuttal_text: str = Field(description="Spoken narration text for the debunker character")
    visual_cue: Optional[str] = Field(default=None, description="Visual / editorial direction for screen display")
    audio_path: Optional[str] = Field(default=None, description="Path to rendered audio file for this segment")
    duration_seconds: Optional[float] = Field(default=None, description="Synthesized voiceover audio duration in seconds")

class DebunkScript(BaseModel):
    video_url: Optional[str] = Field(default=None, description="Source video URL")
    video_title: Optional[str] = Field(default=None, description="Video title")
    language: str = Field(default="en", description="Language of the script ('en' or 'bn')")
    persona: str = Field(default=PersonaType.SKEPTIC.value, description="Persona name ('skeptic', 'journalist', 'educator')")
    hook: str = Field(description="Attention-grabbing opening hook introducing the debunking")
    segments: List[ScriptSegment] = Field(default_factory=list, description="Claim-by-claim debunker segments")
    outro: str = Field(description="Closing remarks and call to critical inquiry")
    full_narration: Optional[str] = Field(default=None, description="Complete concatenated voiceover script")
    audio_path: Optional[str] = Field(default=None, description="Path to full synthesized voiceover audio")
    total_duration_seconds: Optional[float] = Field(default=None, description="Total duration of voiceover audio in seconds")
    created_at: str = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat(), description="ISO UTC timestamp")

    def get_full_narration(self) -> str:
        """
        Returns full narrative text combining hook, segment rebuttals, and outro.
        """
        if self.full_narration and self.full_narration.strip():
            return self.full_narration.strip()
        parts = [self.hook.strip()]
        for seg in self.segments:
            parts.append(seg.rebuttal_text.strip())
        parts.append(self.outro.strip())
        return "\n\n".join(parts)

    @classmethod
    def from_json_string(cls, json_str: str) -> "DebunkScript":
        """
        Parses DebunkScript from raw LLM output, stripping markdown code fences.
        """
        cleaned = json_str.strip()
        if "```" in cleaned:
            match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', cleaned)
            if match:
                cleaned = match.group(1).strip()
        data = json.loads(cleaned)
        return cls.model_validate(data)

    def to_json(self, indent: int = 2) -> str:
        return self.model_dump_json(indent=indent)

    def to_markdown(self) -> str:
        """
        Renders a structured, publication-ready Markdown script for studio voiceover/teleprompter.
        """
        lines = []
        title = self.video_title or self.video_url or "Analyzed Video"
        persona_name = self.persona.capitalize()
        lines.append(f"# Debunker Studio Script: {title}")
        lines.append("")
        lines.append(f"- **Persona:** `{persona_name}`")
        lines.append(f"- **Language:** `{self.language}`")
        lines.append(f"- **Generated:** `{self.created_at}`")
        if self.total_duration_seconds:
            lines.append(f"- **Total Audio Duration:** `{self.total_duration_seconds:.1f}s`")
        if self.audio_path:
            lines.append(f"- **Voiceover Audio:** `{self.audio_path}`")
        lines.append("")

        lines.append("## 🎙️ Hook (Opening)")
        lines.append(f"> *[Audio Hook]*")
        lines.append(self.hook)
        lines.append("")

        lines.append("## 🎬 Rebuttal Segments")
        for seg in self.segments:
            claim_info = f"Claim #{seg.claim_id}" if seg.claim_id else f"Segment #{seg.segment_id}"
            ts = f" ({seg.timestamp_start or '00:00'} - {seg.timestamp_end or '--:--'})" if (seg.timestamp_start or seg.timestamp_end) else ""
            lines.append(f"### {claim_info}{ts}")
            if seg.speaker_quote:
                lines.append(f"- **Target Quote:** > *\"{seg.speaker_quote}\"*")
            if seg.visual_cue:
                lines.append(f"- **Visual Cue:** `[Cue: {seg.visual_cue}]`")
            if seg.duration_seconds:
                lines.append(f"- **Duration:** `{seg.duration_seconds:.1f}s`")
            lines.append(f"- **Debunker Narration:**")
            lines.append(f"  {seg.rebuttal_text}")
            lines.append("")

        lines.append("## 🏁 Outro (Closing)")
        lines.append(f"> *[Closing Statement]*")
        lines.append(self.outro)
        lines.append("")

        return "\n".join(lines)

    def save(self, json_path: Optional[str] = None, md_path: Optional[str] = None):
        os.makedirs(settings.OUTPUT_DIRECTORY, exist_ok=True)
        j_path = json_path or getattr(settings, 'DEBUNK_SCRIPT_JSON', os.path.join(settings.OUTPUT_DIRECTORY, 'debunk_script.json'))
        m_path = md_path or getattr(settings, 'DEBUNK_SCRIPT_MD', os.path.join(settings.OUTPUT_DIRECTORY, 'debunk_script.md'))

        with open(j_path, "w", encoding="utf-8") as f:
            f.write(self.to_json(indent=2))

        with open(m_path, "w", encoding="utf-8") as f:
            f.write(self.to_markdown())

class TimelineEvent(BaseModel):
    event_id: int = Field(description="Sequential timeline event index")
    claim_id: Optional[int] = Field(default=None, description="Linked claim ID if applicable")
    event_type: str = Field(default="debunk_rebuttal", description="'intro', 'original_claim', 'debunk_rebuttal', 'outro'")
    title: str = Field(description="Event label or scene headline")
    start_seconds: float = Field(description="Start time in combined video timeline")
    end_seconds: float = Field(description="End time in combined video timeline")
    timestamp_start: str = Field(description="Formatted MM:SS start timestamp")
    timestamp_end: str = Field(description="Formatted MM:SS end timestamp")
    duration_seconds: float = Field(description="Event duration in seconds")
    text: str = Field(description="Narration, spoken quote, or visual caption text")
    audio_file: Optional[str] = Field(default=None, description="Audio track path for this event")
    veracity: Optional[str] = Field(default=None, description="Veracity badge e.g. False, Misleading")
    cue: Optional[str] = Field(default=None, description="Compositor visual instruction")

class TimelineSheet(BaseModel):
    video_url: Optional[str] = Field(default=None, description="Source video URL")
    language: str = Field(default="en", description="Timeline language")
    total_duration_seconds: float = Field(default=0.0, description="Total synthesized debunk video timeline duration")
    events: List[TimelineEvent] = Field(default_factory=list, description="Ordered sequence of synchronized events")
    created_at: str = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())

    @classmethod
    def from_json_string(cls, json_str: str) -> "TimelineSheet":
        cleaned = json_str.strip()
        if "```" in cleaned:
            match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', cleaned)
            if match:
                cleaned = match.group(1).strip()
        data = json.loads(cleaned)
        return cls.model_validate(data)

    def to_json(self, indent: int = 2) -> str:
        return self.model_dump_json(indent=indent)

    def to_markdown(self) -> str:
        lines = []
        lines.append("# AI Debunker Studio: Synchronized Timeline Sheet")
        lines.append("")
        lines.append(f"- **Language:** `{self.language}`")
        lines.append(f"- **Total Duration:** `{self.total_duration_seconds:.1f}s`")
        lines.append(f"- **Total Events:** `{len(self.events)}`")
        lines.append("")
        lines.append("| # | Time Window | Type | Title | Veracity | Duration | Cue |")
        lines.append("|---|---|---|---|---|---|---|")
        for ev in self.events:
            ts = f"{ev.timestamp_start} - {ev.timestamp_end}"
            veracity = ev.veracity or "-"
            cue = (ev.cue or "-").replace("|", "/")
            lines.append(f"| {ev.event_id} | {ts} | `{ev.event_type}` | {ev.title} | {veracity} | {ev.duration_seconds:.1f}s | {cue} |")

        lines.append("")
        lines.append("## Detailed Event Breakdown")
        for ev in self.events:
            lines.append(f"### Event {ev.event_id}: {ev.title} ({ev.timestamp_start} - {ev.timestamp_end})")
            lines.append(f"- **Type:** `{ev.event_type}`")
            lines.append(f"- **Duration:** `{ev.duration_seconds:.1f} seconds`")
            if ev.veracity:
                lines.append(f"- **Veracity Badge:** `{ev.veracity}`")
            if ev.cue:
                lines.append(f"- **Compositor Cue:** `{ev.cue}`")
            if ev.audio_file:
                lines.append(f"- **Audio File:** `{ev.audio_file}`")
            lines.append(f"- **Content:** > *\"{ev.text}\"*")
            lines.append("")

        return "\n".join(lines)

    def save(self, json_path: Optional[str] = None, md_path: Optional[str] = None):
        os.makedirs(settings.OUTPUT_DIRECTORY, exist_ok=True)
        j_path = json_path or getattr(settings, 'TIMELINE_JSON', os.path.join(settings.OUTPUT_DIRECTORY, 'timeline.json'))
        m_path = md_path or getattr(settings, 'TIMELINE_MD', os.path.join(settings.OUTPUT_DIRECTORY, 'timeline.md'))

        with open(j_path, "w", encoding="utf-8") as f:
            f.write(self.to_json(indent=2))

        with open(m_path, "w", encoding="utf-8") as f:
            f.write(self.to_markdown())
