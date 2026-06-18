# Valor Architecture Pack — Audit Report

**Status:** COMPLETE · all 4 chunks + consolidated verdict
**Date:** 2026-06-16
**Auditor:** co-design (Mervat) · Owner review: Amr
**Pack under audit:** `Cyber-Mario1979/VALOR_Architecture_Pack` @ HEAD (default branch), pack_version `v1.0.1`, manifest `v1.0.1`
**Method:** fresh clone; files read directly; integrity scripts executed live. Every finding tagged CONFIRMED / TO VERIFY / DESIGN / NEW.

> All four chunks and the consolidated verdict are complete. The remaining step is to act on it: reissue the gap assessment at **v0.3** and update `SESSION_LOG.md` + `CHANGELOG.md` (see "Recommended next actions").

---

## Chunk 1 — Foundation & Control

**Read this chunk:** `A00_Specs_Architecture_Pack`, `A01_SoS_Context_Capability`, `scripts/pack_validation/generate_manifest.py`, `scripts/pack_validation/verify_manifest.py`, `.github/workflows/ci.yml`, `manifest.yaml` (header + structure), `requirements.txt`. Plus a live `verify_manifest` run and an exclude-divergence simulation.

### C1-F1 · What the pack claims to be — CONFIRMED
A00 frames Valor as a contract-driven **System of Systems for CQV execution**; explicit **non-scope**: no software implementation, no e-signatures/QMS workflow, no fabricated regulated evidence. A01 sharpens it: a *deterministic assistant that proposes, validates, and structures — humans decide and approve*; nine subsystems; **WP = single source of truth**; Reporting/Export is projection-only (never mutates truth). This confirms the Session-1 reframing (**Humans Decide; Valor Assists**) directly from the top-level specs, and confirms the pack is *design-complete on governance but carries no runtime/buildability content* — consistent with **G-01** (no runtime target spec). A00 also fixes a canonical reading order, useful for sequencing the rest of the audit.

### C1-F2 · G-12 (CI purpose) — CONFIRMED, and weaker than assumed
`ci.yml` triggers on push/PR to `main`/`master` and runs **exactly one step: `python smoke_test.py`**. It does **not** invoke `verify_manifest.py`, and there is no explicit schema-integrity step. **Manifest integrity is therefore not an automated CI gate.** Whether `smoke_test.py` verifies the manifest/schemas internally is unknown — carried to **Chunk 3**. Until proven otherwise, manifest drift on a PR would pass CI silently.
**Recommendation:** add a `verify_manifest.py` step to the CI job (and, once schemas are read, an explicit schema-validation step). Converts **G-12: TO VERIFY → CONFIRMED**, with one residual to close in Chunk 3.

### C1-F3 · NEW — generator/verifier exclude-set divergence (CONFIRMED by demonstration)
The two integrity scripts use **different ignore rules**, so they disagree about what counts as a pack file:

| | `generate_manifest.py` | `verify_manifest.py` |
|---|---|---|
| Ignored dirs | `.git .venv __pycache__ .pytest_cache .mypy_cache .ruff_cache .idea .vscode` | `.venv venv __pycache__ .vscode .git` |
| Match depth | **any depth** | **top-level only** (`parts[0]`) |
| Ignored suffixes | `.pyc .pyo .pyd` | **none** |

**Demonstrated live:** dropping a `.pytest_cache/CACHEDIR.TAG` and a stray `stray.pyc` into the root — both normal after running tests — makes `verify_manifest.py` report **FAIL → "extra files,"** even though `generate_manifest.py` correctly omits them. So routine local testing can trigger spurious integrity failures, and the scripts can disagree on nested excluded dirs.
**Recommendation:** hoist a single shared exclude constant (dirs + suffixes, matched at any depth) used by both scripts. Minor companion code-smell: in `verify_manifest.py`, `manifest_paths` is computed *inside* the `for entry in files:` loop — works only because `files` is guaranteed non-empty earlier. **Proposed new gap G-19.**

### C1-F4 · Repo-placement question — SETTLED ENOUGH TO RECOMMEND (Chunk 1's key deliverable)
`generate_manifest.py` walks the pack **root recursively and hashes everything** except the dev-dir excludes; the live manifest tracks **199 files**, including `.github/workflows/ci.yml`, `.gitignore`, `.gitattributes`, and `CONTRIBUTING.md`. Conclusion: **any file committed to the pack root becomes a governed, hashed asset.** That directly contradicts `SESSION_LOG.md`'s own statement that it "carries no manifest hash."
Therefore the collaboration/build-prep files (`SESSION_LOG.md`, `CHANGELOG.md`, the gap assessment, this audit report) **must not live in the hashed pack root.** Options:
- **(a) separate build/co-design repo** with the pack as a versioned dependency — aligns with the **D-01** recommendation and protects the **D-02** freeze; or
- **(b)** a dedicated top-level directory added to **both** scripts' exclude sets.
**Recommend (a).** Current state is clean: none of the collaboration files are in the repo or manifest yet, so no remediation is needed — only a forward decision. Directly informs **D-01** and **D-09**.

