"""
The Model Verse — Configuration & Design Tokens
"""

import os
import shutil
import datetime
from typing import Optional, Dict, Any, List
from pathlib import Path
from dotenv import load_dotenv

# Safeguard: Manim CE Camera.display_image_mobject passes a 2D float array with mode="RGBA"
# to Image.fromarray(), which raises ValueError in Pillow >= 13.0.0.
try:
    from PIL import Image as _PILImage
    _orig_fromarray = _PILImage.fromarray

    def _patched_fromarray(obj, mode=None):
        if mode == "RGBA" and hasattr(obj, "shape") and len(obj.shape) == 2:
            return _PILImage.new("RGBA", (obj.shape[1], obj.shape[0]), (0, 0, 0, 0))
        return _orig_fromarray(obj, mode=mode)

    _PILImage.fromarray = _patched_fromarray
except Exception:
    pass

# Paths (Dynamic for local macOS and cloud Linux)
WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(WORKSPACE_ROOT / ".env")

FFMPEG_BIN = os.environ.get("FFMPEG_BIN") or shutil.which("ffmpeg") or "/Users/amankumar/bin/ffmpeg"
PUBLIC_DIR = str(WORKSPACE_ROOT / "public")
OUTPUT_DIR = str(WORKSPACE_ROOT / "output")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_MODEL_NAME = os.environ.get("GEMINI_MODEL_NAME", "gemini-flash-latest")
GEMINI_TTS_MODEL = os.environ.get("GEMINI_TTS_MODEL", "gemini-3.8-flash-tts")
GEMINI_TTS_VOICE = os.environ.get("GEMINI_TTS_VOICE", "Charon")
GEMINI_TTS_STYLE = os.environ.get(
    "GEMINI_TTS_STYLE",
    "clear, confident, conversational science explainer; energetic but not theatrical; moderate pace",
)
GEMINI_TTS_TIMEOUT_SECONDS = float(os.environ.get("GEMINI_TTS_TIMEOUT_SECONDS", "90"))

# Typography & Visual Design Tokens
FONT_HELVETICA = "Helvetica Neue"
BG_CARBON = "#0A0D14"
COLOR_MINT = "#10B981"
COLOR_MINT_LIGHT = "#A7F3D0"
COLOR_CYAN = "#00F0FF"
COLOR_GOLD = "#F59E0B"
COLOR_GOLD_LIGHT = "#FDE68A"
COLOR_DANGER = "#FF3366"
COLOR_DANGER_LIGHT = "#FECDD3"
COLOR_SLATE = "#CBD5E1"
COLOR_DARK_SLATE = "#475569"
COLOR_CARD_BG = "#111827"
COLOR_CARD_BORDER = "#1F2937"

# Video Configuration
VIDEO_WIDTH = 1080
VIDEO_HEIGHT = 1920
VIDEO_FPS = 60
FRAME_WIDTH = 9.0
FRAME_HEIGHT = 16.0

# Broadcast Mastering Configuration (1440p 2K QHD @ 60fps for YouTube VP09/AV01 tier)
BROADCAST_WIDTH = 1440
BROADCAST_HEIGHT = 2560
BROADCAST_FPS = 60
BROADCAST_CRF = 15
BROADCAST_MAXRATE = "25M"
BROADCAST_BUFSIZE = "50M"

# Safe-Zones (X in [-3.3, 3.3], Y in [-5.8, 5.8])
SAFE_X_MIN = -3.3
SAFE_X_MAX = 3.3
SAFE_Y_MIN = -5.8
SAFE_Y_MAX = 5.8

# Audio Configuration
SAMPLE_RATE = 24000
DEFAULT_VOICE = os.environ.get("ELEVENLABS_VOICE") or "eric"
DEFAULT_SPEED = 1.12
DEFAULT_TTS_PROVIDER = os.environ.get("TTS_PROVIDER", "auto")
TTS_CACHE_DIR = os.path.join(PUBLIC_DIR, "audio_cache")

