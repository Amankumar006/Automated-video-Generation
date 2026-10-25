# Repository layout

The repository keeps runtime code stable while making generated state clearly
separate from source code.

| Path | Purpose | Commit policy |
| --- | --- | --- |
| `pipeline/` | Ingestion, scripting, audio, publishing, and orchestration | Source |
| `manim_engine/` | Manim scenes, primitives, controllers, and visual composition code | Source |
| `scripts/` | Maintenance and asset-generation utilities | Source |
| `test/` | Python integration and unit tests | Source |
| `src/` | Remotion preview application | Source |
| `docs/` | Setup, architecture, contributor, and operational documentation | Source |
| `skills/` | Optional local YouTube workflow skills | Source |
| `public/sfx/`, `public/brand/` | Small reusable runtime assets | Curated assets |
| `public/math_svgs/` | Curated formula assets used by scenes | Curated/generated assets |
| `pipeline/templates/` | Reusable script/scene specifications | Source fixtures |
| `_archive/` | Historical Aether and superseded experiments | Not imported at runtime |
| `media/`, `output/`, `frames_*`, `final_*.mp4` | Local render products and inspection output | Ignored |
| `node_modules/`, caches | Downloaded dependencies and caches | Ignored |

GitHub contribution forms, ownership, and maintainer settings live under
`.github/`. Remote branch protection and required-check settings are documented
in [`docs/GITHUB_MAINTAINER_SETUP.md`](GITHUB_MAINTAINER_SETUP.md) and must be
enabled by a repository administrator.

Do not place generated videos, frame dumps, credentials, provider tokens, or
model weights in Git. Add a small deterministic fixture under `test/` or
`pipeline/templates/` when a generated artifact is required for validation.
