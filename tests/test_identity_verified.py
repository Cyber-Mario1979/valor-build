"""M-IDENTITY — verified-identity invariants (C1 Step 3, D-16).

Proves the *verified* half B7 §4 named and deferred: a real credential check produces
a verified ``Principal`` with a populated ``actor.id`` and ``identity_verified=True``
(the A09 §6.2 seam, lifted); the D-16 soft role->action map validates real authority
for sensitive (``confirm:true``) actions; controlled-document finalize enforces
approver(s) != author as a *soft* multi-approver warn-with-ack; and the A10 §8 security
audit events fire. Everything stays SOFT (warn-with-ack, never hard RBAC — R6); hard
enforcement is C4. Pack frozen at ``0ec3060``; zero pack/schema change.
"""
from __future__ import annotations

import pytest

from valor_build.engine.audit import AuditLog
from valor_build.engine.authority import Approval, authorize, evaluate_approval
from valor_build.engine.dispatch import Dispatcher, StepRequest
from valor_build.engine.gates import Lifecycle
from valor_build.engine.identity import (
    AuthenticationError,
    CredentialStore,
    LocalIdentityProvider,
    Principal,
    make_credential,
    principal_id,
)
from valor_build.engine.registry import ContractRegistry
from valor_build.engine.schemas import SchemaRegistry
from valor_build.modes.runtime import RuntimeMode
from valor_build.coverage import run_coverage_matrix, summarize
from valor_build.skeleton import run_walking_skeleton


# -- fixtures ---------------------------------------------------------------

def _store():
    s = CredentialStore()
    s.add(make_credential("amr", "rock-n-roll", "admin", role="admin", name="Amr"))
    s.add(make_credential("ed", "pw-ed", "editor", role="CQV editor"))
    s.add(make_credential("appr", "pw-appr", "approver", role="QA approver"))
    s.add(make_credential("ro", "pw-ro", "read-only", role="viewer"))
    s.add(make_credential("cqv", "pw-cqv", "CQV", role="CQV engineer"))
    return s


def _principal(profile, *, name=None, role=None, uid=None):
    return Principal(id=uid or f"valor:uid:{profile}", profile=profile,
                     role=role or profile, name=name)


def _disp(confirm=lambda _m: True):
    return Dispatcher(ContractRegistry(), SchemaRegistry(), AuditLog(), confirm)


def _req(action, principal, *, author_id="", approvals=()):
    return StepRequest(
        action=action, payload={}, target={"wp_id": "WP-X"},
        runtime_mode=RuntimeMode.M3, lifecycle=Lifecycle.BUILD, engine_mode="EXECUTION",
        actor_role="", state="DONE", gate=None, principal=principal,
        author_id=author_id, approvals=approvals,
    )


# -- authentication (real credential check) ---------------------------------

def test_authenticate_returns_verified_principal_with_real_id():
    audit = AuditLog()
    provider = LocalIdentityProvider(_store(), audit)
    p = provider.authenticate("amr", "rock-n-roll")
    assert p.verified is True
    assert p.profile == "admin"
    assert p.id == principal_id("amr") == "valor:uid:amr"
    # one success audit event, no security block
    assert len(audit.of_kind("auth_event")) == 1
    assert audit.of_kind("security_event") == []


def test_wrong_secret_raises_and_emits_security_block():
    audit = AuditLog()
    provider = LocalIdentityProvider(_store(), audit)
    with pytest.raises(AuthenticationError):
        provider.authenticate("amr", "wrong")
    blocks = audit.of_kind("security_event")
    assert len(blocks) == 1
    assert blocks[0]["event_type"] == "EVT_SECURITY_POLICY_BLOCK"
    assert blocks[0]["identity_verified"] is False
    assert audit.of_kind("auth_event") == []


