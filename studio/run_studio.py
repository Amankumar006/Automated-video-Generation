"""
The Model Verse — Studio Launcher
Launches the FastAPI Interactive Local Web Studio.
"""

import sys
import argparse
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import uvicorn

def main():
    parser = argparse.ArgumentParser(description="Launch The Model Verse Web Studio")
    parser.add_argument("--host", default="127.0.0.1", help="Host address (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8000, help="Port (default: 8000)")
    args = parser.parse_args()

    print("\n" + "=" * 65)
    print("📐 THE MODEL VERSE — INTERACTIVE LOCAL PRODUCTION STUDIO")
    print("=" * 65)
    print(f"🌐 Studio Web UI:  http://{args.host}:{args.port}")
    print(f"📡 REST API Docs:  http://{args.host}:{args.port}/docs")
    print(f"🎬 Videos Stored:  {PROJECT_ROOT}")
    print("=" * 65 + "\n")

    uvicorn.run("studio.server:app", host=args.host, port=args.port, reload=False)

if __name__ == "__main__":
    main()
