import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tools"))

import logcat_timeline  # noqa: E402
import manifest_links  # noqa: E402
from redact import redact  # noqa: E402

FIX = os.path.join(os.path.dirname(__file__), "fixtures")
PKG = "com.example.lite"  # 合成データ。実アプリのログではない


def test_redact_keys_and_patterns():
    s = ("GET /a?device_id=7311111111111111111&invite_code=ABC123&x=1 "
         "Cookie: sessionid=deadbeef mail a.b@example.com tel 090-1234-5678 ip 192.168.0.10")
    r = redact(s)
    for leaked in ("7311111111111111111", "ABC123", "deadbeef", "a.b@example.com", "090-1234-5678",
                   "192.168.0.10"):
        assert leaked not in r
    assert "x=1" in r


def test_redact_json_style():
    r = redact('{"user_id": "12345", "nickname":"ryo", "ok": true}')
    assert "12345" not in r and "ryo" not in r and '"ok": true' in r


def test_logcat_timeline_extracts_and_masks():
    with open(os.path.join(FIX, "logcat_sample.txt"), encoding="utf-8") as f:
        ev = logcat_timeline.extract(f, "t01", PKG)
    kinds = [e.kind for e in ev]
    assert kinds[0] == "activity_start"
    assert "activity_displayed" in kinds and "invite" in kinds
    assert "error" in kinds
    assert all("7300000000000000001" not in e.msg for e in ev)
    # 他パッケージのエラーは除外
    assert not any("com.other" in e.msg for e in ev)
    md = logcat_timeline.to_markdown(ev)
    assert "t01-L0001" in md and "観測事実" in md


def test_manifest_links():
    with open(os.path.join(FIX, "manifest_sample.xml"), encoding="utf-8") as f:
        rows = manifest_links.extract(f.read())
    pairs = {(r["scheme"], r["host"]) for r in rows}
    assert ("https", "invite.example.com") in pairs
    assert ("examplelite", "invite") in pairs
    assert not any(r["activity"].endswith("MainActivity") for r in rows)  # LAUNCHERのみは対象外
    https = next(r for r in rows if r["scheme"] == "https")
    assert https["autoVerify"] == "true" and https["browsable"]
