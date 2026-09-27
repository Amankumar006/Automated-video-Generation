import asyncio
import json
import edge_tts

TEXT = "DeepSeek-V3 has 671 billion parameters. But for each token, its gating network routes to only 8 out of 256 experts. That is just 37 billion active parameters!"
VOICE = "en-US-ChristopherNeural"

async def main():
    communicate = edge_tts.Communicate(TEXT, VOICE, rate="+10%")
    words = []
    
    with open("public/deepseek_moe_voice.mp3", "wb") as f:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                f.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                start_sec = round(chunk["offset"] / 10_000_000, 3)
                end_sec = round((chunk["offset"] + chunk["duration"]) / 10_000_000, 3)
                words.append({
                    "word": chunk["text"],
                    "start": start_sec,
                    "end": end_sec,
                })
    
    with open("public/deepseek_moe_words.json", "w", encoding="utf-8") as f:
        json.dump(words, f, indent=2)
    
    print(f"Generated voice and {len(words)} word timestamps.")

if __name__ == "__main__":
    asyncio.run(main())
