"""自作の模擬招待システム（実サービスとは無関係・外部通信なし）。"""
from .errors import InviteError
from .model import InviteService, Result, State
from .rules import CampaignConfig, User

__all__ = ["InviteError", "InviteService", "Result", "State", "CampaignConfig", "User"]