### C1-F5 · D-04 (runtime stack) — CONFIRMED
`requirements.txt` = `pyyaml>=6.0`, `jsonschema>=4.0`. Confirms **Python + JSON Schema** validation engine as the de-facto stack. (Exact JSON Schema draft to confirm in Chunk 3 when schemas are read.)

### C1-F6 · Live integrity — PASS
`verify_manifest.py` run from the pack root: **199/199 files verified and match manifest.** The pack at HEAD is internally consistent; the manifest is current (`created_at_utc 2026-06-13`).

### C1-F7 · NEW / TO VERIFY — a "mode" field already exists in the pack (touches G-16)
A01 §6.2's canonical action envelope carries **`"mode": "M1|M2"`**, i.e. the pack already encodes operating modes at the contract/envelope level. The gap assessment **G-16** states the pack has *no* concept of user-commanded operating modes — that is now **in tension**. It is unknown whether the pack's M1/M2 semantics match the co-design's **M1 Advisory / M2 Execution Planning / M3 Implementation / M4 Project** model. The session-2 mode model may **partially overlap or conflict** with an existing pack mode concept rather than being clean greenfield.
**Action:** confirm pack mode semantics in **Chunk 2** (A04.1 orchestration) and **Chunk 4** (A09 governance, A10 security/mode restrictions) before treating G-16 as a pure DESIGN item. Tag: **NEW (TO VERIFY)**.

### Chunk 1 — gap-assessment deltas (for v0.3)
- **G-12** TO VERIFY → **CONFIRMED** (CI runs smoke test only; no manifest/schema gate). One residual pending Chunk 3.
- **G-01** reinforced CONFIRMED (no runtime content in A00/A01).
- **D-04** recommendation **CONFIRMED** by `requirements.txt`.
- **D-01 / D-09** now backed by concrete evidence (recursive root hashing) → recommend separate build repo / non-hashed location for collaboration files.
- **NEW G-19** (proposed): unify generator/verifier exclude logic; fix verifier loop-scope smell.
- **G-16** flagged for re-examination: pack already carries an `M1|M2` mode field — verify semantics vs the 4-mode design before treating as greenfield.

---

## Chunk 2 — Core Engine Specs

**Read this chunk:** `A04_1_Orchestration`, `A04_2_WorkPackage`, `A04_4_Planning`, `A04_5_DocumentFactory`, `A04_6_Reporting_Export`. (No `A04_3` exists; see C2-F7.) Plus a cross-pack grep for dangling A04.3 references.

**Headline:** the engine specs are **implementation-ready**, not just conceptual. Every subsystem ships concrete entities, required fields, lifecycle state machines, named contract actions, canonical request/response envelopes, error taxonomies with subcodes, and an explicit determinism clause. On the buildability axis the pack is in far better shape than a partial read suggested — the real blockers are the *additive co-design items* (runtime spec, BUILD mode, mode reconciliation), not defects in the engine design.

### C2-F1 · MODE COLLISION — CONFIRMED (escalation of C1-F7) — highest-priority finding
The pack's modes and the co-design's modes **share the labels M1/M2 but mean different things**, and the arities differ (pack = 2 modes, co-design = 4). A04.1 §3.1 defines:
- **Pack M1 = Architecture/Design Mode** — define specs, contracts, assets; *no* commitments to WP truth.
- **Pack M2 = Execution/Implementation Mode** — create/stage/commit WPs, plan, apply, export.

The co-design model is **M1 Advisory / M2 Execution Planning / M3 Implementation / M4 Project Container**. Mapping them exposes the conflict:

| Label | Pack meaning (A04.1) | Co-design meaning (gap assessment) | Collision |
|---|---|---|---|
| **M1** | Architecture/Design (author specs & assets) | Advisory chat / mock-ups, no governed output | **Different concept** |
| **M2** | Execution/Implementation (stage/commit/plan/apply/export) | Execution *Planning* (Valor work structure, **not** a CQV plan) | **Different concept** — pack M2 ≈ co-design **M3** |
| **M3** | — (does not exist) | Implementation (governed, gated) | Pack has no M3 |
| **M4** | — (does not exist) | Project Container | Pack has no M4 |

