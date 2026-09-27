"""
The Model Verse — Studio Server (FastAPI)
Interactive Local Web Studio for AI Short Video Generation.
Provides REST APIs, SSE job streaming, media serving, and UI endpoints.
"""

import os
import sys
import json
import time
import glob
import asyncio
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional

from fastapi import FastAPI, BackgroundTasks, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, FileResponse, StreamingResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from pipeline.config import (
    WORKSPACE_ROOT, FFMPEG_BIN, KOKORO_MODEL_PATH, KOKORO_VOICES_PATH,
    PUBLIC_DIR, DEFAULT_VOICE, DEFAULT_SPEED,
    ENABLE_BG_MUSIC, DEFAULT_DUCK_GAIN, DEFAULT_NORMAL_GAIN
)
from pipeline.run_pipeline import CATEGORY_SCENE_MAP
from pipeline.batch_digest import get_trending_digest
from scripts.synth_music_generator import (
    generate_lofi_ambient_soundtrack, mix_master_audio
)

app = FastAPI(
    title="The Model Verse Web Studio",
    description="Interactive Local Production Studio for 3Blue1Brown Mathematical AI Shorts",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static and public assets
STATIC_DIR = Path(__file__).resolve().parent / "static"
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
app.mount("/public", StaticFiles(directory=str(PUBLIC_DIR)), name="public")

# In-memory Job Registry
jobs_db: Dict[str, Dict[str, Any]] = {}
job_subscribers: Dict[str, List[asyncio.Queue]] = {}

class ProductionRequest(BaseModel):
    topic: Optional[str] = None
    arxiv: Optional[str] = None
    category: Optional[str] = "mechanism_deepdive"
    voice: Optional[str] = DEFAULT_VOICE
    speed: Optional[float] = DEFAULT_SPEED
    quality: Optional[str] = "-qm"
    skip_script: Optional[bool] = False
    publish: Optional[bool] = False
    privacy: Optional[str] = "unlisted"
    dry_run_publish: Optional[bool] = False
    enable_music: Optional[bool] = True
    duck_gain: Optional[float] = DEFAULT_DUCK_GAIN
    normal_gain: Optional[float] = DEFAULT_NORMAL_GAIN

class SynthPreviewRequest(BaseModel):
    duration: float = 6.0
    duck_gain: float = DEFAULT_DUCK_GAIN
    normal_gain: float = DEFAULT_NORMAL_GAIN
    simulate_ducking: bool = True

class ScriptGenerateRequest(BaseModel):
    topic: str
    category: Optional[str] = "mechanism_deepdive"
    arxiv: Optional[str] = None

# -------------------------------------------------------------
# Background Job Execution & Output Streaming
# -------------------------------------------------------------

def push_log_line(job_id: str, line: str):
    if job_id not in jobs_db:
        return
    clean_line = line.strip("\r\n")
    if not clean_line:
        return
    jobs_db[job_id]["logs"].append(clean_line)
    
    # Broadcast to all active SSE queues
    queues = job_subscribers.get(job_id, [])
    for q in list(queues):
        try:
            q.put_nowait(clean_line)
        except Exception:
            pass

def run_production_job(job_id: str, req: ProductionRequest):
    jobs_db[job_id]["status"] = "running"
    jobs_db[job_id]["start_time"] = time.time()
    push_log_line(job_id, f"🚀 Initializing production job [{job_id}] for topic: {req.topic or req.arxiv}...")

    cmd = [
        sys.executable,
        str(PROJECT_ROOT / "pipeline" / "auto_produce.py"),
        "--category", req.category or "mechanism_deepdive",
        "--voice", req.voice or DEFAULT_VOICE,
        f"--quality={req.quality or '-qm'}",
        "--privacy", req.privacy or "unlisted"
    ]

    if req.topic:
        cmd.extend(["--topic", req.topic])
    if req.arxiv:
        cmd.extend(["--arxiv", req.arxiv])
    if req.skip_script:
        cmd.append("--skip-script")
    if req.publish:
        cmd.append("--publish")
    if req.dry_run_publish:
        cmd.append("--dry-run-publish")
    if not req.enable_music:
        cmd.append("--no-music")

    push_log_line(job_id, f"⚙️ Executing command: {' '.join(cmd)}")

    try:
        proc = subprocess.Popen(
            cmd,
            cwd=str(PROJECT_ROOT),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )

        for line in iter(proc.stdout.readline, ""):
            push_log_line(job_id, line)

        proc.stdout.close()
        return_code = proc.wait()

        if return_code == 0:
            jobs_db[job_id]["status"] = "completed"
            push_log_line(job_id, "🎉 Job completed successfully!")
            
            # Find output video
            candidates = list(PROJECT_ROOT.glob("final_*.mp4"))
            if candidates:
                candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
                jobs_db[job_id]["output_video"] = candidates[0].name
        else:
            jobs_db[job_id]["status"] = "failed"
            push_log_line(job_id, f"❌ Job failed with exit code: {return_code}")

    except Exception as e:
        jobs_db[job_id]["status"] = "failed"
        jobs_db[job_id]["error"] = str(e)
        push_log_line(job_id, f"❌ Exception during execution: {e}")
    finally:
        jobs_db[job_id]["end_time"] = time.time()
        push_log_line(job_id, "__STREAM_END__")

# -------------------------------------------------------------
# REST API Endpoints
# -------------------------------------------------------------

@app.get("/", response_class=HTMLResponse)
async def serve_index():
    index_file = STATIC_DIR / "index.html"
    if not index_file.exists():
        raise HTTPException(status_code=404, detail="Studio frontend not found.")
    return HTMLResponse(content=index_file.read_text(encoding="utf-8"))

@app.get("/api/status")
def get_system_status():
    kokoro_ready = os.path.exists(KOKORO_MODEL_PATH) and os.path.exists(KOKORO_VOICES_PATH)
    ffmpeg_ready = os.path.exists(FFMPEG_BIN)
    templates = list((PROJECT_ROOT / "pipeline" / "templates").glob("*.json"))
    videos = list(PROJECT_ROOT.glob("final_*.mp4"))

    return {
        "status": "online",
        "kokoro_ready": kokoro_ready,
        "ffmpeg_ready": ffmpeg_ready,
        "ffmpeg_path": FFMPEG_BIN,
        "template_count": len(templates),
        "video_count": len(videos),
        "categories": list(CATEGORY_SCENE_MAP.keys()),
        "default_voice": DEFAULT_VOICE,
        "default_speed": DEFAULT_SPEED,
        "music_enabled": ENABLE_BG_MUSIC
    }

@app.get("/api/templates")
def list_templates():
    templates_dir = PROJECT_ROOT / "pipeline" / "templates"
    results = []
    for p in sorted(templates_dir.glob("*.json")):
        try:
            with open(p, "r", encoding="utf-8") as f:
                data = json.load(f)
                beats = data.get("beats", [])
                est_dur = sum(b.get("slot_duration", b.get("duration", 5.0)) for b in beats)
                results.append({
                    "filename": p.name,
                    "id": data.get("id", p.stem),
                    "title": data.get("title", "Untitled Short"),
                    "category": data.get("category", "mechanism_deepdive"),
                    "beat_count": len(beats),
                    "estimated_duration": round(est_dur, 2)
                })
        except Exception as e:
            results.append({"filename": p.name, "error": str(e)})
    return results

@app.get("/api/templates/{filename}")
def get_template(filename: str):
    template_path = PROJECT_ROOT / "pipeline" / "templates" / filename
    if not template_path.exists():
        raise HTTPException(status_code=404, detail="Template not found")
    with open(template_path, "r", encoding="utf-8") as f:
        return json.load(f)

@app.post("/api/templates/{filename}")
async def save_template(filename: str, request: Request):
    template_path = PROJECT_ROOT / "pipeline" / "templates" / filename
    payload = await request.json()
    with open(template_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    return {"status": "saved", "filename": filename}

@app.get("/api/digest")
def get_digest_endpoint(limit: int = 15):
    try:
        papers = get_trending_digest(limit=limit)
        return papers
    except Exception as e:
        return {"error": str(e), "papers": []}

@app.get("/api/videos")
def list_produced_videos():
    videos = []
    for p in sorted(PROJECT_ROOT.glob("final_*.mp4"), key=lambda f: f.stat().st_mtime, reverse=True):
        stem = p.stem.replace("final_", "")
        
        # Look for matching frames directory
        frames = []
        possible_dirs = [
            PROJECT_ROOT / f"frames_{stem}",
            PROJECT_ROOT / f"frames_{stem.split('_')[0]}",
        ]
        # Also check with id fragments
        for cand in PROJECT_ROOT.glob("frames_*"):
            if any(part in cand.name for part in stem.split("_") if len(part) >= 4):
                possible_dirs.append(cand)

        for d in possible_dirs:
            if d.exists() and d.is_dir():
                frames = [f"/api/frames/{d.name}/{img.name}" for img in sorted(d.glob("*.png"))]
                break

        # Look for matching audio in public/
        audio_files = {}
        for aud in (PROJECT_ROOT / "public").glob(f"*{stem.split('_')[0]}*.wav"):
            if "narration" in aud.name:
                audio_files["narration"] = f"/public/{aud.name}"
            elif "soundtrack" in aud.name:
                audio_files["soundtrack"] = f"/public/{aud.name}"
            elif "master" in aud.name:
                audio_files["master"] = f"/public/{aud.name}"

        # Look for matching poster in public/thumbnails/
        poster_url = None
        for post in sorted((PROJECT_ROOT / "public" / "thumbnails").glob("*.png")):
            if any(part in post.name for part in stem.split("_") if len(part) >= 4):
                poster_url = f"/public/thumbnails/{post.name}"
                break

        videos.append({
            "filename": p.name,
            "title": stem.replace("_", " ").title(),
            "url": f"/api/videos/{p.name}",
            "poster_url": poster_url,
            "size_mb": round(p.stat().st_size / (1024 * 1024), 2),
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(p.stat().st_mtime)),
            "keyframes": frames,
            "audio": audio_files
        })
    return videos

@app.get("/api/thumbnails")
def list_thumbnails():
    posters = []
    for p in sorted((PROJECT_ROOT / "public" / "thumbnails").glob("*.png"), key=lambda f: f.stat().st_mtime, reverse=True):
        posters.append({
            "filename": p.name,
            "url": f"/public/thumbnails/{p.name}",
            "size_kb": round(p.stat().st_size / 1024, 1),
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(p.stat().st_mtime))
        })
    return posters

