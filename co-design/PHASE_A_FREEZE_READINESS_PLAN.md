# Phase A — Pack → Freeze-Readiness Plan

*Part of VALOR phasing — see `BUILD_STRATEGY.md` §0.*

**Status:** ✅ COMPLETE · **Updated:** 2026-06-18 · **Author:** co-design (Mervat)
**Baseline:** Gap Assessment v0.3 + Audit Report v1.0 (decisions FINALIZED 2026-06-16, owner: Amr)
**Charter:** *We edit the pre-freeze pack; owner (Amr; Nexus = Amr) commits and runs the freeze.* Freeze-readiness was **Phase A of the build**, not an external dependency (D-02 / G-14).

> **Outcome:** **A1 ✅ · A2 ✅ · A3 ✅ · A4 ✅ · A5 ✅.** Pack **frozen at v1.0.1**, HEAD **`0ec3060`** (was `78c40d7`); registry `status: frozen_controlled`. Fresh-clone gates all PASS (**verify 173 / smoke / harness**). "Frozen" is now accurate. **→ Phase B begins** (see `PHASE_B_BUILD_WORKFLOW_PLAN.md`, B1).

> **Scope boundary.** Phase A touched only the architecture pack (`Cyber-Mario1979/VALOR_Architecture_Pack`). No build-layer work, no separate repo, no AI/UI. Those are Phase B. Phase A ended when the owner froze **v1.0.1**.

---

## Standing discipline for every Phase-A edit (held throughout — non-negotiable)

- **LF only.** Pack-editing tools must write **LF** (`write_bytes`, not text-mode writes; Windows converts `\n`→`\r\n`). `.gitattributes` enforces `eol=lf`.
- **Regenerate the manifest from a fresh, clean LF clone** after any edit — never from a working tree a tool may have touched.
- **Trust the fresh-clone verify, not the local one.** Local can pass while the committed (normalized) state is broken; the committed state is what CI sees.
- **Build tools stay out of the hashed pack.** Move `apply*.py` / one-shot installers out of the pack root before `git add` / regen (D-01).
- **Never commit/push a non-PASS verify.**

> This discipline earned its keep right up to the freeze: A5 hit the same R1 CRLF gremlin again (13 untouched files), and the fresh-clone-verify rule is what caught it before it shipped.

---

## Why this phase existed

The pack was **design-complete and internally consistent on its core, but not frozen** — the registry was `pre_freeze_controlled` and *retained freeze blockers* ("manifest regeneration and final freeze-readiness check remain blocked until all pre-freeze content edits are complete"). Phase A cleared the remaining pre-freeze edits and tooling defects so the owner could run a clean freeze. None of the work was an architecture defect — it was the last mile to a frozen, buildable baseline.

---

## Work items

### A1 — Mode rename: `M1`/`M2` → `DESIGN`/`EXECUTION` (G-16) — ✅ DONE
The hard blocker. Mechanical, word-boundary relabel of the engine-authority mode **values**, freeing `M1–M4` for the Phase-B runtime layer.
- **Done:** renamed across 26 files (7 contracts, 2 schemas, 12 action_blocks, 4 docs, 1 registry vector); 100 token replacements. Word-boundary only — `MODE_VIOLATION` / `WRONG_MODE_FOR_COMMIT` and the blueprint PNG untouched.
- **Validated:** 0 residual `M1`/`M2`; 51 schemas meta-validate draft-07; smoke `schemas.load` / `report.vectors` / `presets.bindings` PASS.
- Tooling: `apply.py` (one-shot, self-excluding, LF-safe), kept out of the pack.

### A2 — Unify integrity tooling (G-19) — ✅ DONE
`generate_manifest.py` and `verify_manifest.py` used divergent ignore rules → false "extra files" FAILs after routine local testing.
- **Done:** added shared `scripts/pack_validation/pack_excludes.py` (dirs + suffixes, any-depth), imported by both scripts; verifier's `manifest_paths` loop-invariant hoisted out of the per-entry loop; verifier extras-detection aligned to the shared rule.
- **Validated:** fresh-clone `verify_manifest.py` = PASS 200; regression confirmed — a stray `.pytest_cache/` + `.pyc` no longer false-FAIL.
- Tooling: `apply_a2.py` (installer, surgical patches, self-verifying, LF-safe), kept out of the pack.