def test_unknown_user_raises_and_emits_security_block():
    audit = AuditLog()
    provider = LocalIdentityProvider(_store(), audit)
    with pytest.raises(AuthenticationError):
        provider.authenticate("nobody", "x")
    assert audit.of_kind("security_event")[0]["event_type"] == "EVT_SECURITY_POLICY_BLOCK"


def test_secret_is_never_stored_in_clear():
    cred = make_credential("u", "s3cr3t", "editor")
    assert b"s3cr3t" not in cred.hash
    assert cred.hash != b"s3cr3t"
    assert make_credential("u", "wrong", "editor", salt=cred.salt).hash != cred.hash


def test_unknown_profile_rejected_at_credential_build():
    with pytest.raises(ValueError):
        make_credential("u", "s", "superuser")


# -- the D-16 soft role->action map (pure) ----------------------------------

def _spec(action):
    return ContractRegistry().resolve(action)


def test_admin_authorized_for_everything():
    for action in ("WP_CREATE", "DOC_FINALIZE_ARTIFACT", "RPT_GENERATE_WORKBOOK_EXPORT"):
        assert authorize("admin", _spec(action)).authorized is True


def test_editor_runs_task_path_but_cannot_approve_documents():
    assert authorize("editor", _spec("WP_CREATE")).authorized is True
    assert authorize("editor", _spec("WP_APPLY_PLAN_PROPOSAL")).authorized is True
    assert authorize("editor", _spec("DOC_FINALIZE_ARTIFACT")).authorized is False


def test_approver_may_finalize_documents():
    assert authorize("approver", _spec("DOC_FINALIZE_ARTIFACT")).authorized is True


def test_cqv_engineer_runs_the_task_path_solo():
    for action in ("WP_CREATE", "WP_COMMIT_STAGED_TASKS", "WP_APPLY_PLAN_PROPOSAL",
                   "RPT_GENERATE_WORKBOOK_EXPORT"):
        assert authorize("CQV", _spec(action)).authorized is True


def test_read_only_blocked_on_sensitive_but_free_on_reads():
    assert authorize("read-only", _spec("WP_CREATE")).authorized is False
    # non-sensitive (confirm:false) reads are never authority-gated
    assert authorize("read-only", _spec("WP_GET")).authorized is True
    assert authorize("read-only", _spec("RPT_GET_ARTIFACT")).authorized is True


def test_non_sensitive_action_never_gated_for_any_profile():
    for profile in ("read-only", "editor", "approver", "admin", "CQV"):
        assert authorize(profile, _spec("WP_GET")).authorized is True


# -- approver != author (multi-approver, engine/audit layer) ----------------

def test_single_user_author_equals_approver_is_a_conflict():
    d = evaluate_approval("valor:uid:amr", [Approval("valor:uid:amr", "admin")])
    assert d.conflict is True and d.requires_ack is True


def test_distinct_approver_set_has_no_conflict():
    d = evaluate_approval(
        "valor:uid:author",
        [Approval("valor:uid:prod", "head of production"),
         Approval("valor:uid:qa", "head of quality")],
    )
    assert d.conflict is False
    assert d.approver_ids == ("valor:uid:prod", "valor:uid:qa")


# -- dispatch: verified path engages ----------------------------------------

def test_verified_slice_flips_identity_verified_and_populates_actor_id(tmp_path):
    admin = _principal("admin", name="Amr", uid="valor:uid:amr")
    result = run_walking_skeleton(tmp_path, principal=admin)
    assert result.all_ok
    ctx = result.audit.of_kind("identity_context")
    assert len(ctx) == 8
    assert all(e["identity_verified"] is True for e in ctx)
    assert all(e["actor_id"] == "valor:uid:amr" for e in ctx)
    stamps = result.audit.of_kind("output_stamp")
    assert stamps and all(s.get("actor_id") == "valor:uid:amr" for s in stamps)
    assert all(s.get("identity_verified") is True for s in stamps)


