"""
The Model Verse — Script Pedagogy & Comprehensibility Critic
Audits YouTube Shorts voiceover scripts for simplicity, everyday analogies,
jargon density, readability grade level, and retention pacing.
Ensures technical scripts are explainable to everyday viewers without academic jargon.
"""

import os
import re
import sys
import json
import argparse
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field, asdict
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))
import warnings
with warnings.catch_warnings():
    warnings.simplefilter("ignore", category=FutureWarning)
    import google.generativeai as genai

from pipeline.json_utils import robust_json_loads
load_dotenv(PROJECT_ROOT / ".env")

API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
if API_KEY:
    genai.configure(api_key=API_KEY)

MODEL_FALLBACKS = [
    os.getenv("GEMINI_MODEL_NAME", "gemini-3.1-flash-lite"),
    "gemini-3.1-flash-lite",
    "gemini-flash-latest",
    "gemini-2.0-flash",
    "gemini-3.8-flash"
]

# Curated High-Density Technical Jargon List
# Note: Standard developer vocabulary (GPU, RAM, tokens, parameter, bandwidth, latency, inference, AST, git)
# is fully allowed and encouraged when grounded by clear intuition.
HIGH_DENSITY_JARGON = {
    # Critical Jargon (-2.0 pts): Pure unexplained academic / tensor / hardware math
    "critical": [
        "softmax", "swiglu", "flops", "tflops", "eigenvector", "eigenvalue",
        "polysemantic", "monosemantic", "superposition", "sram",
        "hbm", "hbm3", "latent manifold", "manifolds", "hyperplane", "stochastic",
        "backpropagation", "loss landscape", "u-net", "variational", "markov",
        "differential equation", "score-based", "orthogonal", "bifurcation",
        "autoregressive", "p-value", "asymptotic",
        "feedforward", "residual stream", "logits", "activation vector", "matrix explosion"
    ],
    # Moderate Jargon (-0.6 pts): Obscure math/tech terms that need context
    "moderate": [
        "dot product", "embedding", "embeddings", "tensor",
        "tensors", "quantization", "weights matrix", "forward pass",
        "pruning", "checkpoint"
    ]
}

# AI Slop Clichés & Hallucinated Baby-Talk to ban (-2.5 pts each)
AI_SLOP_CLICHES = [
    "smart tool", "smart tools", "safe drawer", "safe drawers", "open desk",
    "delve into", "delving into", "in the realm of", "game changer", "game-changer",
    "revolutionize the way", "tapestry", "beacon", "testament", "ever-evolving",
    "furthermore", "moreover", "cutting-edge technology", "let's dive in",
    "unlock the power", "harness the power", "supercharge your", "magic box"
]

# Real-World Everyday Metaphors & Sensory Anchors
EVERYDAY_ANALOGY_ANCHORS = [
    # Visual / Physical everyday phenomena
    "static", "tv static", "snow", "mirror", "steam", "fog", "foggy", "cloud", "clouds",
    "sculptor", "sculpting", "marble", "stone", "dust", "chisel", "rabbit", "cat",
    "kitchen", "recipe", "chef", "salt", "onion", "library", "bookshelf", "book", "autocomplete",
    "phone", "napkin", "scratchpad", "actor", "stage", "improv", "whisper", "echo",
    "puzzle", "traffic", "highway", "sponge", "accordion", "flashlight", "spotlight",
    "water", "pipe", "dam", "funnel", "filter", "sieve", "colander", "train", "wagon",
    "shadow", "magnifying glass", "telescope", "ice cream", "coin toss", "roulette",
    "director", "movie", "film", "play", "actor", "sea", "ocean", "map", "blueprint", "carve", "chip away",
    # Developer & Operational physical analogies
    "relay race", "baton", "relay", "assembly line", "factory", "express lane", "cashier", "clerk", "waiter"
]


def count_syllables(word: str) -> int:
    """Estimates syllable count of an English word using phonological heuristics."""
    word = word.lower().strip(".:;?!'\"()[]{}")
    if not word:
        return 0
    if len(word) <= 3:
        return 1
    
    # Remove common non-syllabic endings
    word = re.sub(r'(?:[^laeiouy]|ed|es|e)$', '', word)
    if not word:
        return 1
    
    # Split hiatus vowel pairs that form distinct syllables (e.g. cha-os), but preserve suffixes like -tion/-sion
    word = re.sub(r'([aeou])([ao])', r'\1 \2', word)
    word = re.sub(r'(?<![tsc])i([aeo])', r'i \1', word)
        
    vowel_runs = re.findall(r'[aeiouy]+', word)
    count = len(vowel_runs)
    return max(1, count)


