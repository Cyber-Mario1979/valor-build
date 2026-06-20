# B6 — Walking Skeleton (implementation note)

**Status:** LANDED (B6) · **Gap:** G-04 (full-vertical walking skeleton, P0) · **Milestone:** first runnable build (`0.1.0`) · **Baseline:** frozen pack v1.0.1 / `0ec3060`.
**Layer scope:** the build/runtime layer (L2) in `src/valor_build/`. The pack (L1) is consumed read-only; nothing here edits it.

> This is an **implementation note**, not an architecture spec — hence the `B6` prefix, not `A19`. The architecture is fixed by A16 (runtime target), A17 (BUILD mode), A18 (mode model); B6 is the first code that makes those three run. It proves the contract path executes end-to-end, thin but full vertical, against the only live domain (PE-HIGH), with gates logging only.

---

## 1. What it does

Runs the full slice in one pass — **`create → stage → commit → plan → apply → draft → finalize → export`** — for one PE-HIGH work package, in **M3** (runtime) · **BUILD** (lifecycle) · **EXECUTION** (engine-authority):

```
python -m valor_build.skeleton
```

Every step crosses the dispatch spine (A16 §5): request-envelope validation → action resolution against the frozen registry → runtime-mode reachability (A18) → gate evaluation (A17, log-only in BUILD) → human-confirmation gate (always live) → handler execution → result-schema validation → response-envelope validation → output stamp + audit. A validation miss at any boundary is a **refusal**, never a warning-and-proceed.

---

## 2. The eight steps and their real actions

All action types, side-effect classes, confirm rules, and result schemas are read from the pinned pack's `CONTRACT_REGISTRY_v1.0.1.yaml` — none are transcribed into code.

| Step | Action (`type`) | Side-effect | Confirm | Gate (A17) |
|---|---|---|---|---|
| create | `WP_CREATE` | MUTATES_TRUTH | yes | — (root container) |
| stage | `WP_STAGE_TASKS` | STAGE_ONLY | no | GATE-Stage |
| commit | `WP_COMMIT_STAGED_TASKS` | MUTATES_TRUTH | yes | GATE-Commit |
| plan | `PLAN_GENERATE_PROPOSAL` | GENERATES_ARTIFACT | no | GATE-Plan |
| apply | `WP_APPLY_PLAN_PROPOSAL` | MUTATES_TRUTH | yes | GATE-Apply |
| draft | `DOC_GENERATE_DRAFT` | GENERATES_ARTIFACT | no | — (DRAFT, AI step) |
| finalize | `DOC_FINALIZE_ARTIFACT` | GENERATES_ARTIFACT | yes | — (Finalize ≠ gate, A17 §6) |
| export | `RPT_GENERATE_WORKBOOK_EXPORT` | GENERATES_ARTIFACT | yes | GATE-Export |

The slice exercises **all five canonical gates exactly once** and the **two non-gate confirm steps** (finalize, and the root create).

---

## 3. Module map (`src/valor_build/`)

- **`pack_access.py`** — locates the read-only pack (env `VALOR_PACK_ROOT` or walk-up to `pack/`); reads registry + schema files.
- **`engine/schemas.py`** — schema registry + fail-closed validator. Builds a `referencing` registry on absolute `$id`s and **rewrites relative `valor://` `$ref`s to absolute** at load (the A3 lesson; `urljoin` won't resolve a custom scheme).
- **`engine/registry.py`** — typed view over the contract registry: `type`/alias → `ActionSpec(side_effect, confirm, result_schema_ref)`.
- **`engine/store.py`** — file WP store: append-only `ledger.jsonl`, tombstoning, never-reused ID ledger, **single `commit_truth` chokepoint** under an advisory lock; non-truth staging area for STAGE_ONLY + artifact intermediates. Git-commit-per-write is the production `commit_hook` (default no-op).
- **`engine/gates.py`** — the five canonical gates; BUILD logs `WOULD_BLOCK` and proceeds, LIVE raises `GateBlocked`.
- **`engine/audit.py`** — the single audit channel (gate outcomes + AI provenance + output stamps) + sha256 hashing.
- **`modes/runtime.py`** — M1–M4 reachability by side-effect class; M3 reaches all, M1 refuses MUTATES_TRUTH before dispatch.
- **`ai/interface.py`** — the D-08 locked interface: versioned/hashed prompt asset, schema-constrained JSON, 1-retry-then-escalate, audited every call. The model is a deterministic stub (temp 0); a real model is the only seam (`Generator`), O1.
- **`engine/domain.py`** — reads the real `TP/PROF/PS-PE-HIGH` trio from the pack; CAL-WORKWEEK working-day calculator for the scheduler.
- **`engine/dispatch.py`** — the A16 §5 spine (above).
- **`engine/handlers.py`** — the eight thin, schema-valid handlers; truth via the chokepoint, the draft via the D-08 interface.
- **`skeleton.py`** — drives the slice; runnable as `__main__`.

---

## 4. What is real vs. stubbed (honest scope)

- **Real:** the enforcement spine; fail-closed validation against the frozen schemas at every boundary; the append-only/tombstoning/never-reused-ID store with a lock-aware chokepoint; the five gates with BUILD/LIVE behaviour; M1–M4 reachability; the D-08 refuse/accept/escalate loop with provenance hashes; the PE-HIGH task/duration data, read from the pack.
- **Stubbed (by design, carried):** the **model** behind the D-08 interface is deterministic (O1); the **git commit** per truth-write is a no-op hook (production wiring); the **calendar** is a minimal Mon–Fri forward pass; the **UI** does not exist (O2). The slice stages **one** task for thinness — multi-task/dependency staging is additive, the scheduler already walks a task list.

---

## 5. Tests (`tests/test_walking_skeleton.py`)

Ten checks lock the invariants: full slice runs; all five gates logged; committed truth persisted with applied dates; **unmet gate proceeds in BUILD / halts in LIVE**; **confirmation No leaves truth unmutated**; BUILD outputs carry `PRODUCT_TESTING_ONLY`; IDs never reused; **M1 cannot reach a MUTATES_TRUTH action**; the AI call is audited with input/output hashes.

---

## 6. Carried / non-blocking

O1 model · O2 UI · O3 multi-user (the lock-aware chokepoint keeps it an extension) · gate doc-reconcile (6→5 shorthand in G-02 / Phase-B plan / older SESSION_LOG) · schema-count 52-on-disk vs 51-`$id` (the 52nd, `documents/index.json`, carries no `$id`) · G-10 fold · G-07/B7 crypto-identity.

**Next:** B5 — Project container (M4 projection over `SELECTED_WP_SET`), G-18 — additive on top of the M3 slice this milestone proved.