### A3 — Vector/CI harness + CI wiring (G-12 + G-20) — ✅ DONE
CI ran `smoke_test.py` only: manifest verify + schema **parse** + **2** report vectors + preset bindings. ~29 of 31 vectors were inert; the parse glob missed `objects/*_schema.json`; cross-file `$ref` was only stubbed; no extras-detection.
- **Done:** stood up the **vector-driven harness** (runs all suites, validates each case against its declared `schema_ref`, asserts expected pass/fail); schema-coverage hole closed (objects `_schema.json` now covered); real **`$ref` registry** in place of the hand-inlined single ref; CI wired with `verify_manifest.py` (extras-detection, post-A2) **plus** the new harness.
- **Validated:** fresh-clone CI green — **verify / smoke / harness all PASS**; manifest **200 → 201** (the harness is the one added governed file).
- **Known limit (recorded, accepted for pre-freeze):** only end-to-end-exercisable domain is **PE-HIGH** (`TP/PROF/PS-PE-HIGH`); the harness fully runs one domain today.
- Harness is *pack* tooling (lives under `scripts/`); one-shot installers stayed out of the pack.

### A4 — Standards/anchor reconciliation + `PUBLIC_EXCERPT` cleanup (G-10 / G-11 · D-05 / D-06) — ✅ DONE
- **G-10 / G-11 were confirm-only — no fold/remap needed.** The seven drafted standards and the `SRC-ANX…` placeholders were co-design working drafts that **were never committed to the pack**, so there was nothing to remove or remap. The pack already holds exactly one base standard (`STD-CQV-BASE`, 16 reqs `CQV-REQ-001…016`), all three bundles (`BND-CQV-BASE`, `BND-CSV-ADDON`, `BND-CLEANROOM-ADDON`), and a pure `EXT-<SOURCE>` / `EXT-<SOURCE>-<TOPIC>` register + mapping. Confirmed clean; `NO_EXCERPTS` discipline intact.
- **The only A4 pack edits = `PUBLIC_EXCERPT` cleanup, in 2 files** (audit C4-F6 undercounted it as one): `schemas/contracts/ks_citation_resolved.schema.json` enum → `["METADATA_ONLY","INTERNAL_ONLY","NO_EXCERPTS"]`; `A10 §6.4` dropped `PUBLIC_EXCERPT` **and added the missing `NO_EXCERPTS`**. No vector/instance used `PUBLIC_EXCERPT` as a value (grep, pack-wide) — safe.
- **Held the line:** KS **content-approval** lifecycle (`PRE_FREEZE_USER_REVIEW_REQUIRED`, 29 occurrences) left untouched — orthogonal to pack-freeze; sweeping it would misrepresent testing-only content as approved (see Freeze-Status Register §2).
- **Open confirm (carried, non-blocking):** the G-10 "fold any genuinely-new req into `STD-CQV-BASE`" step was never executed — it needs the seven draft texts diffed against the 16 existing reqs. Audit C4-F1 assessed them duplicative and the freeze proceeded treating that as settled (nothing to fold). Owner to confirm, or supply the drafts for a diff.
- **Exit met:** no parallel STD files (none ever existed in the pack); anchors already on `EXT-*`; `PUBLIC_EXCERPT` resolved across both files.