def compute_flesch_metrics(text: str) -> Tuple[float, float, int, int, int]:
    """
    Computes Flesch Reading Ease and Flesch-Kincaid Grade Level.
    Returns (reading_ease, grade_level, total_words, total_sentences, total_syllables).
    """
    # Clean sentences
    sentences = [s.strip() for s in re.split(r'[.!?]+', text) if s.strip()]
    total_sentences = max(1, len(sentences))
    
    words = [w.strip() for w in re.split(r'\s+', text) if re.search(r'\w', w)]
    total_words = max(1, len(words))
    
    total_syllables = sum(count_syllables(w) for w in words)
    
    asl = total_words / total_sentences  # Average Sentence Length
    asw = total_syllables / total_words  # Average Syllables per Word
    
    # Standard Flesch Reading Ease: 206.835 - 1.015 * ASL - 84.6 * ASW
    reading_ease = 206.835 - (1.015 * asl) - (84.6 * asw)
    reading_ease = max(0.0, min(100.0, reading_ease))
    
    # Flesch-Kincaid Grade Level: 0.39 * ASL + 11.8 * ASW - 15.59
    grade_level = (0.39 * asl) + (11.8 * asw) - 15.59
    grade_level = max(1.0, round(grade_level, 1))
    
    return reading_ease, grade_level, total_words, total_sentences, total_syllables


@dataclass
class BeatCriticResult:
    beat_id: int
    text: str
    word_count: int
    critical_jargon: List[str]
    moderate_jargon: List[str]
    analogies_found: List[str]
    reading_ease: float
    grade_level: float
    score: float
    suggestions: List[str]
    slop_cliches_found: List[str] = field(default_factory=list)


@dataclass
class ScriptCriticReport:
    title: str
    overall_score: float
    passed: bool
    reading_ease: float
    grade_level: float
    total_words: int
    total_critical_jargon: int
    total_moderate_jargon: int
    total_analogies: int
    beats: List[BeatCriticResult]
    jargon_list: List[str]
    analogy_list: List[str]
    pacing_warnings: List[str]
    llm_evaluation: Optional[Dict[str, Any]] = None
    summary_verdict: str = ""
    total_slop_cliches: int = 0
    slop_list: List[str] = field(default_factory=list)


