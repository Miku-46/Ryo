"""模擬招待システムのエラー定義。

各エラーには根拠の種別を付ける:
  - "terms"      : 公開規約（Rewards Policy 等）に明記
  - "third_party": 第三者記事のみ（未検証）
  - "hypothesis" : 根拠なし。サーバー側条件の推測
APK/ログで確認できたら docs/05_evidence.md の証拠IDを evidence に追記する。
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


@dataclass(frozen=True)
class ErrorInfo:
    code: str
    message_ja: str
    basis: str  # terms | third_party | hypothesis
    evidence: tuple[str, ...] = ()


class InviteError(Enum):
    INVALID_CODE_FORMAT = ErrorInfo("E_FORMAT", "招待コードの形式が正しくありません", "hypothesis")
    CODE_NOT_FOUND = ErrorInfo("E_NOT_FOUND", "招待コードが見つかりません", "hypothesis")
    LINK_EXPIRED = ErrorInfo("E_EXPIRED", "招待リンクの有効期限が切れています", "hypothesis")
    CAMPAIGN_NOT_ACTIVE = ErrorInfo("E_CAMPAIGN", "キャンペーン期間外です", "hypothesis")
    SELF_INVITE = ErrorInfo("E_SELF", "自分自身は招待できません", "hypothesis")
    NOT_NEW_USER = ErrorInfo("E_NOT_NEW", "新規ユーザーではないため対象外です", "terms",
                             ("TERMS-RP-2b",))
    ALREADY_BOUND = ErrorInfo("E_BOUND", "すでに招待コードが登録されています", "hypothesis")
    REGION_NOT_ELIGIBLE = ErrorInfo("E_REGION", "お住まいの地域は対象外です", "third_party")
    AGE_NOT_ELIGIBLE = ErrorInfo("E_AGE", "年齢条件を満たしていません", "terms", ("TERMS-RP-1",))
    INVITER_CAP_REACHED = ErrorInfo("E_CAP", "招待の上限に達しました", "hypothesis")
    TASK_DEADLINE_PASSED = ErrorInfo("E_DEADLINE", "タスクの達成期限を過ぎました", "hypothesis")
    ACCOUNT_RESTRICTED = ErrorInfo("E_RESTRICTED", "アカウントが制限されています", "terms",
                                   ("TERMS-RP-viol",))

    @property
    def info(self) -> ErrorInfo:
        return self.value
