# Test Infrastructure & 4-Tier Verification Architecture

This document defines the architectural testing philosophy, four-tier methodology, test execution commands, and comprehensive feature coverage checklist for **The Model Verse Shorts Engine** and **Project Aether**.

---

## 1. Architectural Overview & Testing Philosophy

The repository harmonizes two complementary video synthesis engines:
1. **The Model Verse Shorts Engine (`pipeline/` + `manim_engine/`)**: 2D programmatic, mathematical, and algorithmic motion graphics explainer shorts (Manim Community, Cairo/FFmpeg, 9:16 vertical canvas).
2. **Project Aether (`aether/`)**: Multi-shot 3D generative cinematic virtual studio (world state graph, 6-critic Council with hard gates, surgical temporal inpainting, Complexity Levels 0–5).
3. **Shared Contract Adapter Layer (`aether/shared_contract.py`)**: Clean, decoupled inter-engine bridge (`ScriptToFilmSceneAdapter`, `EducationalAssetConditioningPackage`, `DualEnginePipelineConfig`) enabling Aether to consume Model Verse educational scripts and paper figure visual assets with zero cyclic dependencies.

### Core Testing Tenets

- **Anti-Facade / Zero-Cheating Guarantee**: All tests verify authentic logic, genuine filesystem artifacts, real Pydantic V2 validations, real image dimensions, and actual data flows. Facade tests, dummy assertions, or hardcoded return stubs are strictly prohibited.
- **Hermetic & Deterministic Execution**: Automated tests run completely offline without relying on external network endpoints (arXiv API, Hugging Face, Semantic Scholar) or live GPU diffusion APIs. Local fixtures (`public/arxiv_cache/2407.08608/source/`), synthetic CV tensors (for SSIM, optical flow, flickering, strobing), and mock LLM providers provide instant, deterministic execution.
- **Graceful Fault Tolerance & Defensive Boundaries**: Ingestion pipelines and visual directors must never crash on corrupted inputs, missing figures, or un-downloadable e-prints; they must degrade gracefully to verified fallbacks.
- **Cross-Engine Interoperability**: Verifies that 2D educational assets (SVG chalkboard diagrams, super-sampled raster diagrams) seamlessly condition 3D Aether shot requirements.

---

## 2. The 4-Tier Testing Methodology

The end-to-end verification suite follows a strict 4-Tier testing hierarchy implemented in `test/test_e2e_figure_and_subsystem.py`:

```
┌────────────────────────────────────────────────────────────────────────┐
│           Tier 4: Real-World Application Scenario (CLI E2E)           │
│  Full CLI pipeline execution (run_pipeline.py --arxiv 2407.08608)      │
│  Chalkboard asset generation, spec["paper_figures"], Beat 3 binding   │
├────────────────────────────────────────────────────────────────────────┤
│           Tier 3: Cross-Feature Combinations (Integration)             │
│  Fetch -> Script -> Storyboard loop; Aether asset conditioning bridge  │
│  DualEnginePipelineConfig beat allocation; Round-trip conversions      │
├────────────────────────────────────────────────────────────────────────┤
│           Tier 2: Boundary & Corner Cases (Defensive Hardening)        │
│  Missing e-prints, empty figure fallbacks, SVG vs Raster renderer      │
│  Malformed arXiv IDs, Pydantic spatial bounds validation               │
├────────────────────────────────────────────────────────────────────────┤
│           Tier 1: Feature Coverage (Subsystem & API Contracts)         │
│  Dual vector/raster extraction, fetch_arxiv_paper, generate_script     │
│  visual_director Beat 3 blueprint, ScriptToFilmSceneAdapter            │
└────────────────────────────────────────────────────────────────────────┘
```

