"""条件判定（純粋関数）。外部通信・端末情報は一切扱わない。

「新規ユーザー」かどうかは User.has_prior_account という抽象フラグで表す。
実サービスの判定方法（サーバー側）は不明であり、ここでは再現しない。
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta

from .errors import InviteError

CODE_PATTERN = re.compile(r"^[A-Z0-9]{6,12}$")  # 仮定。実際の形式は APK/ログで要確認


@dataclass(frozen=True)
class CampaignConfig:
    start: datetime
    end: datetime
    link_ttl: timedelta = timedelta(days=7)          # 仮定
    eligible_regions: frozenset[str] = frozenset({"JP"})  # 第三者記事ベース
    min_age: int = 18                                 # Rewards Policy (ROW) 1.
    inviter_cap: int = 10                             # 仮定
    task_days: int = 7                                # 仮定
    required_checkins: int = 1                        # 公式招待ページ「daily check-in」より。日数は仮定


@dataclass
class User:
    user_id: str
    region: str
    age: int
    created_at: datetime
    has_prior_account: bool = False   # 抽象化された「既存利用歴」
    restricted: bool = False
    bound_code: str | None = None
    checkins: set[date] = field(default_factory=set)


def check_code_format(code: str) -> InviteError | None:
    return None if CODE_PATTERN.fullmatch(code or "") else InviteError.INVALID_CODE_FORMAT


def check_campaign(cfg: CampaignConfig, now: datetime) -> InviteError | None:
    return None if cfg.start <= now <= cfg.end else InviteError.CAMPAIGN_NOT_ACTIVE


def check_link_ttl(cfg: CampaignConfig, issued_at: datetime, now: datetime) -> InviteError | None:
    return InviteError.LINK_EXPIRED if now - issued_at > cfg.link_ttl else None


def check_invitee(cfg: CampaignConfig, inviter: User, invitee: User) -> InviteError | None:
    """招待される側の適格性。判定順は仮定（実アプリの表示順で要検証）。"""
    if invitee.user_id == inviter.user_id:
        return InviteError.SELF_INVITE
    if invitee.restricted:
        return InviteError.ACCOUNT_RESTRICTED
    if invitee.bound_code is not None:
        return InviteError.ALREADY_BOUND
    if invitee.has_prior_account:
        return InviteError.NOT_NEW_USER
    if invitee.region not in cfg.eligible_regions or invitee.region != inviter.region:
        return InviteError.REGION_NOT_ELIGIBLE
    if invitee.age < cfg.min_age:
        return InviteError.AGE_NOT_ELIGIBLE
    return None


def check_inviter_cap(cfg: CampaignConfig, successful_count: int) -> InviteError | None:
    return InviteError.INVITER_CAP_REACHED if successful_count >= cfg.inviter_cap else None


def task_completed(cfg: CampaignConfig, invitee: User, bound_at: datetime) -> bool:
    deadline = (bound_at + timedelta(days=cfg.task_days)).date()
    valid = {d for d in invitee.checkins if bound_at.date() <= d <= deadline}
    return len(valid) >= cfg.required_checkins


def task_deadline_passed(cfg: CampaignConfig, bound_at: datetime, now: datetime) -> bool:
    return now > bound_at + timedelta(days=cfg.task_days)
