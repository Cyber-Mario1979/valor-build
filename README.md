# valor-build

The **build layer** for VALOR — Phase B. This repo builds the runtime, the AI layer, and (later) the UI **around** the frozen **VALOR Architecture Pack**, which is consumed as a pinned, read-only dependency.

> **Principle:** *Humans Decide; Valor Assists.* The pack is the deterministic engine; everything here is additive and external to it.

## The three-layer stack

- **Layer 1 — Deterministic Python engine.** The **frozen pack** (`VALOR_Architecture_Pack` @ **v1.0.1 / `0ec3060`**). Contracts, schemas, WP truth, invariants. No AI inside.
- **Layer 2 — AI layer.** Narrative-only proposals through a locked refuse/accept interface (D-08), bounded by CQV standards as *constraints, not text*. Lives here, outside the pack.
- **Layer 3 — UI.** Multi-screen (Document Factory + others). Not yet designed.

## Status

Scaffold (Phase B / B1). No engine logic yet. The pack is pinned but its mount mechanism is **the one open decision** — see [`BUILD_STRATEGY.md` §2](./BUILD_STRATEGY.md).

## Where things live

- **`co-design/`** — continuity + decision record (session log, changelog, gap assessment v0.3, audit v1.0, freeze-status register, phase plans). Non-hashed; read these first.
- **`BUILD_STRATEGY.md`** — the repo seam, the pack pin, the co-evolve policy, LF discipline.
- **`docs/A16_Runtime_Target_Spec.md`** — the runtime spec (B2, skeleton for now).
- **`src/valor_build/`** — `engine/` (pack adapter), `ai/` (Layer 2), `modes/` (runtime M1–M4). Placeholders.

## Getting started (once the pack pin is chosen)

```bash
# clone (with submodule, if option A is chosen)
git clone --recurse-submodules <this-repo-url>
cd valor-build
python -m venv .venv && . .venv/bin/activate
pip install -e ".[dev]"
pytest
```

## Read order for a new session

1. `co-design/SESSION_LOG.md` — newest entry's **NEXT SESSION** block is the agenda.
2. `co-design/PHASE_B_BUILD_WORKFLOW_PLAN.md` — the roadmap for the current item.
3. `co-design/VALOR_Build_Readiness_Gap_Assessment_v0.3.md` — gap/decision detail.
4. `BUILD_STRATEGY.md` — the seam + working rules.