# ElevenLabs Configuration (English Neural Voice)
ELEVENLABS_API_KEY = os.environ.get("ELEVENLABS_API_KEY", "")
ELEVENLABS_VOICE_ID = os.environ.get("ELEVENLABS_VOICE_ID", "cjVigY5qzO86Huf0OWal")  # Eric
ELEVENLABS_MODEL_ID = os.environ.get("ELEVENLABS_MODEL_ID", "eleven_multilingual_v2")
ELEVENLABS_VOICES = {
    "eric": "cjVigY5qzO86Huf0OWal",
    "adam": "pNInz6obpgDQGcFmaJgB",
    "alice": "Xb7hH8MSUJpSbSDYk0k2",
    "brian": "nPczCjzI2devNBz1zQrb",
    "daniel": "onwK4e9ZLuTAKqWW03F9",
    "charlie": "IKne3meq5aSn9XLyUdCD",
    "roger": "CwhRBWXzGAHq8TQ4Fs17",
    "sarah": "EXAVITQu4vr4xnSDxMaL",
    "liam": "TX3LPaxmHKxFdv7VOQHJ",
    "george": "JBFqnCBsd6RMkjVDRZzb",
    "laura": "FGY2WhTYpPnrIDTdsKH5",
    "will": "bIHbv24MWmeRgasZH58o",
    "jessica": "cgSgspJ2msm6clMCkdW9",
    "bella": "hpp4J3VqNfWAUOO0d1Us",
    "chris": "iP95p4xoKVk53GoZ742B",
    "lily": "pFZP5JQG7iQjIQuC4Bku",
    "bill": "pqHfZKP75CvOlQylNhV4",
}

# Sarvam AI Configuration (Hindi Neural Voice)
SARVAM_API_KEY = os.environ.get("SARVAM_API_KEY", "")
SARVAM_SPEAKER = os.environ.get("SARVAM_SPEAKER", "shubh")
SARVAM_MODEL = os.environ.get("SARVAM_MODEL", "bulbul:v3")
SARVAM_SPEAKERS = [
    "shubh", "aditya", "ritu", "priya", "neha", "rahul", "pooja",
    "rohan", "simran", "kavya", "amit", "dev", "ishita", "shreya",
    "ratan", "varun", "manan", "sumit", "roopa", "kabir", "aayan",
    "ashutosh", "advait", "meera"
]

# YouTube Publisher Configuration
YOUTUBE_CLIENT_SECRETS_PATH = os.environ.get(
    "YOUTUBE_CLIENT_SECRETS_PATH",
    str(WORKSPACE_ROOT / "pipeline" / "client_secrets.json")
)
YOUTUBE_TOKEN_PATH = os.environ.get(
    "YOUTUBE_TOKEN_PATH",
    str(WORKSPACE_ROOT / "pipeline" / "youtube_token.json")
)
YOUTUBE_DEFAULT_CATEGORY = "28"  # Science & Technology

# Instagram Meta Graph API Configuration
INSTAGRAM_ACCOUNT_ID = os.environ.get("INSTAGRAM_ACCOUNT_ID", "17841425926885618")
INSTAGRAM_ACCESS_TOKEN = os.environ.get("INSTAGRAM_ACCESS_TOKEN", "")
INSTAGRAM_API_VERSION = os.environ.get("INSTAGRAM_API_VERSION", "v21.0")
INSTAGRAM_GRAPH_URL = f"https://graph.facebook.com/{INSTAGRAM_API_VERSION}"
INSTAGRAM_RUPLOAD_URL = f"https://rupload.facebook.com/ig-video-upload/{INSTAGRAM_API_VERSION}"

# Twitter / X API Configuration (OAuth 1.0a User Context & API v2)
TWITTER_API_KEY = os.environ.get("TWITTER_API_KEY", "")
TWITTER_API_SECRET = os.environ.get("TWITTER_API_SECRET", "")
TWITTER_ACCESS_TOKEN = os.environ.get("TWITTER_ACCESS_TOKEN", "")
TWITTER_ACCESS_TOKEN_SECRET = os.environ.get("TWITTER_ACCESS_TOKEN_SECRET", "")
TWITTER_CLIENT_ID = os.environ.get("TWITTER_CLIENT_ID", "")
TWITTER_CLIENT_SECRET = os.environ.get("TWITTER_CLIENT_SECRET", "")
TWITTER_API_BASE_URL = "https://api.twitter.com"
TWITTER_UPLOAD_BASE_URL = "https://upload.twitter.com/1.1/media/upload.json"

