# 🤝 CONTRIBUTING.md — Contributing to The Model Verse

Welcome to **The Model Verse Shorts** engineering team! This guide outlines our development workflow, coding conventions, testing standards, and pull request protocol.

---

## 1. Core Engineering Principles

### Backend-First Protocol
The core engine is Python and Manim-based. **Do not modify, refactor, or write frontend code** (`src/`, Remotion components) unless explicitly tasked by the user. Default to focusing on backend algorithms, pipelines, Manim geometric primitives, and data ingestion.

### Read-Only Testing & PR Protocol
- When testing or investigating issues, default to read-only diagnostics and non-destructive scripts.
- Never edit production files directly or push directly to `main`.
- Always create a dedicated feature branch (`feat/<feature-name>` or `fix/<bug-name>`), verify all tests locally, and open a GitHub Pull Request with full verification details.

---

## 2. Environment Setup

### Prerequisites
- **Python:** 3.12+ (managed via `pyenv` or `venv`)
- **System Binaries:** `ffmpeg`, `cairosvg`, `pango`, `pkg-config`
  ```bash
  # macOS (Homebrew)
  brew install ffmpeg pango cairo pkg-config
  
  # Linux (Ubuntu/Debian)
  sudo apt-get update && sudo apt-get install -y ffmpeg libpango1.0-dev libcairo2-dev
  ```

### Python Virtual Environment
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Environment Variables (`.env`)
Create a `.env` file in the repository root:
```ini
GEMINI_API_KEY=your_gemini_api_key_here
GITHUB_TOKEN=optional_github_personal_access_token
```

---

## 3. Safe Zone & Visual Geometry Rules

All animations are designed for **9:16 vertical video**:
- **Canvas Dimensions:** `config.frame_width = 9.0`, `config.frame_height = 16.0`.
- **Hero Safe Zone:** Keep all visual compositions between $Y \in [-2.4, 5.5]$ and $X \in [-3.6, 3.6]$.
- **Kinetic Subtitle Pill:** Positioned at $y = -3.45$. All visual compositions must maintain a **clearance buffer $\ge 0.95$ units** above $y = -3.45$ (bottom edge of mobject must stay $\ge -2.40$).
- **Top Safe Zone:** Leave room above $y = 6.2$ for mobile app navigation bars. Brand watermark is placed at $y = 7.10$.

---

## 4. Testing Standards

Every feature or bug fix must include automated unit tests and pass headless visual inspection:

### 1. Run Unit Tests
```bash
# Run full repository test suite
pytest

# Run targeted test suites
pytest test/test_code_execution_engine.py test/test_github_trending_fetcher.py -v
```

### 2. Verify Headless Render
```bash
# Render keyframe at 540x960 vertical resolution
manim -ql -s -r 540,960 --fps 15 test/test_code_execution_engine.py TestChalkboardCodeBlockScene
```

---

## 5. Pull Request Process

1. **Create a Branch:**
   ```bash
   git checkout -b feat/my-new-feature
   ```
2. **Commit with Semantic Messages:**
   ```bash
   git commit -m "feat: add novel 3b1b primitive for diffusion trajectory"
   ```
3. **Push & Create PR:**
   ```bash
   git push -u origin feat/my-new-feature
   gh pr create --title "feat: my new feature" --body "Detailed summary of changes"
   ```
