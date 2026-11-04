from datetime import datetime, timedelta

import pytest

from mock_invite import CampaignConfig, InviteError, InviteService, State, User

T0 = datetime(2026, 11, 1, 12, 0)


@pytest.fixture
def svc():
    cfg = CampaignConfig(start=T0 - timedelta(days=30), end=T0 + timedelta(days=30), inviter_cap=2)
    s = InviteService(cfg)
    s.add_user(User("inviter", "JP", 30, T0 - timedelta(days=100)))
    s.add_user(User("friend", "JP", 25, T0))
    s.issue("inviter", T0, code="ABC12345")
    return s


def new_friend(s, uid, **kw):
    s.add_user(User(uid, kw.pop("region", "JP"), kw.pop("age", 25), T0, **kw))
    return uid


# --- 正常系 ---
def test_happy_path_reaches_rewarded(svc):
    assert svc.bind("friend", "ABC12345", T0).state is State.TASK_IN_PROGRESS
    svc.checkin("friend", T0 + timedelta(days=1))
    assert svc.evaluate("friend", T0 + timedelta(days=1)).state is State.PENDING_REVIEW
    assert svc.evaluate("friend", T0 + timedelta(days=2)).state is State.REWARDED
    hist = [st for st, _ in svc.referrals["friend"].history]
    assert hist == [State.BOUND, State.TASK_IN_PROGRESS, State.PENDING_REVIEW, State.REWARDED]


def test_task_not_done_yet_stays_in_progress(svc):
    svc.bind("friend", "ABC12345", T0)
    assert svc.evaluate("friend", T0 + timedelta(days=3)).state is State.TASK_IN_PROGRESS


# --- リンク段階のエラー ---
@pytest.mark.parametrize("code", ["", "abc", "ab!c1234", "X" * 13])
def test_invalid_code_format(svc, code):
    assert svc.open_link(code, T0).error is InviteError.INVALID_CODE_FORMAT


def test_code_not_found(svc):
    assert svc.open_link("ZZZ99999", T0).error is InviteError.CODE_NOT_FOUND


def test_link_expired(svc):
    assert svc.open_link("ABC12345", T0 + timedelta(days=8)).error is InviteError.LINK_EXPIRED


def test_campaign_not_active(svc):
    assert svc.open_link("ABC12345", T0 + timedelta(days=31)).error is InviteError.CAMPAIGN_NOT_ACTIVE


# --- 招待される側の適格性 ---
def test_self_invite(svc):
    assert svc.bind("inviter", "ABC12345", T0).error is InviteError.SELF_INVITE


def test_not_new_user(svc):
    uid = new_friend(svc, "old", has_prior_account=True)
    assert svc.bind(uid, "ABC12345", T0).error is InviteError.NOT_NEW_USER


def test_already_bound(svc):
    svc.bind("friend", "ABC12345", T0)
    assert svc.bind("friend", "ABC12345", T0).error is InviteError.ALREADY_BOUND


@pytest.mark.parametrize("region", ["US", "KR"])
def test_region_not_eligible(svc, region):
    uid = new_friend(svc, "abroad", region=region)
    assert svc.bind(uid, "ABC12345", T0).error is InviteError.REGION_NOT_ELIGIBLE


def test_age_not_eligible(svc):
    uid = new_friend(svc, "minor", age=17)
    assert svc.bind(uid, "ABC12345", T0).error is InviteError.AGE_NOT_ELIGIBLE


def test_restricted_account_at_bind(svc):
    uid = new_friend(svc, "banned", restricted=True)
    assert svc.bind(uid, "ABC12345", T0).error is InviteError.ACCOUNT_RESTRICTED


def test_restricted_after_bind_rejects_on_evaluate(svc):
    svc.bind("friend", "ABC12345", T0)
    svc.users["friend"].restricted = True
    r = svc.evaluate("friend", T0 + timedelta(days=1))
    assert (r.state, r.error) == (State.REJECTED, InviteError.ACCOUNT_RESTRICTED)


# --- 上限・期限 ---
def test_inviter_cap_reached(svc):
    for i in range(2):
        uid = new_friend(svc, f"f{i}")
        svc.bind(uid, "ABC12345", T0)
        svc.checkin(uid, T0)
        svc.evaluate(uid, T0)
        svc.evaluate(uid, T0)
    assert svc.successful_count("inviter") == 2
    uid = new_friend(svc, "f3")
    assert svc.bind(uid, "ABC12345", T0).error is InviteError.INVITER_CAP_REACHED


def test_task_deadline_passed(svc):
    svc.bind("friend", "ABC12345", T0)
    r = svc.evaluate("friend", T0 + timedelta(days=8))
    assert (r.state, r.error) == (State.REJECTED, InviteError.TASK_DEADLINE_PASSED)


def test_checkin_after_deadline_does_not_count(svc):
    svc.bind("friend", "ABC12345", T0)
    svc.checkin("friend", T0 + timedelta(days=9))
    assert svc.evaluate("friend", T0 + timedelta(days=9)).error is InviteError.TASK_DEADLINE_PASSED


def test_terminal_states_are_sticky(svc):
    svc.bind("friend", "ABC12345", T0)
    svc.evaluate("friend", T0 + timedelta(days=8))
    svc.checkin("friend", T0 + timedelta(days=8))
    assert svc.evaluate("friend", T0 + timedelta(days=8)).state is State.REJECTED


def test_every_error_has_basis():
    for e in InviteError:
        assert e.info.basis in {"terms", "third_party", "hypothesis"}
        assert e.info.message_ja
