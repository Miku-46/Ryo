"""logcat (-v threadtime) から画面遷移・ディープリンク・招待/エラー関連行を抽出し、
証拠ID付きの Markdown 表を出力する。出力はすべて自動でマスクされる。

使い方:
  python3 -I tools/logcat_timeline.py private_inputs/case01_logcat.txt --case case01 [--pkg <PKG>]

抽出された行は「観測事実」。行の解釈（なぜその遷移が起きたか等）は
docs/02_observations.md に「推測」として別途記載すること。
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from dataclasses import dataclass

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from redact import redact  # noqa: E402

LINE = re.compile(
    r"^(?P<date>\d\d-\d\d)\s+(?P<time>\d\d:\d\d:\d\d\.\d{3})\s+(?P<pid>\d+)\s+(?P<tid>\d+)\s+"
    r"(?P<lvl>[VDIWEF])\s+(?P<tag>[^:]+?)\s*:\s(?P<msg>.*)$"
)

# (種別, 正規表現) — 先にマッチしたものを採用
RULES: list[tuple[str, re.Pattern[str]]] = [
    ("activity_start", re.compile(r"START u\d+ \{.*\}")),
    ("activity_displayed", re.compile(r"\bDisplayed\s+\S+/\S+")),
    ("intent_view", re.compile(r"act=android\.intent\.action\.VIEW|dat=\w+://")),
    ("app_links", re.compile(r"(?i)IntentFilterVerif|DomainVerif|app.?links?")),
    ("error", re.compile(r"(?i)\b(error|exception|fail(ed|ure)?)\b")),
    ("invite", re.compile(r"(?i)invite|invitation|referr|inviter")),
    ("deeplink", re.compile(r"(?i)deep.?link|schema|router|scheme")),
    ("webview", re.compile(r"(?i)webview|chromium.*Console")),
]


@dataclass
class Event:
    eid: str
    ts: str
    kind: str
    level: str
    tag: str
    msg: str


def classify(tag: str, msg: str, skip: tuple[str, ...] = ()) -> str | None:
    blob = f"{tag}: {msg}"
    for kind, pat in RULES:
        if kind not in skip and pat.search(blob):
            return kind
    return None


def extract(lines, case: str, pkg: str | None = None, errors_need_pkg: bool = True) -> list[Event]:
    events: list[Event] = []
    for raw in lines:
        m = LINE.match(raw.rstrip("\n"))
        if not m:
            continue
        tag, msg = m["tag"].strip(), m["msg"]
        kind = classify(tag, msg)
        if kind is None:
            continue
        # 汎用エラーはノイズが多いので、パッケージ名を含む行に限定（pkg指定時）。
        # ただし招待/ディープリンク等の語を含むなら、その種別で残す。
        if kind == "error" and pkg and errors_need_pkg and pkg not in msg:
            kind = classify(tag, msg, skip=("error",))
            if kind is None:
                continue
        if kind in ("activity_start", "activity_displayed") and pkg and pkg not in msg:
            continue
        events.append(Event(f"{case}-L{len(events) + 1:04d}", f"{m['date']} {m['time']}",
                            kind, m["lvl"], tag, redact(msg)))
    return events


def to_markdown(events: list[Event]) -> str:
    out = ["| 証拠ID | 時刻 | 種別 | Lv | タグ | 内容（マスク済） | 区分 |",
           "|---|---|---|---|---|---|---|"]
    for e in events:
        msg = e.msg.replace("|", "\\|")
        if len(msg) > 200:
            msg = msg[:200] + "…"
        out.append(f"| {e.eid} | {e.ts} | {e.kind} | {e.level} | {e.tag} | `{msg}` | 観測事実 |")
    return "\n".join(out) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("logfile")
    ap.add_argument("--case", required=True)
    ap.add_argument("--pkg")
    a = ap.parse_args()
    with open(a.logfile, encoding="utf-8", errors="replace") as f:
        sys.stdout.write(to_markdown(extract(f, a.case, a.pkg)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
