# A16 — Runtime Target Spec

**Status:** WRITTEN (B2) · **Gap:** G-01 (biggest buildability gap, P0) · **Baseline:** frozen pack v1.0.1 / `0ec3060`.
**Layer scope:** the build layer (L2/L3 + the L1↔L2 boundary). The pack (L1) is consumed read-only; nothing here edits it.

> The pack specifies *what the system is* (contracts, schemas, WP truth, invariants). A16 specifies *what it is built on* — stack, store, the AI-call interface, and the seams between layers — concretely enough to build against. Every clause below traces to a settled decision (D-##), a confirmed gap (G-##), or pack content read directly from the `0ec3060` submodule. No invention; unknowns are tagged **[OPEN]**.
>
> **Doc placement note:** the pack's architecture series runs A00–A15. A16 is intentionally the *first build-repo* architecture doc — it extends the A-series **externally** and lives in `docs/`, outside any hashed pack root (D-01/D-09). It is never folded into the pack.

---

## 1. Scope & relationship to the pack

- A16 is **additive and external** to the frozen pack. It defines the runtime the pack runs *inside*, not the pack itself.
- **Three-layer stack** (governing principle: *Humans Decide; Valor Assists*; AI freedom shrinks as stakes rise):
  - **Layer 1 — Deterministic Python engine.** The frozen pack (`pack/` submodule, `0ec3060`). Contracts, schemas, WP truth, invariants. No AI inside. Read-only.
  - **Layer 2 — AI layer.** Narrative-only proposals through the locked **D-08** refuse/accept interface, bounded by CQV standards **as constraints, not text**. Lives entirely outside the pack (mitigates **R2** — AI creep into L1).
  - **Layer 3 — UI.** Multi-screen, **[OPEN — O2]**, not designed here.
- **What A16 does not do:** it does not redefine pack truth, re-specify contracts, or own the action catalogue. The pack's **`CONTRACT_REGISTRY_v1.0.1.yaml`** remains the single authoritative action↔schema map (see §5).

---

## 2. Stack (D-04)

- **Language:** Python, `requires-python >=3.11` (matches `pyproject.toml`).
- **Schema dialect:** **JSON Schema draft-07** — the dialect the pack's schema files are authored in. The build layer validates against them; it does not re-author them. *(Count clarification: 52 `.json` files under `schemas/` at `0ec3060`; 51 are draft-07 schemas carrying `$id`, and `schemas/documents/index.json` is a non-schema index manifest — so "51 schemas" and "52 files" both appear in the docs and are each correct in context.)*
- **Validation posture: fail-closed at every boundary.** Every cross-boundary call is validated against its declared schema *before* the call is allowed to take effect. A validation miss is a **refusal**, never a warning-and-proceed. This is the contract-validation layer named in D-04 and is the spine of §5.
- **Envelope:** every contract call carries the pack's standard request/response envelope —
  - request → `schemas/contracts/contract_request.schema.json`
  - response → `schemas/contracts/contract_response.schema.json`
  (the `schema_defaults` block in the registry). The build layer enforces the envelope on the way in and the action's `result_schema_ref` on the way out.
- **Dependencies (already pinned in `pyproject.toml`):** `jsonschema` (draft-07 validation), **`referencing`** (the real `$ref` registry — see §4, the A3 lesson), `pyyaml` (registry/contract bodies are YAML).

---

## 3. WP store (G-06 / D-03)

The pack fixes the *logical* truth model and constrains the *physical* store; it deliberately does not pick one. A16 picks it.

- **Store: file/git.** Chosen because it natively satisfies the mandated constraint — **append-only ID ledger + tombstoning** (pack `A04_2_WorkPackage_Arch`, §4). A plain mutable store does **not** satisfy it and is rejected.
- **Truth shape:** WP is the **single-entity, boundary-defended source of truth**. The store records truth transitions append-only; deletions are **tombstones**, never destructive edits; IDs are never reused.
- **Lock-aware write path from day one** (not retrofitted):
  - a **single commit chokepoint** — all `MUTATES_TRUTH` actions funnel through one write path;
  - an **advisory lock** around that path so concurrent writers serialize rather than corrupt.
- **Multi-user concurrency is deferred [OPEN — O3], not designed out.** The lock-aware chokepoint is precisely what keeps O3 an *extension* later, not a rewrite. Single-writer is the day-one assumption; the lock is the seam that makes multi-writer additive.
- **Side-effect discipline ties to the store:** of the 39 catalogued actions, **8 are `MUTATES_TRUTH`** and all 8 carry `confirm: true` — every truth mutation is human-confirmed at the boundary (Humans Decide). `STAGE_ONLY` (1) writes to a staging area, not truth; `READ_ONLY` (14) / `VALIDATE_ONLY` (10) never touch the write path; `GENERATES_ARTIFACT` (6) writes artifacts, not WP truth.

---

## 4. LLM interface (D-08 — LOCKED)

The AI call is **locked** by D-08; A16 records the locked shape, it does not reopen it. Model selection is the only open piece.

- **Prompt = versioned, hashed asset.** Prompts are not inline strings; they are stored assets with a version id and a content hash. The hash is logged on every call.
- **Determinism:** **temperature 0**; **schema-constrained JSON** output only — the model's response is validated against the relevant draft-07 result schema before it is allowed to mean anything. Free-form prose out is a refusal.
- **Refuse/accept loop:** on a schema-invalid response → **1 silent retry**; a **second** failure **escalates to a human** (never a third silent attempt, never a coerced parse). This is the D-08 interface the AI layer must call through; there is no side door to L1.
- **Audit log, every call:** `prompt_version` + `input_hash` + `output_hash` (+ accept/refuse outcome + escalation flag). Reproducibility of the AI call is an L2 concern logged here — **not** a pack edit (mitigates R2).
- **Validation lesson carried from A3 (load-bearing):** the validation layer must resolve `$ref`s through a real **`referencing`** registry keyed on **absolute `$id`s**. The pack's `valor://` scheme **defeats naive `urljoin`/relative ref-following** — that was the concrete A3 failure. The registry is built once from the pack's schemas at startup; refs resolve against it, not against the filesystem path.
- **Model selection: [OPEN — O1]** — a later spike. D-08 is model-agnostic by construction; swapping models must not change the interface.

---

## 5. Contract-enforcement map

**Approach (owner-decided):** *representative mapping + pointer to the live registry.* A16 documents the **enforcement pattern** and a handful of **worked examples**; it does **not** enumerate all 39 actions inline. The authoritative, complete, always-current map is the pack's **`contracts/CONTRACT_REGISTRY_v1.0.1.yaml`**. Rationale: the pack co-evolves into a deliberate v1.1.0 someday (D-02); an inline copy would silently drift, a pointer cannot. (A new action added in a future pack version is in-scope here **by pattern**, with zero A16 edit, provided the validation layer loads actions/schemas dynamically from the registry per §4 — which is the design intent.)

**The pattern (applies to every boundary, fail-closed):**

```
caller → [validate request envelope: contract_request.schema.json]
       → resolve action in registry → side_effect class + confirm rule + result_schema_ref
       → (if confirm:true) human confirmation gate
       → execute against L1 pack
       → [validate result against result_schema_ref]
       → [validate response envelope: contract_response.schema.json]
       → return | refuse
```

**Catalogue shape (read from the registry — the live source for the full map):**
- **7 contracts:** `orch-wp`, `orch-wp-user-driven-baseline`, `orch-plan`, `orch-doc`, `orch-rpt`, `orch-ks`, `orch-ps`.
- **39 actions**, by side-effect class: 14 `READ_ONLY` · 10 `VALIDATE_ONLY` · 8 `MUTATES_TRUTH` · 6 `GENERATES_ARTIFACT` · 1 `STAGE_ONLY`.
- **24 distinct `result_schema_ref`s** (heavy reuse — most WP actions resolve to `schemas/objects/work_package_schema.json`).

**Worked examples** (real action types + their `result_schema_ref`, lifted verbatim from the registry — these are illustrative, not the whole set; they also happen to trace the B6 walking-skeleton slice `stage → commit → plan → doc → export`):

| Boundary / step | Action (`type`) | Side-effect | Confirm | `result_schema_ref` |
|---|---|---|---|---|
| Root WP — stage | `WP_STAGE_TASKS` | `STAGE_ONLY` | no | `schemas/contracts/staged_task_set.schema.json` |
| Root WP — commit | `WP_COMMIT_STAGED_TASKS` | `MUTATES_TRUTH` | **yes** | `schemas/objects/work_package_schema.json` |
| Plan — propose | `PLAN_GENERATE_PROPOSAL` | `GENERATES_ARTIFACT` | no | `schemas/contracts/plan_proposal.schema.json` |
| Plan — apply to WP | `WP_APPLY_PLAN_PROPOSAL` | `MUTATES_TRUTH` | **yes** | `schemas/objects/work_package_schema.json` |
| Doc — draft | `DOC_GENERATE_DRAFT` | `GENERATES_ARTIFACT` | no | `schemas/contracts/doc_draft_result.schema.json` |
| Doc — finalize | `DOC_FINALIZE_ARTIFACT` | `GENERATES_ARTIFACT` | **yes** | `schemas/contracts/doc_artifact_result.schema.json` |
| Report — export | `RPT_GENERATE_WORKBOOK_EXPORT` | `GENERATES_ARTIFACT` | **yes** | `schemas/contracts/workbook_export_result.schema.json` |

> To read the full 39-action map, query `contracts/CONTRACT_REGISTRY_v1.0.1.yaml` at the pinned pack commit. Do not transcribe it here.

**[OPEN — minor, non-blocking]** schema-count reconcile: the registry maps actions to **24 distinct** result schemas; **52** schema files exist on disk at `0ec3060`; the gap assessment cited **51**. The 52-vs-51 is a 1-file discrepancy worth a later reconcile (likely an envelope/object schema not referenced as a result-ref) — it does not affect the enforcement pattern and does not block B2.

---

## 6. Seams

Three concrete interfaces. Each is one-directional in authority: stakes (and human-in-the-loop) rise leftward toward truth; AI latitude rises rightward toward narrative.

- **Seam A — Engine ↔ AI (L1 ↔ L2).** The **only** way L2 touches truth is by calling L1 contract actions through the validated envelope (§2, §5). L2 never reads or writes the store directly; it proposes, L1 validates and (on `confirm`) a human accepts. The D-08 refuse/accept loop (§4) is the gate. **This seam is where R2 is enforced** — no AI code path reaches inside the pack.
- **Seam B — AI ↔ UI (L2 ↔ L3).** L2 hands L3 **narrative proposals + provenance stamps** (mode, prompt-version, input/output hashes). L3 renders and collects the human accept/refuse; it does not itself reason about truth. **[OPEN — O2]** the concrete UI contract is undesigned.
- **Seam C — UI ↔ Engine (L3 ↔ L1), read path.** L3 reads WP truth for display via `READ_ONLY` actions (e.g. `WP_GET`, `RPT_GET_ARTIFACT`) — same validated envelope, no bypass. Display never mutates.
- **Cross-cutting — identity (G-07 / pack `A10_Security_Compliance`).** Day-one identity is **declared-role soft controls** (the A10 stub) with role-context captured into the audit log at every boundary. Cryptographic identity is deferred to the **named A10 integration point** — carried as the B7 milestone, not invented here.

---

## 7. Open items

Carried, all non-blocking for B2; each owned downstream:
- **O1 — LLM model selection.** Later spike. D-08 interface is model-agnostic (§4).
- **O2 — UI design.** Seam B / L3 concrete contract (§6) undesigned.
- **O3 — Multi-user concurrency.** Extension on the day-one lock-aware path (§3), not a rewrite.
- **O4 — cosmetic:** 3 KS schemas without trailing newline (pack-side, do not touch under freeze).
- **G-10 fold** (separate axis from §5): whether genuinely-new CQV requirements fold into `STD-CQV-BASE`. Awaiting owner confirm that audit C4-F1 ("drafts duplicative → nothing to fold") is settled, or the seven draft texts for a diff. Touches the standards, not the enforcement map.
- **Schema-count reconcile** (§5) — 52-on-disk vs 51-cited, 1 file.

---

### Exit criteria (B2) — met by this doc
- [x] Stack fixed (D-04): Python · draft-07 · fail-closed at every boundary.
- [x] Store fixed (G-06/D-03): file/git, append-only ledger + tombstoning, lock-aware write path day one, O3 deferred as extension.
- [x] LLM interface recorded as locked (D-08): hashed prompt · temp 0 · schema-constrained JSON · 1-retry-then-escalate · full audit hashes · `referencing`/absolute-`$id` resolution (A3 lesson).
- [x] Enforcement: pattern + worked examples + pointer to the registry as live authoritative map (39 actions / 7 contracts / 24 result schemas).
- [x] Seams A/B/C defined concretely with authority direction and the R2 enforcement point.
- [x] Open items carried with owners.

**Next:** B3 — BUILD mode (gates log-only / dormant) — G-02 / D-07.