class ScriptCritic:
    """
    Evaluates short-form video scripts on pedagogical simplicity,
    everyday metaphors, and retention suitability.
    """

    def __init__(self, target_grade_level: float = 9.0, min_score: float = 8.0):
        self.target_grade_level = target_grade_level
        self.min_score = min_score

    def analyze_beat(self, beat_id: int, text: str) -> BeatCriticResult:
        """Deterministic linguistic inspection of an individual beat."""
        words = [w.lower().strip(".,!?:;\"'()[]{}") for w in re.split(r'\s+', text) if w]
        text_lower = text.lower()
        word_count = len(words)
        
        # Jargon detection
        crit_found = []
        for term in HIGH_DENSITY_JARGON["critical"]:
            pattern = r'\b' + re.escape(term) + r'\b'
            if re.search(pattern, text_lower):
                crit_found.append(term)
                
        mod_found = []
        for term in HIGH_DENSITY_JARGON["moderate"]:
            pattern = r'\b' + re.escape(term) + r'\b'
            if re.search(pattern, text_lower):
                mod_found.append(term)
                
        # Analogy detection
        analogies = []
        for anchor in EVERYDAY_ANALOGY_ANCHORS:
            pattern = r'\b' + re.escape(anchor) + r'\b'
            if re.search(pattern, text_lower):
                analogies.append(anchor)

        # AI Slop Cliché detection
        slop_found = []
        for cl in AI_SLOP_CLICHES:
            pattern = r'\b' + re.escape(cl) + r'\b'
            if re.search(pattern, text_lower):
                slop_found.append(cl)
                
        reading_ease, grade_level, _, _, _ = compute_flesch_metrics(text)
        
        # Scoring logic (Base: 8.5)
        score = 8.5
        
        # Jargon penalties
        score -= len(crit_found) * 2.0
        score -= len(mod_found) * 0.5
        
        # AI Slop Cliché penalties (-2.5 pts each)
        score -= len(slop_found) * 2.5
        
        # Analogy reward
        score += min(2.5, len(analogies) * 1.2)
        
        # Grade level penalty (if higher than target grade level)
        if grade_level > self.target_grade_level:
            score -= (grade_level - self.target_grade_level) * 0.4
        elif grade_level <= 7.0:
            score += 0.5
            
        # Pacing budget (ideal: 18 - 28 words)
        suggestions = []
        if word_count < 14:
            score -= 0.5
            suggestions.append(f"Beat too short ({word_count} words). May sound clipped in audio.")
        elif word_count > 30:
            score -= 1.0
            suggestions.append(f"Beat too long ({word_count} words). Will cause hurried vocal pacing.")
            
        if crit_found:
            suggestions.append(f"Replace academic jargon: {', '.join(crit_found)} with everyday physical examples.")

        if slop_found:
            suggestions.append(f"CRITICAL: Remove AI slop / baby-talk: {', '.join(slop_found)}. Use real developer names.")
            
        if not analogies and beat_id == 2:
            suggestions.append("Add a central sensory or physical analogy (e.g. chef, relay race, mirror, clouds, sculptor).")
            
        score = max(1.0, min(10.0, round(score, 1)))
        
        return BeatCriticResult(
            beat_id=beat_id,
            text=text,
            word_count=word_count,
            critical_jargon=crit_found,
            moderate_jargon=mod_found,
            analogies_found=analogies,
            reading_ease=round(reading_ease, 1),
            grade_level=round(grade_level, 1),
            score=score,
            suggestions=suggestions,
            slop_cliches_found=slop_found
        )

    def evaluate_script(
        self,
        spec: Dict[str, Any],
        use_llm: bool = False
    ) -> ScriptCriticReport:
        """
        Runs comprehensive critique across all beats in a script spec.
        """
        title = spec.get("title", "Untitled Script")
        beats_data = spec.get("beats", [])
        
        analyzed_beats: List[BeatCriticResult] = []
        all_text_list = []
        all_crit_jargon = set()
        all_mod_jargon = set()
        all_analogies = set()
        all_slop_cliches = set()
        
        for idx, b in enumerate(beats_data):
            b_id = b.get("beat_id", idx + 1)
            b_text = b.get("text", "")
            all_text_list.append(b_text)
            
            b_res = self.analyze_beat(b_id, b_text)
            analyzed_beats.append(b_res)
            all_crit_jargon.update(b_res.critical_jargon)
            all_mod_jargon.update(b_res.moderate_jargon)
            all_analogies.update(b_res.analogies_found)
            all_slop_cliches.update(b_res.slop_cliches_found)
            
        full_text = " ".join(all_text_list)
        total_reading_ease, overall_grade_level, total_words, _, _ = compute_flesch_metrics(full_text)
        
        # Composite deterministic score
        if analyzed_beats:
            beat_scores = [b.score for b in analyzed_beats]
            det_score = sum(beat_scores) / len(beat_scores)
        else:
            det_score = 5.0
            
        # Hook bonus (Beat 1)
        b1 = analyzed_beats[0] if analyzed_beats else None
        if b1:
            # Check for curiosity hooks: questions, second person, curiosity triggers
            if any(w in b1.text.lower() for w in ["you", "your", "?", "bizarre", "imagine", "ever", "vanish", "secret", "waste", "every"]):
                det_score = min(10.0, det_score + 0.3)
                
        pacing_warnings = []
        if total_words < 90:
            pacing_warnings.append(f"Script total word count is very short ({total_words} words). Target: 110-135 words.")
        elif total_words > 165:
            pacing_warnings.append(f"Script total word count is high ({total_words} words). May exceed 60s at standard pacing.")

        llm_eval = None
        final_score = det_score
        
        if use_llm and API_KEY:
            llm_eval = self._call_gemini_critic(title, analyzed_beats)
            if llm_eval and "overall_score" in llm_eval:
                final_score = round(0.4 * det_score + 0.6 * float(llm_eval["overall_score"]), 1)
        else:
            final_score = round(det_score, 1)

        passed = (
            final_score >= self.min_score and
            overall_grade_level <= (self.target_grade_level + 1.5) and
            len(all_crit_jargon) == 0 and
            len(all_slop_cliches) == 0
        )
        
        if passed:
            verdict = "✅ APPROVED: The script is conversational, intuitive, grounded in everyday examples, and free of AI slop."
        else:
            reasons = []
            if len(all_slop_cliches) > 0:
                reasons.append(f"contains {len(all_slop_cliches)} AI slop cliché(s): {', '.join(all_slop_cliches)}")
            if len(all_crit_jargon) > 0:
                reasons.append(f"contains {len(all_crit_jargon)} heavy jargon term(s): {', '.join(all_crit_jargon)}")
            if overall_grade_level > self.target_grade_level + 1.0:
                reasons.append(f"reading level is Grade {overall_grade_level} (target: Grade {self.target_grade_level})")
            if final_score < self.min_score:
                reasons.append(f"overall score {final_score}/10 is below threshold {self.min_score}")
            verdict = f"❌ REJECTED: Script {', '.join(reasons)}."

        return ScriptCriticReport(
            title=title,
            overall_score=final_score,
            passed=passed,
            reading_ease=round(total_reading_ease, 1),
            grade_level=round(overall_grade_level, 1),
            total_words=total_words,
            total_critical_jargon=len(all_crit_jargon),
            total_moderate_jargon=len(all_mod_jargon),
            total_analogies=len(all_analogies),
            beats=analyzed_beats,
            jargon_list=sorted(list(all_crit_jargon | all_mod_jargon)),
            analogy_list=sorted(list(all_analogies)),
            pacing_warnings=pacing_warnings,
            llm_evaluation=llm_eval,
            summary_verdict=verdict,
            total_slop_cliches=len(all_slop_cliches),
            slop_list=sorted(list(all_slop_cliches))
        )

    def _call_gemini_critic(
        self,
        title: str,
        beats: List[BeatCriticResult]
    ) -> Optional[Dict[str, Any]]:
        """Invokes Gemini as an everyday YouTube audience persona."""
        beats_json = []
        for b in beats:
            beats_json.append({
                "beat_id": b.beat_id,
                "text": b.text,
                "word_count": b.word_count
            })
            
        prompt = f"""You are a veteran YouTube Shorts Creative Director and science communicator in the style of Veritasium and Cleo Abram.
Your audience is everyday curious people, students, and tech enthusiasts. They do NOT have a computer science degree.

Review this proposed voiceover script for an animated short:
Title: "{title}"
Beats:
{json.dumps(beats_json, indent=2)}

Evaluate strictly across these criteria:
1. **Conversational Simplicity (1-10)**: Is the language plain, direct, and conversational? Or does it sound like an academic textbook or Wikipedia?
2. **Everyday Analogies & Sensory Grounding (1-10)**: Does it use tangible real-world comparisons (e.g. foggy mirrors, cooking recipes, sculptors, clouds, libraries) instead of formulas or abstract matrices?
3. **Hook & Curiosity (1-10)**: Does Beat 1 grab attention in the first 3 seconds with a relatable mystery or question?
4. **Overall Pedagogical Score (1-10)**: Would a 14-year-old or non-tech viewer fully understand how it works?

Respond strictly in valid JSON with this exact schema:
{{
  "overall_score": 8.8,
  "conversational_score": 9.0,
  "analogy_score": 8.5,
  "hook_score": 9.0,
  "estimated_audience_grade": 7.5,
  "jargony_phrases_to_simplify": ["list of confusing phrases if any"],
  "effective_analogies_praised": ["list of strong examples used"],
  "beat_by_beat_critique": [
    {{"beat_id": 1, "critique": "Strong hook with TV static.", "suggested_tweak": null}}
  ],
  "director_verdict": "Clear summary sentence."
}}
"""
        for model_name in MODEL_FALLBACKS:
            try:
                model = genai.GenerativeModel(model_name)
                resp = model.generate_content(
                    prompt,
                    generation_config={"response_mime_type": "application/json"}
                )
                text = resp.text.strip()
                if "```json" in text:
                    text = text.split("```json")[1].split("```")[0].strip()
                return robust_json_loads(text)
            except Exception as e:
                continue
        return None