# LinkedIn REST API Configuration (OAuth 2.0 & Posts API)
LINKEDIN_CLIENT_ID = os.environ.get("LINKEDIN_CLIENT_ID", "")
LINKEDIN_CLIENT_SECRET = os.environ.get("LINKEDIN_CLIENT_SECRET", "")
LINKEDIN_ACCESS_TOKEN = os.environ.get("LINKEDIN_ACCESS_TOKEN", "")
LINKEDIN_REDIRECT_URI = os.environ.get("LINKEDIN_REDIRECT_URI", "http://localhost:8080/callback")
LINKEDIN_TOKEN_PATH = os.environ.get(
    "LINKEDIN_TOKEN_PATH",
    str(WORKSPACE_ROOT / "pipeline" / "linkedin_token.json")
)
LINKEDIN_API_VERSION = os.environ.get("LINKEDIN_API_VERSION", "202601")
LINKEDIN_API_BASE_URL = "https://api.linkedin.com"

# Background Music & Dynamic Ducking
ENABLE_BG_MUSIC = True
DEFAULT_DUCK_GAIN = 0.10    # -20 dB during speech
DEFAULT_NORMAL_GAIN = 0.32  # -10 dB during pauses & outro
CUSTOM_BG_MUSIC_PATH = str(WORKSPACE_ROOT / "public" / "audio" / "bg_music.wav")

# Content Recency & Maximum Age Constraints (1 to 2 months max)
# Strict default: 45 days. Hard ceiling: 60 days.
MAX_CONTENT_AGE_DAYS: int = int(os.environ.get("MAX_CONTENT_AGE_DAYS", "45"))
MAX_PERK_VERIFICATION_AGE_DAYS: int = int(os.environ.get("MAX_PERK_VERIFICATION_AGE_DAYS", "60"))
STRICT_RECENCY_ENFORCEMENT: bool = os.environ.get("STRICT_RECENCY_ENFORCEMENT", "true").lower() in ("true", "1", "yes")
# Production topic policy. `latest_or_viral` refuses candidates without current evidence.
TOPIC_SELECTION_MODE: str = os.environ.get("TOPIC_SELECTION_MODE", "latest_or_viral").lower()


def parse_content_date(date_str_or_id: Optional[str]) -> Optional[datetime.date]:
    """
    Parses an ISO date string, human date string, RFC date string, or arXiv ID
    into a clean standard datetime.date object.
    """
    import re
    import datetime
    import email.utils

    if not date_str_or_id:
        return None

    raw = str(date_str_or_id).strip()

    # 1. Try ISO string (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)
    iso_match = re.match(r"^(\d{4})-(\d{2})-(\d{2})", raw)
    if iso_match:
        try:
            return datetime.date(int(iso_match.group(1)), int(iso_match.group(2)), int(iso_match.group(3)))
        except ValueError:
            pass

    # 2. Try RFC 2822 (e.g., 'Fri, 31 Jan 2025 18:00:00 GMT')
    try:
        dt_tuple = email.utils.parsedate_to_datetime(raw)
        if dt_tuple:
            return dt_tuple.date()
    except Exception:
        pass

    # 3. Try standard human-readable formats
    for fmt in (
        "%b %d, %Y", "%B %d, %Y",
        "%d %b %Y", "%d %B %Y",
        "%Y/%m/%d", "%m/%d/%Y"
    ):
        try:
            return datetime.datetime.strptime(raw, fmt).date()
        except Exception:
            pass

    # 4. Check if raw string is or contains an arXiv ID (YYMM.NNNNN)
    arxiv_match = re.search(r"\b(\d{2})(\d{2})\.\d{4,5}(?:v\d+)?\b", raw)
    if arxiv_match:
        yy = int(arxiv_match.group(1))
        mm = int(arxiv_match.group(2))
        year = (2000 + yy) if yy < 70 else (1900 + yy)
        if 1 <= mm <= 12:
            return datetime.date(year, mm, 1)

    return None


def calculate_content_age_days(
    date_str_or_id: Optional[str],
    reference_date: Optional[datetime.date] = None
) -> Optional[int]:
    """
    Computes age in elapsed days relative to reference_date (defaults to current date in UTC).
    Returns None if date could not be extracted.
    """
    import datetime

    target_date = parse_content_date(date_str_or_id)
    if not target_date:
        return None

    ref = reference_date or datetime.datetime.now(datetime.timezone.utc).date()
    return max(0, (ref - target_date).days)