class ThumbnailGenerateRequest(BaseModel):
    topic: Optional[str] = None
    spec_id: Optional[str] = None
    badge: Optional[str] = None
    keyframe: Optional[str] = None

@app.post("/api/thumbnails/generate")
def generate_thumbnail_api(req: ThumbnailGenerateRequest):
    from pipeline.thumbnail_generator import thumbnail_generator
    from scripts.generate_thumbnail import find_best_keyframe

    spec = None
    templates_dir = PROJECT_ROOT / "pipeline" / "templates"
    query = (req.spec_id or req.topic or "").lower()
    for p in templates_dir.glob("*.json"):
        if query and (query in p.stem.lower() or any(w in p.stem.lower() for w in query.split() if len(w) >= 4)):
            with open(p, "r", encoding="utf-8") as f:
                spec = json.load(f)
            break

    if not spec:
        spec = {
            "id": req.spec_id or "custom_short",
            "title": req.topic or "Autonomous AI Short",
            "category": "mechanism_deepdive"
        }

    base_kf = req.keyframe or find_best_keyframe(spec.get("id", ""))
    poster_path = thumbnail_generator.generate(
        spec=spec,
        base_keyframe_path=base_kf,
        custom_badge=req.badge
    )
    return {
        "status": "ready",
        "poster_url": f"/public/thumbnails/{Path(poster_path).name}"
    }

