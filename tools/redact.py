"""ログのマスキング。共有・コミット前に必ず通す。

使い方: python3 -I tools/redact.py private_inputs/case01_logcat.txt > case01_redacted.txt
完全ではないため、出力は目視で確認すること。
"""
from __future__ import annotations

import re
import sys

# クエリ/JSON/ヘッダ中の機微キー（値をマスク）
SENSITIVE_KEYS = (
    "token|access_token|sessionid|session_id|sid_tt|sid_guard|uid_tt|sid|"
    "device_id|did|iid|install_id|openudid|udid|android_id|aid_ad|gaid|adid|cdid|"
    "ttwid|odin_tt|mstoken|x-tt-token|x-gorgon|x-khronos|x-argus|x-ladon|x-tt-params|cookie|set-cookie|"
    "invite_code|invitation_code|inviter_id|user_id|uid|sec_uid|unique_id|"
    "phone|mobile|email|nickname"
)
_KV = re.compile(
    rf'(?i)(["\']?\b(?:{SENSITIVE_KEYS})\b["\']?\s*[:=]\s*["\']?)([^"\'&\s,;}}]+)'
)
_EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
_PHONE_JP = re.compile(r"(?<!\d)(?:\+81[-\s]?|0)[789]0[-\s]?\d{4}[-\s]?\d{4}(?!\d)")
_IPV4 = re.compile(r"(?<![\d.])(?:\d{1,3}\.){3}\d{1,3}(?![\d.])")
_LONG_TOKEN = re.compile(r"\b[A-Za-z0-9_\-]{32,}\b")
_LONG_DIGITS = re.compile(r"(?<!\d)\d{15,}(?!\d)")  # 数値ID（ユーザーID・デバイスID等）


def redact(text: str) -> str:
    text = _KV.sub(lambda m: m.group(1) + "<REDACTED>", text)
    text = _EMAIL.sub("<EMAIL>", text)
    text = _PHONE_JP.sub("<PHONE>", text)
    text = _IPV4.sub("<IP>", text)
    text = _LONG_TOKEN.sub("<TOKEN>", text)
    text = _LONG_DIGITS.sub("<ID>", text)
    return text


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(__doc__, file=sys.stderr)
        return 2
    with open(argv[1], encoding="utf-8", errors="replace") as f:
        for line in f:
            sys.stdout.write(redact(line))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
