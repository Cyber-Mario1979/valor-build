# A18 — Runtime Mode Model (M1–M4)

**Status:** WRITTEN (B4) · **Gap:** G-16 / G-17 · **Decisions:** D-10/D-11 (M4 projection) · D-12 (staging) · D-13 (M4 no gates) · 3a/3b (latitude, owner) · **Baseline:** frozen pack v1.0.1 / `0ec3060`.
**Layer scope:** the build/runtime layer (L2 orchestration around the L1 pack). The pack (L1) is consumed read-only. Builds on **A16** (runtime spec) and **A17** (BUILD mode).

> B4 defines the runtime's **operating modes** — M1 Advisory, M2 Delivery Plan, M3 WP Mode, M4 Project Mode — the axis along which AI latitude and human-in-the-loop scale. The governing principle holds throughout: *Humans Decide; Valor Assists* — **AI freedom shrinks as stakes rise** (M1 → M3). The hard requirement (R1) is that this runtime axis stays **strictly separate** from the pack's engine-authority axis (`DESIGN`/`EXECUTION`) and from the lifecycle axis (`ARCH`/`BUILD`). Every clause traces to a settled decision (D-##), a confirmed gap (G-##), or pack content read at `0ec3060`. No invention; unknowns tagged **[OPEN]**.
>
> **Doc placement note:** like A16/A17, a build-repo architecture doc extending the A-series externally; lives in `docs/`, outside any hashed pack root (D-01/D-09); never folded into the pack.

---

## 1. Three axes, never conflated (R1)

Every runtime operation has a coordinate on **all three** axes. They are orthogonal — none substitutes for another. Collapsing them is exactly the mode collision Phase A's rename was meant to end.

| Axis | Values | Owns | Source |
|---|---|---|---|
| **Lifecycle** | `ARCH` / `BUILD` | are we designing the system or building the product? (`BUILD` = A17's log-only mode) | this build layer |
| **Engine-authority** | `DESIGN` / `EXECUTION` | the pack's per-action `allowed_modes` field | **the pack** (reference only; never redefined here) |
| **Runtime** | `M1` / `M2` / `M3` / `M4` | the operating mode / AI latitude scope | **A18 (new)** |

Verified at the pin: the engine axis is real and live — 7 actions allow `[DESIGN, EXECUTION]`, 5 are `[EXECUTION]`-only; **no leftover engine `M1/M2`** survives the rename. So the runtime `M1–M4` names cannot collide.

**Coordinate example:** *committing a staged task set* = `M3` (runtime) · `BUILD` or `LIVE` (lifecycle) · `EXECUTION` (engine-authority). Three independent dials on one operation.

---

## 2. Runtime modes M1–M4

Grounded against `CONTRACT_REGISTRY_v1.0.1.yaml` (7 contracts / 39 actions). The action **side-effect class** is what bounds each mode — not prose.

| Mode | Scope / entity | Reachable action classes | Real actions (registry) | Truth relation |
|---|---|---|---|---|
| **M1 Advisory** | any readable context | `READ_ONLY` + `VALIDATE_ONLY` (+ non-binding generation, see §3a) | all `orch-ks` (12), `orch-ps` (4), `WP_GET`, `RPT_LIST_ARTIFACTS`, `RPT_GET_ARTIFACT`, all `*_VALIDATE_*` | reads & validates only — **no truth, no staging** |
| **M2 Delivery Plan** | a selected WP set (which WPs exist, how linked) | `READ_ONLY` + plan proposal + `VALIDATE_ONLY` | `PLAN_GENERATE_PROPOSAL`, `PLAN_VALIDATE_PROPOSAL`, `WP_GET` across set, consolidated `RPT_*` | produces `PROPOSED` — **proposes, never commits** |
| **M3 WP Mode** | within **one** WP — the full path | all classes incl. `STAGE_ONLY`, `MUTATES_TRUTH`, `GENERATES_ARTIFACT` | `WP_STAGE_TASKS` → `WP_COMMIT_STAGED_TASKS` → `WP_APPLY_PLAN_PROPOSAL` → `DOC_GENERATE_DRAFT`/`DOC_FINALIZE_ARTIFACT` → `RPT_*`; `WP_UPDATE_TASK_FIELDS`, baseline-setters, `WP_RECORD_CONFIRMATION` | **writes truth** — every `MUTATES_TRUTH` is `confirm:true`; human gate always on (A17/D-08); **D-12** governs amend/commit |
| **M4 Project Mode** | a project composing `SELECTED_WP_SET` | `READ_ONLY` / projection + composition metadata | consolidated `RPT_GENERATE_*` over the set + references | **projection-only, NO truth gates (D-13)**; each WP runs M3 for its own truth; sole control = scope-bound |

The classes do the enforcing: M1 reaches only the 24 read/validate actions; **M3 is the only mode that reaches the 8 `MUTATES_TRUTH` + 1 `STAGE_ONLY`**; M4 reaches none of them (it projects over what M3 already wrote).

---

## 3. Per-mode AI latitude + output stamping

**Principle:** latitude shrinks `M1 → M3`. M4 sits off the ladder — its latitude is *compositional* (which WPs, how presented), never *mutational*.

| Mode | AI latitude | What the AI may do | Human role |
|---|---|---|---|
| **M1** | **HIGH** | read, validate, and **generate non-binding proposals/drafts** (§3a) | consumes advice; nothing to confirm (no truth touched) |
| **M2** | **MEDIUM** | compose the WP set; generate plan proposals (`PROPOSED`) | selects/links WPs; proposals stay advisory |
| **M3** | **LOW** | propose staged sets, field updates, plan applications | **confirms every truth mutation** at the gate (§3b) |
| **M4** | **COMPOSITIONAL** | propose which WPs to include + how to present the projection | bounds the selected set; owns each WP's truth via M3 |

**3a — M1 ceiling (owner-decided).** M1 **may** generate non-binding output (`PLAN_GENERATE_PROPOSAL`, `DOC_GENERATE_DRAFT`), provided it is stamped **`PROPOSED`/`DRAFT` + `mode: M1`** so it can never be read as a delivery commitment. Pure read-only Advisory would needlessly cripple the mode whose purpose is to think out loud.

**3b — M3 confirmation granularity (owner-decided).** M3 keeps the pack's **gate-level batch confirmation** as the floor (A04_1 §4.2: one Yes/No per commit, one per apply). Finer per-item review is an optional UI affordance **deferred to O2**, not a B4 requirement — the gate already captures consent; mandatory per-item confirm would slow M3 with no governance gain.

**Output stamp (every output, every mode).** Rides the **same audit channel** as the A16 §4 AI-call log and the A17 gate-outcome record — not a parallel log:
```
runtime_mode:     M1 | M2 | M3 | M4
lifecycle:        ARCH | BUILD          (BUILD adds PRODUCT_TESTING_ONLY, A17 §6)
engine_authority: DESIGN | EXECUTION    (pack field, reflected not redefined)
state:            PROPOSED | DRAFT | COMMITTED | FINAL | ...   (A04_1 §4.3 labels)
provenance:       prompt_version + input_hash + output_hash    (when an AI call was involved)
```

---

## 4. Label discipline (G-17) — three things that share the word "plan"

These MUST stay distinct in every screen, log line, and code identifier. Conflating them is G-17.

| Term | What it is | Axis | NOT |
|---|---|---|---|
| **M2 "Delivery Plan"** | a runtime **mode** — which WPs exist and how they link | runtime (§2) | a document; a within-WP step |
| **M3 "WP-Tasks Planning"** | task planning **within** a WP — the `GATE-Plan` step producing a `PROPOSED` schedule | engine gate (A04_1 §4.1) | a mode; a document |
| **"CQV plan"** | a **document output** (an artifact, e.g. a validation plan doc) | artifact (DOC) | a mode; a gate |

**Rule:** never use the bare word "plan." Always qualify — *Delivery Plan* (mode), *WP-tasks planning* (gate step), or *CQV plan document* (artifact).

---

## 5. Open / carried items (non-blocking for B4)

- **O2** UI — the optional per-item M3 review (§3b) lands here, plus the M4 projection presentation surface.
- **O1** LLM model spike · **O3** multi-user concurrency — per A16 §7.
- **Gate doc-reconcile** (carried from B3): six-gate shorthand → five canonical gates in G-02 / Phase-B plan / SESSION_LOG.
- **Schema-count reconcile** (A16 §5): 52-on-disk vs 51-cited.
- **G-07/B7** identity: outputs already stamp `actor_role` via the A10 soft-control stub; crypto-identity milestone remains carried.

---

### Exit criteria (B4) — met by this doc
- [x] Both axes documented and kept separate from the runtime axis (R1); engine `DESIGN`/`EXECUTION` referenced, not redefined.
- [x] Runtime `M1–M4` defined, each mapped to real action classes from the registry.
- [x] Per-mode latitude ladder set (M1 high → M3 low; M4 compositional), with 3a/3b owner decisions and the output stamp on the A16/A17 audit channel.
- [x] G-17 label discipline table + "never bare plan" rule.
- [x] Consistent with D-10/D-11 (M4 projection), D-12 (staging), D-13 (M4 no gates).

**Next:** B6 — walking skeleton (full thin vertical `stage → commit → plan → doc → export`, PE-HIGH, BUILD mode gates log-only) — G-04. B4 unblocks it; **B5** (Project container M4, G-18) is additive and available in parallel.