@app.get("/api/videos/{filename}")
def serve_video(filename: str):
    video_path = PROJECT_ROOT / filename
    if not video_path.exists():
        raise HTTPException(status_code=404, detail="Video file not found")
    return FileResponse(str(video_path), media_type="video/mp4", filename=filename)

@app.get("/api/frames/{dir_name}/{filename}")
def serve_frame(dir_name: str, filename: str):
    frame_path = PROJECT_ROOT / dir_name / filename
    if not frame_path.exists():
        raise HTTPException(status_code=404, detail="Frame not found")
    return FileResponse(str(frame_path), media_type="image/png")

@app.post("/api/audio/preview-synth")
def preview_synth(req: SynthPreviewRequest):
    """Generates an instant procedural synth snippet with optional simulated ducking."""
    import soundfile as sf
    import numpy as np

    sr = 24000
    duration = max(3.0, min(req.duration, 15.0))
    soundtrack = generate_lofi_ambient_soundtrack(duration, sr=sr)

    preview_name = f"preview_synth_{int(time.time())}.wav"
    preview_path = PROJECT_ROOT / "public" / "audio" / preview_name
    preview_path.parent.mkdir(parents=True, exist_ok=True)

    if req.simulate_ducking:
        # Create a mock speech pulse in the middle (e.g. 1.5s -> 4.0s)
        mock_speech = np.zeros_like(soundtrack)
        speech_start = int(1.2 * sr)
        speech_end = min(int(3.8 * sr), len(soundtrack))
        t = np.linspace(0, (speech_end - speech_start) / sr, speech_end - speech_start)
        mock_speech[speech_start:speech_end] = 0.6 * np.sin(2 * np.pi * 220 * t)

        mixed = mix_master_audio(
            narration=mock_speech,
            soundtrack=soundtrack,
            sfx=np.zeros_like(soundtrack),
            sr=sr,
            duck_gain=req.duck_gain,
            normal_gain=req.normal_gain
        )
        sf.write(str(preview_path), mixed.astype(np.float32), sr)
    else:
        sf.write(str(preview_path), soundtrack.astype(np.float32), sr)

    return {
        "status": "ready",
        "audio_url": f"/public/audio/{preview_name}",
        "duration": duration
    }