### Tier 1: Feature Coverage (Unit / Subsystem Contracts)
Tests each core function and class in isolation against its interface contract:
- **Feature 1 (Dual Extraction)**: `extract_paper_figures` produces both SVG vector diagrams and super-sampled 350 DPI raster PNGs, populating `figure_id`, `caption`, `page_num`, `svg_path`, `image_path`, `original_type`, and `score`.
- **Feature 2 (ArXiv Fetcher)**: `fetch_arxiv_paper` inspects local cache, triggers figure extraction when `extract_figures=True`, and binds `res["paper_figures"]`.
- **Feature 3 (Script Generator)**: `generate_script` propagates `spec["paper_figures"]` from paper metadata or extracts figures if missing, setting `spec["arxiv_id"]`.
- **Feature 4 (CLI Pipeline)**: `run_pipeline.py` CLI workflow ingests arXiv papers and attaches figures to the production spec.
- **Feature 5 (Beat 3 Storyboard Binding)**: `VisualDirector.prepare_storyboard_for_spec` inspects `spec["paper_figures"]` and binds Beat 3 to `motif_type = "paper_figure"` with `kinetic_action = "figure_scan"` and parameters containing `svg_path`, `image_path`, and `arxiv_id`.
- **Feature 6 (Aether Shared Contract)**: `ScriptToFilmSceneAdapter.convert_spec_to_brief` converts a 6-beat `VideoSpec` into a `DirectorProductionBrief` containing 6 `FilmScene` objects with camera movements, locations, and durations.

### Tier 2: Boundary & Corner Cases (Defensive Robustness)
Verifies resilience against incomplete data and edge-case inputs:
- **Missing e-Print Source**: When arXiv e-print download fails or source directory does not exist, `extract_paper_figures` returns an empty list without raising unhandled exceptions.
- **Empty Figures Fallback**: When `spec["paper_figures"]` is empty or None, `VisualDirector` does not crash and falls back to standard code block, pipeline stages, or default layouts for Beat 3.
- **Preferred Renderer Selection**: Verifies that when an SVG exists, `preferred_renderer` is selected as `"vector"`, whereas when only a raster PNG exists, it resolves to `"raster"`.
- **Malformed & Edge-Case arXiv IDs**: Tests normalization of dirty inputs: URL formats (`https://arxiv.org/abs/2407.08608`), versioned strings (`2407.08608v2`), old-style IDs (`hep-th/9912012`), and malformed strings.
- **Conditioning Package Boundary Validation**: Tests that `EducationalAssetConditioningPackage` enforces normalized coordinate bounds `[0.0, 1.0]` of length 4, rejecting invalid bounds with descriptive errors.

### Tier 3: Cross-Feature Combinations (Integration Pipelines)
Tests multi-stage workflows across module boundaries:
- **Full Ingestion-to-Storyboard Pipeline**: Metadata ingestion (`fetch_arxiv_paper`) -> script synthesis (`generate_script`) -> visual choreography (`VisualDirector.prepare_storyboard_for_spec`), verifying end-to-end data flow into Beat 3's visual blueprint.
- **Cross-Engine Educational Asset Conditioning**: Extracts paper figures from `spec["paper_figures"]`, encapsulates them into `EducationalAssetConditioningPackage` with role `LEVEL_1_REFERENCE_IMAGE`, feeds them to `ScriptToFilmSceneAdapter.convert_spec_to_brief`, and verifies that the corresponding Aether `ShotRequirement` receives `first_frame_uri`, `reference_image_uri`, and conditioning metadata.
- **Dual-Engine Pipeline Configuration**: Verifies `DualEnginePipelineConfig` multi-beat allocation between 2D Manim, 3D Aether, and hybrid composite modes.
- **Reverse Brief-to-Spec Round Trip**: Verifies bidirectional translation from `DirectorProductionBrief` back into a 6-beat Model Verse `VideoSpec` outline.

### Tier 4: Real-World Application Scenario (CLI E2E)
Validates complete user-facing workflows matching production usage:
- **End-to-End CLI Pipeline Execution**: Simulates executing `run_pipeline.py --arxiv 2407.08608 --skip-render`:
  1. Ingests real FlashAttention-3 paper metadata from cache.
  2. Extracts chalkboard figures to `public/arxiv_cache/2407.08608/chalkboard_figures/`.
  3. Populates `spec["paper_figures"]`.
  4. Generates visual storyboard binding Beat 3 to `paper_figure`.
  5. Serializes spec to `pipeline/templates/`.
- **Manim Coordinate System Constraints**: Verifies that instantiated `BlueprintPaperFigure` elements respect 9:16 vertical canvas boundaries:
  - Upper boundary safe margin: `top_y <= 5.5`
  - Lower boundary safe margin: `bottom_y >= -2.5`
  - Clearance above subtitle pill (`y = -3.45`): `bottom_y - (-3.45) > 0.8`