def format_report_markdown(report: ScriptCriticReport) -> str:
    """Formats the audit report into a rich Markdown summary."""
    lines = [
        f"# 🎙️ Script Pedagogy & Comprehensibility Audit: *{report.title}*",
        f"\n**Verdict:** {report.summary_verdict}",
        f"\n### 📊 Key Metric Scoreboard",
        f"| Metric | Measurement | Target | Status |",
        f"| :--- | :--- | :--- | :--- |",
        f"| **Overall Pedagogical Score** | **{report.overall_score} / 10.0** | $\\ge 8.0$ | {'🟢 PASS' if report.overall_score >= 8.0 else '🔴 FAIL'} |",
        f"| **Flesch-Kincaid Grade Level** | **Grade {report.grade_level}** | $\\le 8.5$ (Middle School) | {'🟢 PASS' if report.grade_level <= 8.5 else '🟡 WARNING' if report.grade_level <= 10.5 else '🔴 FAIL (Too Academic)'} |",
        f"| **Flesch Reading Ease** | **{report.reading_ease} / 100** | $\\ge 60.0$ (Conversational) | {'🟢 PASS' if report.reading_ease >= 60.0 else '🔴 FAIL'} |",
        f"| **Heavy / Academic Jargon** | **{report.total_critical_jargon} terms** | $0$ terms | {'🟢 ZERO JARGON' if report.total_critical_jargon == 0 else '🔴 JARGON DETECTED'} |",
        f"| **AI Slop Clichés** | **{report.total_slop_cliches} clichés** | $0$ clichés | {'🟢 ZERO SLOP' if report.total_slop_cliches == 0 else '🔴 AI SLOP DETECTED'} |",
        f"| **Everyday Analogies Found** | **{report.total_analogies} anchors** | $\\ge 3$ physical anchors | {'🟢 RICH ANALOGIES' if report.total_analogies >= 3 else '🟡 NEEDS MORE ANALOGIES'} |",
        f"| **Total Word Count** | **{report.total_words} words** | 110 – 140 words | {'🟢 OPTIMAL' if 100 <= report.total_words <= 145 else '🟡 PACING ALERT'} |",
    ]
    
    if report.slop_list:
        lines.append(f"\n🚫 **Detected AI Slop Clichés:** `{', '.join(report.slop_list)}`")
    if report.jargon_list:
        lines.append(f"\n⚠️ **Detected Jargon Terms:** `{', '.join(report.jargon_list)}`")
    if report.analogy_list:
        lines.append(f"\n💡 **Grounded Everyday Analogies:** `{', '.join(report.analogy_list)}`")
        
    lines.append(f"\n---")
    lines.append(f"### 🔍 Beat-by-Beat Detailed Breakdown")
    for b in report.beats:
        status_icon = "🟢" if b.score >= 8.0 else "🟡" if b.score >= 6.5 else "🔴"
        lines.append(f"\n#### Beat {b.beat_id}: {status_icon} Score {b.score}/10 (Grade {b.grade_level} | {b.word_count} words)")
        lines.append(f"> *\"{b.text}\"*")
        if b.analogies_found:
            lines.append(f"- **Metaphors**: `{', '.join(b.analogies_found)}`")
        if b.critical_jargon or b.moderate_jargon:
            lines.append(f"- **Jargon**: Critical: `{b.critical_jargon}`, Moderate: `{b.moderate_jargon}`")
        if b.suggestions:
            for s in b.suggestions:
                lines.append(f"- 💡 *Suggestion*: {s}")

    if report.llm_evaluation:
        lines.append(f"\n---")
        lines.append(f"### 🎬 YouTube Creative Director Persona Feedback (Gemini)")
        llm = report.llm_evaluation
        lines.append(f"- **Director Score**: {llm.get('overall_score')}/10 (Conversational: {llm.get('conversational_score')}/10, Analogies: {llm.get('analogy_score')}/10)")
        lines.append(f"- **Verdict**: {llm.get('director_verdict')}")
        if llm.get("effective_analogies_praised"):
            lines.append(f"- **Praised Analogies**: {', '.join(llm.get('effective_analogies_praised'))}")
        if llm.get("jargony_phrases_to_simplify"):
            lines.append(f"- **Phrases to Simplify**: {', '.join(llm.get('jargony_phrases_to_simplify'))}")
            
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="The Model Verse — Script Pedagogy & Comprehensibility Critic")
    parser.add_argument("--spec", help="Path to script template JSON")
    parser.add_argument("--use-llm", action="store_true", help="Invoke Gemini for deep qualitative persona critique")
    parser.add_argument("--compare", nargs=2, help="Compare two script templates (e.g. old vs new)")
    args = parser.parse_args()

    critic = ScriptCritic()

    if args.compare:
        p1, p2 = Path(args.compare[0]), Path(args.compare[1])
        with open(p1, "r", encoding="utf-8") as f:
            s1 = json.load(f)
        with open(p2, "r", encoding="utf-8") as f:
            s2 = json.load(f)

        r1 = critic.evaluate_script(s1, use_llm=args.use_llm)
        r2 = critic.evaluate_script(s2, use_llm=args.use_llm)

        print(format_report_markdown(r1))
        print("\n" + "="*80 + "\n")
        print(format_report_markdown(r2))
        return

    if args.spec:
        with open(args.spec, "r", encoding="utf-8") as f:
            spec = json.load(f)
        report = critic.evaluate_script(spec, use_llm=args.use_llm)
        print(format_report_markdown(report))
    else:
        print("Usage: python3 pipeline/script_critic.py --spec <template.json> [--use-llm]")


if __name__ == "__main__":
    main()
