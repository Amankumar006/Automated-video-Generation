"""
The Model Verse — Configuration & Design Tokens
"""

import os
import shutil
from pathlib import Path
from dotenv import load_dotenv

# Paths (Dynamic for local macOS and cloud Linux)
WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(WORKSPACE_ROOT / ".env")

FFMPEG_BIN = os.environ.get("FFMPEG_BIN") or shutil.which("ffmpeg") or "/Users/amankumar/bin/ffmpeg"
KOKORO_MODEL_PATH = str(WORKSPACE_ROOT / "kokoro_models" / "kokoro-v1.0.onnx")
KOKORO_VOICES_PATH = str(WORKSPACE_ROOT / "kokoro_models" / "voices-v1.0.bin")
PUBLIC_DIR = str(WORKSPACE_ROOT / "public")
OUTPUT_DIR = str(WORKSPACE_ROOT / "output")

# Typography & Visual Design Tokens
FONT_HELVETICA = "Helvetica"
BG_CARBON = "#0A0D14"
COLOR_MINT = "#10B981"
COLOR_MINT_LIGHT = "#A7F3D0"
COLOR_CYAN = "#00F0FF"
COLOR_GOLD = "#F59E0B"
COLOR_GOLD_LIGHT = "#FDE68A"
COLOR_DANGER = "#FF3366"
COLOR_DANGER_LIGHT = "#FECDD3"
COLOR_SLATE = "#94A3B8"
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
DEFAULT_VOICE = os.environ.get("KOKORO_VOICE", "am_eric")
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

# Background Music & Dynamic Ducking
ENABLE_BG_MUSIC = True
DEFAULT_DUCK_GAIN = 0.10    # -20 dB during speech
DEFAULT_NORMAL_GAIN = 0.32  # -10 dB during pauses & outro
CUSTOM_BG_MUSIC_PATH = str(WORKSPACE_ROOT / "public" / "audio" / "bg_music.wav")