---

## 3. Test Runner Commands & Execution Matrix

### Primary Commands

```bash
# 1. Run the comprehensive 4-Tier E2E & Subsystem Test Suite
pytest test/test_e2e_figure_and_subsystem.py -v

# 2. Run the arXiv Figure Extraction Test Suite
pytest test/test_arxiv_figure_extraction.py -v

# 3. Run the Aether Shared Contract Test Suite
pytest test/test_aether_shared_contract.py -v

# 4. Run all Project Aether Regression Test Suites (345+ tests)
pytest test/test_aether_*.py -v

# 5. Run the Full Acceptance Regression Suite (All M1, M2, M3 targets)
pytest test/test_arxiv_figure_extraction.py test/test_aether_*.py test/test_e2e_figure_and_subsystem.py -v
```

### Execution Performance Benchmarks

| Test Target | Test Count | Target Duration | Dependencies |
|---|---|---|---|
| `test/test_e2e_figure_and_subsystem.py` | 16+ tests | < 6.0s | PyMuPDF, PIL, in-memory fixtures |
| `test/test_arxiv_figure_extraction.py` | 6 tests | < 7.0s | Manim CE, PyMuPDF, PIL |
| `test/test_aether_shared_contract.py` | 22 tests | < 1.0s | Pydantic V2 |
| `test/test_aether_*.py` (Aether Core) | 345 tests | < 4.0s | Pydantic V2, numpy |
| **Combined Acceptance Suite** | **389+ tests** | **< 16.0s** | Zero network, zero GPU |

---

## 4. Coverage Checklist for Features in PROJECT.md

| Feature # | Feature Name | Milestone | Implementing Module | Primary Verification Test | Tier | Status |
|---|---|---|---|---|---|---|
| **F1** | Dual Vector & Raster Figure Extraction | M1 | `pipeline/arxiv_vector_extractor.py` | `test_tier1_extract_paper_figures_dual_formats`, `test_extract_paper_figures_high_res` | Tier 1 | ✅ Covered |
| **F2** | Automatic Figure Extraction in `arxiv_fetcher.py` | M1 | `pipeline/arxiv_fetcher.py` | `test_tier1_fetch_arxiv_paper_extracts_figures`, `test_tier2_missing_eprint_graceful_handling` | Tier 1, Tier 2 | ✅ Covered |
| **F3** | Figure Passthrough in `script_generator.py` | M1 | `pipeline/script_generator.py` | `test_tier1_generate_script_propagates_paper_figures` | Tier 1 | ✅ Covered |
| **F4** | CLI Pipeline Integration in `run_pipeline.py` | M1 | `pipeline/run_pipeline.py` | `test_tier1_run_pipeline_cli_figure_wiring`, `test_tier4_e2e_run_pipeline_execution` | Tier 1, Tier 4 | ✅ Covered |
| **F5** | Beat 3 Blueprint Binding in `visual_director.py` | M1 | `pipeline/visual_director.py` | `test_tier1_visual_director_binds_beat3_figure`, `test_tier2_empty_figures_fallback` | Tier 1, Tier 2 | ✅ Covered |
| **F6** | Clean Shared Contract for Aether | M2 | `aether/shared_contract.py` | `test_tier1_aether_adapter_spec_to_brief_conversion`, `test_tier3_aether_conditioning_asset_pipeline` | Tier 1, Tier 3 | ✅ Covered |
| **F7** | Architectural Boundaries & File Audit Documentation | M2 | `ARCHITECTURE.md`, `README.md` | Audit verification in `ARCHITECTURE.md` Section 4 & 5 | N/A (Doc) | ✅ Covered |
| **F8** | End-to-End Verification & Test Suite Hardening | M3 | Full test suite | Full pytest regression pass: `test/test_arxiv_figure_extraction.py`, `test/test_aether_*.py`, `test/test_e2e_figure_and_subsystem.py` | Tier 1–4 | ✅ Covered |

---

## 5. Verification Sign-off & Audit Compliance

All tests strictly follow the Teamwork testing framework:
1. Every test asserts on concrete observable outputs (file existence, pixel dimensions, schema attributes, layout coordinates).
2. All test cases are independent and self-cleaning.
3. No implementation code is mocked to bypass real business logic; only external networks and heavy subprocess renders are safely decoupled.
