"""JADX 出力の AndroidManifest.xml から VIEW 系 intent-filter（ディープリンク/App Links）を一覧化する。

使い方:
  python3 -I tools/manifest_links.py private_inputs/jadx_out/resources/AndroidManifest.xml
出力: Markdown 表（Activity / scheme / host / path / autoVerify / exported）
"""
from __future__ import annotations

import sys
import xml.etree.ElementTree as ET

A = "{http://schemas.android.com/apk/res/android}"


def extract(xml_text: str) -> list[dict]:
    root = ET.fromstring(xml_text)
    rows: list[dict] = []
    for comp in root.iter():
        if comp.tag not in ("activity", "activity-alias"):
            continue
        name = comp.get(A + "name", "")
        exported = comp.get(A + "exported", "")
        for f in comp.findall("intent-filter"):
            actions = {a.get(A + "name") for a in f.findall("action")}
            if "android.intent.action.VIEW" not in actions:
                continue
            cats = {c.get(A + "name") for c in f.findall("category")}
            datas = f.findall("data")
            schemes = [d.get(A + "scheme") for d in datas if d.get(A + "scheme")] or [""]
            hosts = [d.get(A + "host") for d in datas if d.get(A + "host")] or [""]
            paths = [d.get(A + k) for d in datas
                     for k in ("path", "pathPrefix", "pathPattern", "pathAdvancedPattern")
                     if d.get(A + k)] or [""]
            for s in schemes:
                for h in hosts:
                    rows.append({
                        "activity": name, "scheme": s, "host": h, "paths": ", ".join(paths),
                        "autoVerify": f.get(A + "autoVerify", ""),
                        "browsable": "android.intent.category.BROWSABLE" in cats,
                        "exported": exported,
                    })
    return rows


def to_markdown(rows: list[dict]) -> str:
    out = ["| Activity | scheme | host | path | autoVerify | BROWSABLE | exported |",
           "|---|---|---|---|---|---|---|"]
    for r in rows:
        out.append(f"| `{r['activity']}` | {r['scheme']} | {r['host']} | {r['paths']} | "
                   f"{r['autoVerify']} | {r['browsable']} | {r['exported']} |")
    return "\n".join(out) + "\n"


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(__doc__, file=sys.stderr)
        return 2
    with open(argv[1], encoding="utf-8") as f:
        sys.stdout.write(to_markdown(extract(f.read())))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