@app.post("/api/script/generate")
def generate_script_endpoint(req: ScriptGenerateRequest):
    from pipeline.script_generator import generate_script
    from pipeline.arxiv_fetcher import fetch_arxiv_paper

    arxiv_meta = None
    if req.arxiv:
        arxiv_meta = fetch_arxiv_paper(req.arxiv)

    spec = generate_script(
        topic=req.topic,
        category=req.category,
        arxiv_meta=arxiv_meta
    )
    return spec

@app.post("/api/produce")
def trigger_produce(req: ProductionRequest, background_tasks: BackgroundTasks):
    job_id = f"job_{int(time.time())}_{os.urandom(2).hex()}"
    jobs_db[job_id] = {
        "id": job_id,
        "status": "pending",
        "topic": req.topic or req.arxiv,
        "category": req.category,
        "voice": req.voice,
        "speed": req.speed,
        "quality": req.quality,
        "enable_music": req.enable_music,
        "logs": [],
        "output_video": None,
        "error": None,
        "created_at": time.time()
    }
    job_subscribers[job_id] = []

    background_tasks.add_task(run_production_job, job_id, req)
    return {"job_id": job_id, "status": "queued"}

@app.get("/api/jobs")
def list_jobs():
    return sorted(list(jobs_db.values()), key=lambda j: j.get("created_at", 0), reverse=True)

@app.get("/api/jobs/{job_id}")
def get_job(job_id: str):
    if job_id not in jobs_db:
        raise HTTPException(status_code=404, detail="Job not found")
    return jobs_db[job_id]

@app.get("/api/jobs/{job_id}/stream")
async def stream_job_logs(job_id: str):
    if job_id not in jobs_db:
        raise HTTPException(status_code=404, detail="Job not found")

    q = asyncio.Queue()
    if job_id not in job_subscribers:
        job_subscribers[job_id] = []
    job_subscribers[job_id].append(q)

    # Replay existing historical logs
    for line in jobs_db[job_id]["logs"]:
        q.put_nowait(line)

    async def event_generator():
        try:
            while True:
                line = await q.get()
                if line == "__STREAM_END__":
                    yield f"event: end\ndata: {json.dumps({'status': jobs_db[job_id]['status']})}\n\n"
                    break
                yield f"data: {json.dumps({'line': line})}\n\n"
        finally:
            if job_id in job_subscribers and q in job_subscribers[job_id]:
                job_subscribers[job_id].remove(q)

    return StreamingResponse(event_generator(), media_type="text/event-stream")

# -------------------------------------------------------------
# CLI Entrypoint
# -------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn
    import argparse

    parser = argparse.ArgumentParser(description="The Model Verse — Studio Server")
    parser.add_argument("--host", default="127.0.0.1", help="Host binding (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8000, help="Port binding (default: 8000)")
    args = parser.parse_args()

    print(f"\n=======================================================")
    print(f"🚀 THE MODEL VERSE — INTERACTIVE WEB STUDIO")
    print(f"🌐 Serving on: http://{args.host}:{args.port}")
    print(f"=======================================================\n")

    uvicorn.run("studio.server:app", host=args.host, port=args.port, reload=False)