The mode field is **live in the contract envelope** (`"mode": "M1|M2"` in A01 §6.2 and every A04.x example) and **enforced** (`MODE_VIOLATION` appears in WP §10, Planning §14, DOC §9). So **G-16 is not greenfield** — the co-design's 4-mode model would overload an existing, enforced 2-mode field with conflicting semantics. This *must* be reconciled before the mode model is built.
**Recommendation:** the co-design should **rename its modes** (or explicitly re-map them onto the pack's design/execution axis) to avoid silently redefining `M1`/`M2`. Cleanest option: treat the pack's M1/M2 as the *governance axis* (design-time vs execution-time truth mutation) and give the co-design's advisory/planning/implementation/project concepts **distinct names**. Carry the final reconciliation to Chunk 4 (A09 governance, A10 security/mode restrictions) to confirm no further mode semantics exist. **G-16: DESIGN → DESIGN (CONFLICT CONFIRMED), reframed as a reconciliation task, not a net-new capability.**

### C2-F2 · G-04 (walking skeleton) — TO VERIFY → CONFIRMED (at spec level)
The end-to-end reference flow is fully specified across the chunk: A04.1 §4 gates (**Stage → Commit → Plan → Apply → Export**) and §8 state machine (S0–S6); A04.2 §8 apply boundary; A04.4 §12 apply sequence naming `PLAN_GENERATE_PROPOSAL` + `WP_APPLY_PLAN_PROPOSAL`; A04.5 §7 generation pipeline (Resolve → Validate Source Chain → Assemble → Validate Completeness → Render → Finalize) with `DOC_GENERATE_DRAFT`/`DOC_FINALIZE_ARTIFACT`; A04.6 §9 `RPT_GENERATE_*`. These action names match real files in `action_blocks/`. So the slice (stage → commit → generate → stamp → export) is **designed and catalogued**; the "walking skeleton" is now a *build milestone proving the path runs*, not a missing design. **Recommended first slice:** `VALOR-contract-orch-wp` stage→commit, since it is the truth-owning root every other path depends on.

### C2-F3 · G-06 (WP persistence) — TO VERIFY → CONFIRMED (logical model complete; physical store deliberately open)
A04.2 fully specifies the *logical* truth model: required WP/Task fields, two lifecycle state machines, deterministic ID allocation with an **append-only ID ledger (or equivalent) + tombstoning** (§4), mutability rules, and provenance refs. It does **not** name a physical store — and that is now clearly *by design*, not an oversight: §4 mandates persistence *properties* (append-only, non-reuse, tombstone, immutable IDs) and leaves the *medium* to implementation. This sharpens **D-03**: whatever store is chosen (the recommendation is file/git) **must support an append-only ledger and tombstoning** — a plain mutable file store would violate §4. Gap converts to CONFIRMED with the physical-store decision routed to D-03 under that constraint.

### C2-F4 · G-13 (determinism) — TO VERIFY → CLOSED at the pack level
Determinism is stated **explicitly and repeatedly**: Planning §15 (same inputs → reproducible; any change → new `plan_id`), DOC §7.2 (same inputs → same content + checksum), RPT §13 (same inputs → same artifact + new snapshot hash on change), WP §4 (deterministic IDs). Critically, **the pack describes no AI/LLM component at all** — orchestration is pure deterministic intent→contract routing (A04.1 §3.3). This confirms the 3-layer model's mapping: **the pack *is* Layer 1 (the deterministic engine)**, and the AI layer is entirely additive/external. G-13's residual ("make the AI *call* reproducible") therefore lives **outside the pack** and is properly a **D-08** concern (versioned prompts, fixed settings, refuse/accept contract). **Closed for the pack; residual reassigned to D-08.**

### C2-F5 · G-08 (approval/signature event) — leaning CONFIRMED, final pending A09
A04.2 models `APPROVAL` as a task_type and A01 §4.2 places signatures outside Valor (human-owned). But no subsystem in this chunk models the *signature/approval event* as an integration interface. The gap stands; final confirmation deferred to **A09 Governance/Branching (approvals/audit trail)** in Chunk 4.

### C2-F6 · Project container (G-18 / D-11) — reinforced by existing precedent
A04.6 already defines **`SELECTED_WP_SET`** — a multi-WP, **projection-only** target scope that "must never correct, overwrite, infer, or silently mutate WP/task truth" (§1, INV-09). This is a concrete in-pack precedent for the D-11 recommendation that the **M4 Project container be projection/reference-only "like Reporting."** Design constraint surfaced: A04.6 puts **`ALL_WPS` out of freeze scope** — so an M4 container must compose *explicitly selected* WPs (SELECTED_WP_SET semantics), never imply an all-WP rollup. Strengthens D-10/D-11; the container is additive and has a pattern to copy.

### C2-F7 · `A04_3` — benign numbering gap (not a defect)
The canonical index (A00) skips A04_3, and a cross-pack grep finds **zero** references to A04.3/A04_3/A04-3. It is an intentional numbering gap, not a missing file or dangling dependency. No action.

### C2-F8 · Carried to Chunk 4 (standards governance)
Two items surfaced here that belong to the standards audit: (1) the base bundle **`BND-CQV-BASE_v1.0.1` is `TESTING_ONLY` / `PRODUCT_TESTING_ONLY`** in this scope — regulated output is *blocked* (DOC §3.2, envelope examples), which directly frames **G-10**; (2) the **`NO_EXCERPTS` / METADATA_ONLY / INTERNAL_ONLY** citation policy is enforced in DOC §3.5, matching the S1 standards discipline and framing **G-11** (anchors). DCF artifact generation/finalization is **inactive** in current scope.

### Chunk 2 — gap-assessment deltas (for v0.3)
- **G-04** TO VERIFY → **CONFIRMED** (reference flow fully specified + catalogued; build slice = first milestone; suggest orch-wp stage/commit).
- **G-06** TO VERIFY → **CONFIRMED** (logical model complete; physical store open via D-03, *constrained* by append-only ledger + tombstoning).
- **G-13** TO VERIFY → **CLOSED at pack** (determinism explicit across Planning/DOC/RPT/WP; no AI in pack; residual → D-08).
- **G-08** leaning **CONFIRMED**, final pending A09 (Chunk 4).
- **G-16** reframed: **CONFLICT CONFIRMED** — pack already enforces M1/M2 with different meaning; co-design must rename/re-map modes, not invent over them.
- **G-18 / D-10 / D-11** reinforced: `SELECTED_WP_SET` is an existing projection-only multi-WP precedent; M4 must avoid `ALL_WPS` (out of freeze scope).
- Carried to Chunk 4: **G-10** (base bundle is TESTING_ONLY), **G-11** (NO_EXCERPTS anchors).

---

## Chunk 3 — Contracts & Schemas

**Read this chunk:** `CONTRACT_REGISTRY_v1.0.1.yaml`, all 7 contract bodies, the 51 schema files under `schemas/`, the 31 test vectors under `test_vectors/`, and `smoke_test.py`. Executed live: the smoke test, a registry↔contract↔schema↔action_block alignment check, schema meta-validation, and ref-resolved validation of the single-instance vectors.

**Headline (G-05 verdict):** the **contract and schema *definitions* are complete and internally consistent** — buildable on both sides. But the **test/validation tooling enforces only a thin slice** of the rich vector corpus the pack ships. Definitions are freeze-quality; enforcement is not. That split is the real story of this chunk.

### C3-F1 · G-05 (contract completeness) — TO VERIFY → CONFIRMED (complete)
Verified programmatically, not by eyeball:
- **Registry self-consistency:** every contract `file:`, every action `schema:`, and every non-null action `block:` reference **resolves** — zero missing.
- **Registry ↔ contract-body alignment:** all 7 contracts match their bodies exactly — **39 actions, zero mismatches** (wp 7, wp-user-driven 3, plan 2, doc 2, rpt 9, ks 12, ps 4). The Blocker-1/Blocker-5 alignment work appears genuinely complete.
- **Contract bodies are complete:** each carries envelopes (request/response schema), SemVer compatibility policy, stamp policy, an error taxonomy (standard codes + subsystem subcodes), and per-action `allowed_modes`, `side_effect_class`, `idempotent`, `confirmation_required`, required/optional payload fields, target fields, `result_schema_ref`, and `validation_rules`. This is exactly the "envelopes/actions/errors/validation" G-05 asked for.
- **Schemas valid:** all **51** schema files parse and **meta-validate as JSON Schema draft-07**.
- **Single-instance vectors validate:** with refs resolved, `expected_committed_wp`, `seed_wp`, `expected_doc_metadata`, `expected_staged_tasks`, `expected_plan_proposal`, and both `expected_report_*` vectors validate cleanly against their schemas. (The one apparent failure, `expected_export.json`, was a *mis-pairing on my part* — it is a scenario/declaration vector, not a single instance; not a pack defect.)
**Conclusion:** contracts are complete enough to build both sides against. **G-05 CONFIRMED.**

### C3-F2 · D-04 (runtime stack) — CONFIRMED definitively
Every one of the 51 schemas declares `http://json-schema.org/draft-07/schema#`. The D-04 recommendation ("JSON Schema draft-07 in use") is now proven across the whole schema set, not assumed.

### C3-F3 · NEW — validation tooling under-enforces the contract corpus (proposed G-20)
The pack ships a **rich 31-file vector corpus**: single-instance expectations, positive/negative case suites (`ks_*`, `negative/`), full e2e flows (positive + gate-failure), and governance/registry/security suites — several of which **declare their own `schema_ref`(s)** internally, signalling they were meant to be validated. But `smoke_test.py` (the only thing CI runs) exercises **only**: manifest verify + a schema **parse** check + **2** `expected_report_*` vectors + preset-binding resolution. So **~29 of 31 vectors are inert** — present and well-structured, but executed by no harness. Three concrete sub-issues:
- **(a) ~29 vectors unexercised** — the negative/e2e/ks/governance/registry/security suites never run in CI. The material for real contract testing exists; the harness to run it does not (consistent with "no engine built yet").
- **(b) schema-parse coverage hole** — `validate_all_json_schemas` globs `*.schema.json`, which **misses the 12 `schemas/objects/*_schema.json` files** (naming inconsistency: `contracts/`+`documents/` use `.schema.json`; `objects/` use `_schema.json`). Ironically those include the most-referenced result schemas (`work_package_schema.json`, `rpt_artifact_metadata_schema.json`). They are valid — my own pass meta-validated them — but the smoke test never looks.
- **(c) cross-file `$ref` resolution is only stubbed** — `work_package_schema.json → task_schema.json` and `report_result → ../objects/rpt_artifact_metadata` are relative file refs; `smoke_test.py` hand-inlines **one** of them and notes the deprecated RefResolver was failing. Any builder validating instances must stand up a proper ref registry; the current tooling doesn't.
**Recommendation:** build the vector-driven test harness (run all suites, validate cases against their declared `schema_ref`s, assert expected pass/fail), normalise schema filenames (or widen the glob to `*_schema.json` too), and configure a real `$ref` registry. **Proposed new gap G-20.**

### C3-F4 · CORRECTION to C1-F2 (CI / manifest gating)
Chunk 1 stated CI "does **not** gate manifest integrity." **`smoke_test.py` overturns that:** its default first check is `verify_manifest`, which compares **sha256 + byte size** of every tracked file, so CI **does** catch modification or deletion of tracked files. The accurate, narrower statement: **CI gates manifest integrity for tracked files, but has no extra-file (injection) detection** — only the standalone `verify_manifest.py` detects extras, and that script carries the exclude-divergence bug (G-19). So an *added* untracked file passes CI. **G-12 final:** CONFIRMED with precise scope — CI verifies manifest (tracked-file hash/size) + schema-parse (with the C3-F3b hole) + 2 report vectors + preset bindings; it does **not** run the full vector suite, validate non-report instances, or detect extras. Recommendation: after fixing G-19, wire the standalone `verify_manifest.py` (extras detection) and the G-20 harness into CI.

### C3-F5 · NEW — the pack is *pre-freeze*, not frozen (correction for D-02)
The registry status is `pre_freeze_controlled` (matching every A04.x block) and it **explicitly retains freeze blockers**: *"Manifest regeneration and final freeze-readiness check remain blocked until all pre-freeze content edits are complete."* The build-prep CHANGELOG describes the pack as "frozen pending D-02 (`v1.0.1`, frozen)." That framing is **slightly inaccurate** — v1.0.1 is a controlled *pre-freeze* state, not a completed freeze. This doesn't change the D-02 recommendation (freeze before building) but sharpens it: **D-02 is partly the pack's own open task**, not just a co-design policy choice. The co-design docs should stop calling v1.0.1 "frozen."

### C3-F6 · KS contract is TESTING_ONLY (reinforces G-10, for Chunk 4)
`VALOR-contract-orch-ks` is registered `TESTING_ONLY_PRE_FREEZE_WITH_REGULATED_USE_BLOCK`: `regulated_output_allowed: false`, `testing_only_stamp_required: true`. Its 12 KS actions resolve standards/templates/bundles/anchors/citations for **product testing only**. This is the contract-level confirmation of C2-F8 and frames the **G-10/G-11** standards audit in Chunk 4 (the KS schemas — `ks_external_references`, `ks_source_mapping`, `ks_anchors_list` — are where the real-anchor scheme for G-11 will be checked).

### Chunk 3 — gap-assessment deltas (for v0.3)
- **G-05** TO VERIFY → **CONFIRMED (complete)** — definitions consistent and buildable; verified by alignment + schema + vector checks.
- **G-12** → **CONFIRMED (precise scope)** — CI verifies manifest (tracked-file hash/size) + schema-parse + 2 report vectors + preset bindings; no full-suite/instance/extras enforcement.
- **D-04** → **CONFIRMED definitively** (all 51 schemas draft-07).
- **NEW G-20** (proposed) — validation tooling under-enforces the corpus: ~29 vectors inert; objects `_schema.json` outside the parse glob; cross-file `$ref` only stubbed. Build the harness; normalise schema naming; configure a ref registry.
- **NEW (D-02 correction)** — pack is `pre_freeze_controlled`, not frozen; registry retains freeze blockers. Stop describing v1.0.1 as "frozen."
- **C1-F2 corrected** (see C3-F4): CI *does* verify the manifest; the residual is extras-detection + broad enforcement.
- Carried to Chunk 4: **G-10/G-11** (KS TESTING_ONLY; anchor scheme lives in KS schemas + `libraries/knowledge_standards`).

---

## Chunk 4 — Remaining Specs & Existing Standards

**Read this chunk:** `STD-CQV-BASE` (16 requirements), the external-reference register, `BND-CQV-BASE` + the two add-on bundle heads, A09 (Governance/Branching) and A10 (Security/Compliance) in full, plus a coverage sweep of A05–A08, A11, A13, and the full A14 invariant index. This closes the last open gaps (G-07, G-08, G-10, G-11) and confirms the mode finding.

### C4-F1 · G-10 (do the seven drafted standards duplicate existing content?) — CONFIRMED: significant overlap; do NOT add them as separate standards
The pack's standards architecture is **one** internal standard plus **trigger-composed bundles**, not seven parallel standards:
- **`STD-CQV-BASE`** — 16 governed requirements (CQV-REQ-001…016): lifecycle, URS, risk, RTM/traceability, DQ/IQ/OQ/PQ, VSR, FAT/SAT, **CSV trigger (011)**, **Cleanroom/HVAC trigger (012)**, documentation control, approval expectations, reporting, and the missing/expired blocked-state rule.
- **3 bundles** — `BND-CQV-BASE` (includes STD-CQV-BASE + 6 external refs + 8 templates) plus `BND-CSV-ADDON` and `BND-CLEANROOM-ADDON`, pulled in by conditional triggers (`TRG-CSV-ADDON`, `TRG-CLEANROOM-ADDON`).

Mapping the seven drafts onto this: **STD-CQV-MGT** ≈ the base lifecycle/management requirements; **STD-CSV-CQ** and **STD-CLEANROOM-CQ** duplicate the existing CSV/Cleanroom **add-on bundle** mechanism + REQ-011/012 triggers; the equipment-domain ones (**PEQ/CUTIL/BUTIL/CAL**) have **no separate-standard counterpart** — the pack handles equipment/domain specificity through **task pools / profiles / presets** (e.g. `TP-PE-HIGH`, `PROF-PE-HIGH`, `PS-PE-HIGH`), not standards.
**Recommendation:** do not integrate the seven as parallel `STD-*` files. Fold any genuinely new governed requirements into `STD-CQV-BASE` as additional `CQV-REQ-###` entries, route cleanroom/CSV through the existing add-on bundles, and keep domain specificity in the task-pool/profile/preset layer. This **confirms D-05** ("base = sections; cleanroom & CSV = add-ons") and sharpens it: the add-ons already exist as bundles, so little or nothing new is needed there. **G-10 CONFIRMED.**

### C4-F2 · G-11 (real anchor scheme) — CONFIRMED
The register `EXT-REFS-VALOR-KS-v1.0.1` defines the real scheme: **source IDs `EXT-<SOURCE>`** (10 sources: ISPE-BG5, ISPE-GAMP5, EUGMP-ANNEX15, EUGMP-ANNEX11, ASTM-E2500, ICH-Q9, ICH-Q10, 21CFR11, ISO14644, LOCAL-EDA-SITE-GMP) and **TOPIC anchors `EXT-<SOURCE>-<TOPIC>`** (e.g. `EXT-EUGMP-ANNEX15-QUALIFICATION-VALIDATION`). All sources are `TESTING_ONLY`, `excerpt_policy: NO_EXCERPTS`, with edition/date held as `TESTING_PLACEHOLDER_NOT_APPROVED` and explicit `control_rules` forbidding invented clause numbers/editions/dates. The co-design's placeholder anchors (`SRC-ANX15…`) must be remapped to this scheme (e.g. → `EXT-EUGMP-ANNEX15-*`). **Confirms D-06** (adopt the existing register scheme; never invent a parallel one). **G-11 CONFIRMED.**

### C4-F3 · G-08 (approval/signature event) — TO VERIFY → CONFIRMED (modeled; integration point named)
A09 §6 defines an explicit **Approval Model**: approvals are **governance records, not signatures** — categories `APPROVE_STAGE_TO_COMMIT / PLAN_APPLY / DOC_FINALIZE / EXPORT / WP_CLOSE`. §3.2 specifies mandatory human-confirmation capture (`confirmation_id`, `confirmer_role`, `timestamp_utc`, scope, staged-object hash). §7 defines an **append-only, hash-chained audit trail** (EVT_* events incl. `EVT_OVERRIDE_ACCEPTED`). §6.2 states the system stores who approved but "does not validate real-world authority unless integrated with identity systems." So the approval *event* and its capture **are** modeled; only external e-signature execution is (correctly) out of scope. **G-08 CONFIRMED — effectively closed at the architecture level**; the build implements confirmation/approval records + audit events, with the identity/e-sign integration point named.

### C4-F4 · G-07 (identity/authorization) — TO VERIFY → CONFIRMED (deferral explicit; stub + integration point already specified)
A10 §3.2 states identity/authorization is "**not cryptographically verified in v0.1.x**." §7 defines **soft controls** as the stub: declared role context, mandatory confirmations, and role logged in audit events, with a warn-and-acknowledge path when an action is inconsistent with the declared role. The integration point (identity systems for real authority validation) is named in A10 §7 + A09 §6.2. This is exactly G-07's proposal ("stub identity boundary + integrate at X note") — **already satisfied by the pack**. **G-07 CONFIRMED — closed at the architecture level.**

### C4-F5 · Mode collision (C2-F1) — FINAL confirmation
A09 and A10 both use only **M1/M2** (`MODE_VIOLATION / WRONG_MODE_FOR_COMMIT`); no `M3`/`M4` appears anywhere in the pack. The pack's M1 (design) / M2 (execution) axis is consistent across A01, A04.1/.2/.4/.5, A09, A10 and the contract bodies. The co-design's 4-mode model therefore *must* be renamed/re-mapped, not built over the existing field. C2-F1 stands, fully confirmed across the whole pack.

### C4-F6 · Coverage notes (A05–A08, A11, A13, A14)
- **Single worked-example domain.** The libraries ship exactly one instance each: `TP-PE-HIGH`, `PROF-PE-HIGH`, `PS-PE-HIGH`, `CAL-WORKWEEK`. The architecture is general, but the only end-to-end-exercisable domain today is **Process Equipment / High complexity**. The walking-skeleton slice (G-04) can only run against PE-HIGH; other domains have no governed pool/profile/preset yet. Not a defect (reasonable for pre-freeze), but the build plan should know the live test surface is one domain.
- **Invariant set complete.** A14 indexes **INV-01…INV-10** (defined in A02), consistently cross-referenced across A04.x/A06/A08/A09. A regenerate-and-check tool for the INV index (like the manifest) would be a good build-time guard.
- **Mixed freeze status.** A00/A01/A09/A10/A11/A13(checklist)/A14 are `released`; A04.x and A05–A08 are `pre_freeze_controlled` — reinforcing C3-F5 (the pack is mid-freeze, not uniformly frozen).
- **Minor cross-file inconsistency (NEW, low severity):** A10 §6.4 lists excerpt policies as `METADATA_ONLY / PUBLIC_EXCERPT / INTERNAL_ONLY`, but the actual register uses `NO_EXCERPTS` (every source) and the DOC CitationSet enum (A04.5 §3.5) is `METADATA_ONLY / INTERNAL_ONLY / NO_EXCERPTS`. `PUBLIC_EXCERPT` appears only in A10 and is never used. Recommend aligning A10's vocabulary to the register/DOC model (drop or reconcile `PUBLIC_EXCERPT`).

### Chunk 4 — gap-assessment deltas (for v0.3)
- **G-07** TO VERIFY → **CONFIRMED (closed)** — identity deferral explicit; soft-control stub + integration point already in A10.
- **G-08** TO VERIFY → **CONFIRMED (closed)** — approval records + confirmation capture + audit events modeled (A09); e-sign external.
- **G-10** → **CONFIRMED** — seven drafts overlap STD-CQV-BASE + add-on bundles; do not add as separate standards; **D-05 confirmed**.
- **G-11** → **CONFIRMED** — real scheme `EXT-<SOURCE>` / `EXT-<SOURCE>-<TOPIC>`; remap placeholders; **D-06 confirmed**.
- **G-16 / C2-F1** → mode collision confirmed pack-wide; co-design must rename modes.
- **NEW (low severity):** A10 excerpt-policy vocabulary (`PUBLIC_EXCERPT`) drifts from register/DOC; align.
- Coverage note: single worked-example domain (PE-HIGH); INV-01–10 complete; pack mid-freeze.

---

## Consolidated Build-Readiness Verdict

### Bottom line
**The Valor Architecture Pack is design-complete and internally consistent on its core — and it is not yet buildable as-is, because the buildability scaffolding is deliberately absent and a few additive reconciliations remain.** None of the blockers are defects in the architecture; they are the missing *build layer* the gap assessment set out to define. The audit converts the partial-read picture into a confirmed one: **the pack is a sound, deterministic Layer-1 engine spec; what's missing lives around it, not inside it.**

### What's strong (confirmed, not assumed)
- **Governance & determinism.** Pure deterministic engine, no AI inside the pack; explicit determinism clauses in Planning/DOC/RPT/WP; 10 invariants (INV-01–10) cross-referenced and indexed; append-only audit trail with hash-chaining; fail-closed safe-output policy.
- **Contracts & schemas (G-05).** Registry ↔ 7 contract bodies ↔ 51 draft-07 schemas ↔ action_blocks all align (39 actions, zero mismatches); single-instance vectors validate. Buildable on both sides.
- **End-to-end path (G-04).** The full stage→commit→plan→apply→generate→stamp→export flow is specified and catalogued with real action names.
- **Truth model & persistence properties (G-06).** WP truth model complete; append-only ID ledger + tombstoning mandated.
- **Identity & approvals (G-07/G-08).** Deferral explicit, soft-control stub + integration point named; approval events modeled as records + audit.
- **Standards governance (G-10/G-11).** One base standard + trigger-composed bundles + a 10-source `EXT-*` register with strict NO_EXCERPTS discipline.

### What blocks the build (all additive, none are pack defects)
1. **No runtime/target spec (G-01)** — biggest buildability gap; write A16 around the 3-layer stack.
2. **No BUILD mode (G-02)** — gates are mandatory; needs a log-only dormant build mode (D-07).
3. **Mode-name collision (G-16/C2-F1)** — co-design's M1–M4 conflict with the pack's enforced M1/M2; rename/re-map before building the mode model.
4. **Test/CI under-enforcement (G-20, NEW)** — ~29 of 31 vectors inert; objects `_schema.json` outside the smoke-test glob; cross-file `$ref` only stubbed; CI has no extras-detection. Build the vector harness; wire `verify_manifest.py` (post-G-19 fix) into CI.
5. **Integrity-tooling bug (G-19, NEW)** — generator/verifier exclude-set divergence produces false FAILs; unify the exclude logic.
6. **Repo placement (D-01/D-09)** — the manifest hashes the whole root recursively, so collaboration files must live outside the hashed pack (separate build repo recommended).
7. **Freeze reality (D-02 / C3-F5)** — the pack is `pre_freeze_controlled` with retained freeze blockers, not "frozen"; finish the freeze (partly the pack's own open task) before building against it.

### Cross-file issues surfaced
- Pack M1/M2 vs co-design M1/M2/M3/M4 (semantic + arity collision) — **must reconcile**.
- Generator vs verifier exclude divergence (G-19).
- Schema filename inconsistency (`.schema.json` vs `_schema.json`) creating a smoke-test coverage hole (G-20b).
- Excerpt-policy vocabulary drift (A10 `PUBLIC_EXCERPT` vs register/DOC `NO_EXCERPTS`) — low severity.
- Gate-naming granularity differs slightly between A04.1 (Stage/Commit/Plan/Apply/Export) and A09 (Stage/Validate/Commit/Apply/Finalize/Close) — consistent, but worth a single canonical statement.

### TO-VERIFY → final status (all resolved)
| Gap | Before | After |
|---|---|---|
| G-04 walking skeleton | TO VERIFY | **CONFIRMED** (path specified/catalogued) |
| G-05 contract completeness | TO VERIFY | **CONFIRMED (complete)** |
| G-06 WP persistence | TO VERIFY | **CONFIRMED** (logical complete; store via D-03 under append-only/tombstone) |
| G-08 approval event | TO VERIFY | **CONFIRMED (closed)** |
| G-12 CI purpose | TO VERIFY | **CONFIRMED (precise scope)** |
| G-13 determinism | TO VERIFY | **CLOSED at pack** (residual → D-08) |
| G-07 identity | CONFIRMED (proposal) | **CONFIRMED (closed — stub already in pack)** |
| G-10 standards overlap | CONFIRMED | **CONFIRMED (do not add 7)** |
| G-11 anchor scheme | CONFIRMED | **CONFIRMED (EXT-* scheme)** |

### New gaps proposed
- **G-19** — unify manifest generator/verifier exclude logic; fix verifier loop-scope smell.
- **G-20** — build the vector-driven test harness; normalise schema filenames / widen the glob; configure a `$ref` registry; wire extras-detection into CI.

### Decisions touched
- **D-04** CONFIRMED definitively (Python + JSON Schema draft-07).
- **D-05** CONFIRMED (base = sections; cleanroom/CSV already add-on bundles).
- **D-06** CONFIRMED (adopt `EXT-*` register scheme).
- **D-01 / D-09** evidence-backed → separate build repo / non-hashed location for collaboration files.
- **D-02** sharpened/corrected → pack is pre-freeze, not frozen; finishing the freeze is partly the pack's own task.
- **D-03** constrained → store must support append-only ledger + tombstoning.
- **D-08** confirmed as the home for AI-call reproducibility (pack has no AI layer).
- **D-10 / D-11** reinforced → `SELECTED_WP_SET` is an existing projection-only precedent for the M4 container; avoid `ALL_WPS`.

### Recommended next actions
1. Amend the gap assessment to **v0.3**: flip every TO VERIFY per the table above, add **G-19** and **G-20**, record the **D-02** correction, and the mode-rename action under G-16.
2. Update `SESSION_LOG.md` (Session 3) and `CHANGELOG.md` (`build-prep-0.3`).
3. Decide repo placement (D-01) and the mode-naming reconciliation (G-16) — the two decisions that unblock the most downstream work.
4. Then proceed in the gap assessment's recommended order: BUILD mode (G-02) → runtime spec A16 (G-01) → walking skeleton (G-04, against the PE-HIGH worked example) → standards reconciliation (G-10/G-11) last.

*Audit complete. No repo commits or build work performed, per the audit charter.*
