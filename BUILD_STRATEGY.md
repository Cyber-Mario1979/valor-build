# BUILD_STRATEGY

**Repo:** `valor-build` (the Phase-B build repo) · **Status:** scaffold (B1) · **Baseline:** frozen pack **v1.0.1 / `0ec3060`**.

This document is the seam between the **frozen VALOR Architecture Pack** (Layer 1, the deterministic engine) and the **build layer** we add around it (Layer 2 AI + Layer 3 UI). The pack stays pristine; everything here is additive and external to it.

---

## 1. The two repos

| Repo | Role | Mutability |
|------|------|------------|
| `Cyber-Mario1979/VALOR_Architecture_Pack` | **Layer 1** — contracts, schemas, WP truth, invariants. Frozen at **v1.0.1 (`0ec3060`)**, registry `frozen_controlled`, 173 governed files. | Frozen. Changes batch into a deliberate **v1.1.0** (D-02), never ad-hoc. |
| `valor-build` (this repo) | **Layers 2 + 3** + runtime, the A16 runtime spec, the mode model, the walking skeleton. | Active development. Never hashes the pack. |

The pack is consumed as a **pinned, read-only dependency**. We do not vendor a mutable copy, and we never edit pack files from here.

---

## 2. Pack dependency — pin mechanism (⚠ ONE OPEN DECISION)

The pack must be pinned at exactly **v1.0.1 / `0ec3060`** and treated as read-only. Three viable mechanisms — **owner to choose before the repo goes live:**

| Option | How | Pros | Cons |
|--------|-----|------|------|
| **(A) git submodule** *(recommended default)* | `git submodule add -b main <pack-url> pack` then `cd pack && git checkout v1.0.1` | Cleanest provenance; pack history stays separate and independently verifiable; impossible to accidentally edit-and-commit pack files into this repo. | Submodules are a known collaborator footgun (clone needs `--recurse-submodules`; updates are manual). |
| **(B) vendored read-only copy** | Copy the `0ec3060` tree into `pack/` (no `.git`); mark read-only; CI re-runs the pack's own `verify_manifest.py` to prove it's unmodified. | Simplest to clone and consume; no submodule mechanics. | Duplicates the hashed tree; nothing structural stops an edit — relies on the CI verify + discipline. |
| **(C) packaged dependency** | Build the pack into an installable artifact (wheel/tarball) pinned by version+hash; install into the env. | Most "correct" long-term; clean dependency semantics. | Most upfront plumbing; the pack isn't currently packaged. |

**Recommendation:** **(A) submodule** for now — it matches the project's whole ethos (the pack is governed, hash-verified, and must stay untouchable), and it's the lowest-effort way to guarantee the frozen tree can't drift. Revisit **(C)** if/when the pack gets packaged for wider consumption.

**Whichever is chosen,** CI must run the pack's own `verify_manifest.py` against the pinned tree on every build, so a tampered or wrong-commit pack fails fast. The mount point is `pack/` (gitignored until the mechanism is wired, so the scaffold stays clean for any of the three).

---

## 3. Co-evolve policy (D-02 / G-14)

- The pack is **frozen**. Build-layer needs do **not** trigger pack edits.
- Genuinely-needed pack changes are **batched** into a deliberate **v1.1.0**, reviewed and re-frozen the same way Phase A was (we edit pre-freeze; owner commits/freezes). The build repo then re-pins to the new tag.
- Carried open pack item: the **G-10 "fold"** confirm (nothing-to-fold per audit C4-F1, or supply the seven drafts for a diff) — if it ever produces a real new requirement, it rides a v1.1.0, not a hotfix.

---

## 4. Collaboration files — `co-design/` (D-01 / D-09)

All continuity/decision docs live in **`co-design/`**, **outside any manifest**. Migrated here in B1: `SESSION_LOG.md`, `CHANGELOG.md`, the gap assessment (v0.3), the audit report (v1.0), the **freeze-status register**, and both phase plans. The owner commits them; co-design reads/writes through the owner.

Raw per-session fragments are not kept here — they live in an `_archive/` outside the repo (gitignored if ever dropped in).

---

## 5. LF discipline (R1 — non-negotiable, made structural)

The single recurring gremlin across Phase A was CRLF/LF manifest mismatch. Structural defenses in this repo:

- **`.gitattributes` forces `eol=lf`** on all text; `*.png` and other binaries are `binary`.
- Any tool that writes files writes **LF** (`write_bytes`, never text-mode on Windows).
- **Trust a fresh-clone verify, never the local one** — the committed/normalized state is what CI sees.
- **`apply*.py` is the standard checkpoint delivery format — and is never committed.** Each checkpoint the assistant emits a single gitignored `apply_sessionN.py` that writes the checkpoint's **repo** docs into the working tree: **LF-deterministic, idempotent, fail-closed** (all anchors resolved before any write), and **never touching the frozen pack**. The owner runs it, reviews `git diff`, and commits **only** the resulting doc changes; `.gitignore` blocks `apply*.py` so the installer itself can never land. **Manual full-file replacement is the documented fallback.** Non-repo artifacts (e.g. `SESSION_PROTOCOL.md`, the instructions field) have other homes — see the artifact-home → landing-mechanism table in `SESSION_PROTOCOL.md` (D-01).
- Owner-env cure (recommended): `git config core.autocrlf false` and work from a fresh LF clone.

---

## 6. Layout

```
valor-build/
├── README.md
├── BUILD_STRATEGY.md            ← this file
├── LICENSE                      (placeholder)
├── pyproject.toml               (Python + jsonschema/referencing — D-04)
├── .gitattributes  .gitignore
├── pack/                        ← frozen pack mount (submodule/vendor/package; gitignored until wired)
├── co-design/                   ← non-hashed continuity + decision docs (migrated)
├── docs/
│   └── A16_Runtime_Target_Spec.md   (B2 — skeleton only)
├── src/valor_build/
│   ├── engine/   (Layer 1 adapter — reads the frozen pack; placeholder)
│   ├── ai/       (Layer 2 — D-08 refuse/accept interface; placeholder)
│   └── modes/    (runtime M1–M4; placeholder)
└── tests/
```

---

## 7. What's next (Phase B sequence)

B1 (this scaffold) → **B2 `docs/A16_Runtime_Target_Spec.md`** (biggest buildability gap, G-01) → B3 BUILD mode → B4 mode model → B5 Project container (M4) → B6 walking skeleton (PE-HIGH) → B7 identity milestone. Full detail in `co-design/PHASE_B_BUILD_WORKFLOW_PLAN.md`.