### A5 — Manifest regen + freeze-readiness + **freeze v1.0.1** (owner-run) — ✅ DONE
Regen was blocked until all pre-freeze content edits were complete — so this ran **last**, after A3/A4.
- **Status sweep:** `*_PRE_FREEZE → *_FROZEN` lifecycle suffix; capability prefix preserved; header phase `pre_freeze_controlled / PRE_FREEZE_CONTROLLED → frozen_controlled` (lowercase normalized). **126 replacements across 32 files** (exact whole-token value-map).
- **`_review_control/` retired:** 28 files (stale scaffolding from a prior failed freeze attempt) deleted; `EXCLUDE_DEGOVERNED_DIRS` dropped from `pack_excludes.py`. Recoverable via git history. (Membership unaffected — the dir was degoverned/excluded.)
- **Freeze blocker B removed** (process gate; condition met); **blocker A retained** verbatim (K&S testing-only / regulated-use — a standing scope constraint, not a process gate).
- **Manifest regenerated** (Linux/LF clone): governed membership **201 → 173** (the pre-A5 cleanup de-governed/retired `_review_control/`, 28 files; the A5 sweep itself moved only hashes, not membership); registry `status: frozen_controlled`.
- **CRLF episode (R1, recurred):** owner's local verify FAILed on 13 *untouched* files — CRLF stragglers from a Windows checkout, not content drift. Installer extended to whole-tree LF-normalize (idempotent, self-skipping, default-path). Local then PASS 173.
- **Owner action (Amr):** ran the installer in-repo, dropped the LF manifest, local `verify_manifest` = PASS 173 → `git add -A` → commit → `git tag -a v1.0.1` → push (+tags). **Fresh clone of `0ec3060` (independent):** `frozen_controlled`; blocker B 0 / A 1; residual swept tokens 0; `PRE_FREEZE_USER_REVIEW_REQUIRED` 29; committed `i/crlf` 0; **verify 173 / smoke / harness PASS.**
- **Exit met:** pack frozen at **v1.0.1** (`0ec3060`); manifest current; gates green on a fresh clone.

---

## Dependency order (as executed)

```
A1 ✅ ─┐
A2 ✅ ─┤
A3 ✅ ─┼─> A4 ✅ ──> A5 ✅ (regen → freeze-readiness → FREEZE v1.0.1)  [owner]
       │
(A3/A4 were content+tooling edits; A5 ran LAST — regen was blocked until edits landed)
```

---

## Phase-A exit criteria — all met

1. **G-16:** zero old `M1`/`M2`; `DESIGN`/`EXECUTION` consistent pack-wide. — ✅
2. **G-19:** generator/verifier share one exclude constant; no false-FAIL on routine test artifacts. — ✅
3. **G-12 + G-20:** CI runs the full vector harness + `verify_manifest.py` (extras) + complete schema coverage + `$ref` registry — green on a fresh clone. — ✅
4. **G-10 / G-11:** confirmed clean — no parallel STD files ever in the pack; anchors already on `EXT-*`; `PUBLIC_EXCERPT` resolved (2 files). G-10 "fold" left as an owner confirm (nothing to fold per C4-F1). — ✅
5. **D-02 / freeze:** registry freeze blockers cleared (B removed, A retained as a standing constraint); manifest regenerated & verifies; **owner froze v1.0.1**. — ✅

---

## Risks & cautions (how they played out)

- **R1 — CRLF/LF manifest mismatch.** Recurred at A5 (13-file episode) exactly as warned. Caught by the standing discipline (fresh-clone verify) and cured in the installer (whole-tree LF-normalize). Durable owner-env fix flagged: `git config core.autocrlf false`. **Carries into Phase B.**
- **R2 — Build-tool leakage into the pack.** Held — one-shot installers (`apply.py`, `apply_a2.py`, `apply_freeze_sweep.py`) stayed out of the hashed pack; the A3 harness correctly lives under `scripts/`.
- **R3 — Single live domain (PE-HIGH).** Accepted and recorded; the harness exercises one domain end-to-end. **Carries into Phase B (B6 walking skeleton).**

---

## What Phase A deliberately did NOT do

- No build repo, no `co-design/` migration, no runtime spec, no mode model, no walking skeleton, no AI/UI — **all Phase B.**
- No new governance documents.
- No reopening of DECIDED items.

---

## Owner action log (Amr)

- [x] Approved A1 labels `DESIGN`/`EXECUTION`.
- [x] `PUBLIC_EXCERPT` cleanup: **do now** (folded into A4).
- [x] Committed/pushed A1 + A2; fresh-clone verify PASS 200.
- [x] A3 → A4 edits committed; CI green on fresh clone.
- [x] A5: freeze-readiness check, **froze v1.0.1** (`0ec3060`); fresh-clone verify 173 / smoke / harness PASS.

**Phase A is closed.** This doc is now a historical record. Live status of record → `SESSION_LOG.md`; next roadmap → `PHASE_B_BUILD_WORKFLOW_PLAN.md` (B1).
