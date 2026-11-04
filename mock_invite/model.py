"""インメモリの模擬招待サービスと状態遷移。

状態（docs/04_state_machine.md と対応）:
  ISSUED -> LINK_OPENED -> BOUND -> TASK_IN_PROGRESS -> PENDING_REVIEW -> REWARDED
  いずれの段階からも REJECTED(InviteError) へ遷移しうる。
PENDING_REVIEW は Rewards Policy の「審査（24時間目安）」を模したもので、
実際の審査ロジックは不明（推測）。
"""
from __future__ import annotations

import secrets
import string
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto

from . import rules
from .errors import InviteError


class State(Enum):
    ISSUED = auto()
    LINK_OPENED = auto()
    BOUND = auto()
    TASK_IN_PROGRESS = auto()
    PENDING_REVIEW = auto()
    REWARDED = auto()
    REJECTED = auto()


@dataclass
class Invite:
    code: str
    inviter_id: str
    issued_at: datetime


@dataclass
class Referral:
    invite: Invite
    invitee_id: str
    state: State
    bound_at: datetime | None = None
    error: InviteError | None = None
    history: list[tuple[State, str]] = field(default_factory=list)

    def move(self, state: State, note: str = "") -> None:
        self.state = state
        self.history.append((state, note))


@dataclass(frozen=True)
class Result:
    ok: bool
    state: State
    error: InviteError | None = None


class InviteService:
    def __init__(self, cfg: rules.CampaignConfig):
        self.cfg = cfg
        self.users: dict[str, rules.User] = {}
        self.invites: dict[str, Invite] = {}
        self.referrals: dict[str, Referral] = {}  # key: invitee_id

    # --- 招待する側 ---
    def add_user(self, user: rules.User) -> None:
        self.users[user.user_id] = user

    def issue(self, inviter_id: str, now: datetime, code: str | None = None) -> Invite:
        code = code or "".join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(8))
        inv = Invite(code, inviter_id, now)
        self.invites[code] = inv
        return inv

    def successful_count(self, inviter_id: str) -> int:
        return sum(1 for r in self.referrals.values()
                   if r.invite.inviter_id == inviter_id and r.state is State.REWARDED)

    # --- 招待される側 ---
    def open_link(self, code: str, now: datetime) -> Result:
        """リンクを開いた時点の検証（クライアント側で出る可能性のあるエラー）。"""
        for err in (rules.check_code_format(code),):
            if err:
                return Result(False, State.REJECTED, err)
        inv = self.invites.get(code)
        if inv is None:
            return Result(False, State.REJECTED, InviteError.CODE_NOT_FOUND)
        err = rules.check_campaign(self.cfg, now) or rules.check_link_ttl(self.cfg, inv.issued_at, now)
        if err:
            return Result(False, State.REJECTED, err)
        return Result(True, State.LINK_OPENED)

    def bind(self, invitee_id: str, code: str, now: datetime) -> Result:
        opened = self.open_link(code, now)
        if not opened.ok:
            return opened
        inv = self.invites[code]
        inviter, invitee = self.users[inv.inviter_id], self.users[invitee_id]
        err = (rules.check_invitee(self.cfg, inviter, invitee)
               or rules.check_inviter_cap(self.cfg, self.successful_count(inviter.user_id)))
        if err:
            return Result(False, State.REJECTED, err)
        invitee.bound_code = code
        ref = Referral(inv, invitee_id, State.BOUND, bound_at=now)
        ref.history.append((State.BOUND, "code bound"))
        ref.move(State.TASK_IN_PROGRESS)
        self.referrals[invitee_id] = ref
        return Result(True, ref.state)

    def checkin(self, invitee_id: str, now: datetime) -> None:
        self.users[invitee_id].checkins.add(now.date())

    def evaluate(self, invitee_id: str, now: datetime) -> Result:
        ref = self.referrals[invitee_id]
        if ref.state in (State.REWARDED, State.REJECTED):
            return Result(ref.state is State.REWARDED, ref.state, ref.error)
        invitee = self.users[invitee_id]
        if invitee.restricted:
            return self._reject(ref, InviteError.ACCOUNT_RESTRICTED)
        if rules.task_completed(self.cfg, invitee, ref.bound_at):
            if ref.state is State.TASK_IN_PROGRESS:
                ref.move(State.PENDING_REVIEW, "task done")
                return Result(True, ref.state)
            ref.move(State.REWARDED, "review passed (mock)")
            return Result(True, ref.state)
        if rules.task_deadline_passed(self.cfg, ref.bound_at, now):
            return self._reject(ref, InviteError.TASK_DEADLINE_PASSED)
        return Result(True, ref.state)

    @staticmethod
    def _reject(ref: Referral, err: InviteError) -> Result:
        ref.error = err
        ref.move(State.REJECTED, err.info.code)
        return Result(False, State.REJECTED, err)