def is_content_recent(
    date_str_or_id: Optional[str],
    max_age_days: int = MAX_CONTENT_AGE_DAYS,
    reference_date: Optional[datetime.date] = None
) -> bool:
    """
    Validates whether content is recent and eligible for publication.
    Enforces that content older than max_age_days (default: 45 days, max: 60 days) is rejected.
    """
    age = calculate_content_age_days(date_str_or_id, reference_date=reference_date)
    if age is None:
        # If date is completely unparseable and strict enforcement is active, reject
        return not STRICT_RECENCY_ENFORCEMENT
    return age <= max_age_days


# -----------------------------------------------------------------------------
# Canonical 3-Track Production Architecture
# -----------------------------------------------------------------------------
TRACK_ACADEMIC = "academic_breakdown"
TRACK_TECH_NEWS = "tech_news"
TRACK_DEVELOPER_PERKS = "developer_perks"

CANONICAL_TRACKS = [TRACK_ACADEMIC, TRACK_TECH_NEWS, TRACK_DEVELOPER_PERKS]

TRACK_ALIASES = {
    # Track 1 aliases
    "academic": TRACK_ACADEMIC,
    "academic_breakdown": TRACK_ACADEMIC,
    "architecture_breakdown": TRACK_ACADEMIC,
    "mechanism_deepdive": TRACK_ACADEMIC,
    "benchmark_news": TRACK_ACADEMIC,
    "model_showdown": TRACK_ACADEMIC,
    "arxiv": TRACK_ACADEMIC,
    "paper": TRACK_ACADEMIC,
    "papers": TRACK_ACADEMIC,

    # Track 2 aliases
    "news": TRACK_TECH_NEWS,
    "tech_news": TRACK_TECH_NEWS,
    "blogs": TRACK_TECH_NEWS,
    "official_blogs": TRACK_TECH_NEWS,

    # Track 3 aliases
    "perks": TRACK_DEVELOPER_PERKS,
    "developer_perks": TRACK_DEVELOPER_PERKS,
    "startup_credits": TRACK_DEVELOPER_PERKS,
    "credits": TRACK_DEVELOPER_PERKS,
}

TRACK_METADATA = {
    TRACK_ACADEMIC: {
        "display_name": "Academic Breakdown",
        "badge": "PAPER BREAKDOWN",
        "scene_file": "manim_engine/scenes/script_driven_scene.py",
        "scene_class": "ScriptDrivenScene",
        "description_prefix": "Frontier AI Research & Architectural Deep Dive",
        "default_tags": ["AIResearch", "PaperBreakdown", "DeepLearning", "ComputerScience", "MachineLearning", "arXiv", "Shorts"],
        "pinned_comment": "💡 What AI paper or architectural breakthrough should we break down next? Let us know below! 👇"
    },
    TRACK_TECH_NEWS: {
        "display_name": "Official Tech News",
        "badge": "TECH NEWS DISPATCH",
        "scene_file": "manim_engine/scenes/tech_news_scene.py",
        "scene_class": "TechNewsScene",
        "description_prefix": "Official AI Tech News & Breakthrough Launch Dispatch",
        "default_tags": ["AITechNews", "TechNews", "ArtificialIntelligence", "FoundationModels", "OpenAI", "Anthropic", "GoogleDeepMind", "Shorts"],
        "pinned_comment": "🔥 Are you testing this new release in your workflow? Drop your benchmarks and thoughts below! 👇"
    },
    TRACK_DEVELOPER_PERKS: {
        "display_name": "Developer Perks & Credits",
        "badge": "DEVELOPER PERKS",
        "scene_file": "manim_engine/scenes/developer_perks_scene.py",
        "scene_class": "DeveloperPerksScene",
        "description_prefix": "Actionable Developer Grants, Free API Credits & Startup Tiers",
        "default_tags": ["DeveloperPerks", "StartupCredits", "FreeAIAPI", "StartupGrant", "SoftwareEngineering", "CodingTools", "Shorts"],
        "pinned_comment": "🎁 Did you claim this grant? Which AI tool or cloud perk should we audit next? Let us know below! 👇"
    }
}

def resolve_track(category_or_pillar: Optional[str]) -> str:
    """Normalizes any category, alias, or source string into one of the 3 canonical tracks."""
    if not category_or_pillar:
        return TRACK_ACADEMIC
    clean = str(category_or_pillar).strip().lower()
    return TRACK_ALIASES.get(clean, TRACK_ACADEMIC)