def test_admin_actions_are_always_logged(tmp_path):
    admin = _principal("admin", uid="valor:uid:amr")
    result = run_walking_skeleton(tmp_path, principal=admin)
    admin_events = [e for e in result.audit.of_kind("security_event")
                    if e["event_type"] == "EVT_ADMIN_ACTION"]
    # one per confirm:true step in the 8-step slice (5 of them)
    assert len(admin_events) == 5
    # admin never trips an authority warning
    assert result.audit.of_kind("authority_warning") == []


def test_unauthorized_profile_declined_refuses_with_security_block():
    # read-only attempting a mutating confirm action, ack declined -> soft refusal.
    disp = _disp(confirm=lambda _m: False)
    res = disp.dispatch(_req("WP_CREATE", _principal("read-only")), lambda: {})
    assert not res.ok
    assert res.error["code"] == "AUTHORITY_UNACKNOWLEDGED"
    warn = disp.audit.of_kind("authority_warning")
    assert len(warn) == 1 and warn[0]["acknowledged"] is False
    block = [e for e in disp.audit.of_kind("security_event")
             if e["event_type"] == "EVT_SECURITY_POLICY_BLOCK"]
    assert len(block) == 1 and block[0]["phase"] == "authorization"


def test_unauthorized_profile_acknowledged_proceeds_past_authority():
    # Same unauthorized action, acknowledged -> soft control lets it through; any
    # refusal is downstream (result schema), never the authority code.
    disp = _disp(confirm=lambda _m: True)
    res = disp.dispatch(_req("WP_CREATE", _principal("read-only")), lambda: {})
    warn = disp.audit.of_kind("authority_warning")
    assert len(warn) == 1 and warn[0]["acknowledged"] is True
    assert res.error is None or res.error["code"] != "AUTHORITY_UNACKNOWLEDGED"


def test_doc_finalize_records_full_approver_set_and_conflict():
    # author == approver (single user) -> conflict; declined -> approver/author refusal.
    disp = _disp(confirm=lambda _m: False)
    appr = _principal("approver", uid="valor:uid:appr")
    res = disp.dispatch(
        _req("DOC_FINALIZE_ARTIFACT", appr, author_id="valor:uid:appr"), lambda: {})
    assert not res.ok
    assert res.error["code"] == "APPROVER_AUTHOR_CONFLICT_UNACKNOWLEDGED"
    doc = disp.audit.of_kind("document_approval")
    assert len(doc) == 1
    assert doc[0]["approver_author_conflict"] is True
    assert doc[0]["approver_set"][0]["id"] == "valor:uid:appr"


def test_doc_finalize_distinct_approver_no_conflict_passes_authority():
    # approver != author + a multi-approver set -> no conflict at the approval gate.
    disp = _disp(confirm=lambda _m: True)
    appr = _principal("approver", uid="valor:uid:appr")
    approvals = (Approval("valor:uid:prod", "head of production"),
                 Approval("valor:uid:qa", "head of quality"))
    res = disp.dispatch(
        _req("DOC_FINALIZE_ARTIFACT", appr, author_id="valor:uid:author", approvals=approvals),
        lambda: {})
    doc = disp.audit.of_kind("document_approval")
    assert doc[0]["approver_author_conflict"] is False
    assert len(doc[0]["approver_set"]) == 2
    # no approver/author refusal; any refusal is downstream
    assert res.error is None or res.error["code"] != "APPROVER_AUTHOR_CONFLICT_UNACKNOWLEDGED"


# -- C1 EXIT: the whole grid runs single-user with identity verified ---------

def test_coverage_matrix_runs_green_with_identity_verified(tmp_path):
    admin = _principal("admin", name="Amr", uid="valor:uid:amr")
    cells = run_coverage_matrix(tmp_path, principal=admin)
    s = summarize(cells)
    assert s["total_cells"] == 96
    assert s["failed"] == [], [(c.action_type, c.mode, c.note) for c in s["failed"]]
    assert s["action_count"] == 27
