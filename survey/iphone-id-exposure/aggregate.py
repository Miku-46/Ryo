#!/usr/bin/env python3
"""iPhone中古出品の識別番号「公開状況」調査CSVを検証・集計する。

番号そのものは記録しない方針のため、IMEI/シリアルらしき文字列が
どの列に含まれていても検証エラーにする。

使い方:
    python3 aggregate.py listings.csv [--target 50]
"""

import argparse
import csv
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime
from urllib.parse import urlparse

COLUMNS = [
    "商品URL", "取得元", "機種", "価格", "状態", "販売状況",
    "IMEI記載", "シリアル記載", "記載箇所", "確認日時", "備考",
]
SITES = {"メルカリ", "Yahoo!オークション", "楽天ラクマ"}
MODELS = {
    f"iPhone {gen}{suffix}"
    for gen in range(14, 18)
    for suffix in ("", " Plus", " Pro", " Pro Max")
}
CONDITIONS = {"中古", "ジャンク"}
EXPOSURE = {"あり", "一部伏せ字", "なし", "未確認"}
LOCATIONS = {"説明文", "画像", "説明文+画像", "-"}
EXPOSED = {"あり", "一部伏せ字"}

# 生の番号が紛れ込んでいないかの検出（IMEI: 15桁、Apple シリアル: 英数字10〜12桁）
RAW_IMEI = re.compile(r"(?<!\d)\d{15}(?!\d)")
RAW_SERIAL = re.compile(r"(?<![A-Z0-9])(?=[A-Z0-9]*\d)(?=[A-Z0-9]*[A-Z])[A-Z0-9]{10,12}(?![A-Z0-9])")

# サイトごとの商品IDの取り出し方（重複判定に使う）
ITEM_ID_PATTERNS = {
    "jp.mercari.com": re.compile(r"/item/(m\d+)"),
    "auctions.yahoo.co.jp": re.compile(r"/auction/([a-z]?\d+)"),
    "page.auctions.yahoo.co.jp": re.compile(r"/auction/([a-z]?\d+)"),
    "item.fril.jp": re.compile(r"/([0-9a-f]{32})"),
}


def item_key(url):
    parsed = urlparse(url.strip())
    host = parsed.netloc.lower()
    pattern = ITEM_ID_PATTERNS.get(host)
    if pattern and (m := pattern.search(parsed.path)):
        return f"{host}:{m.group(1)}"
    return f"{host}{parsed.path.rstrip('/')}"


def validate(row, line):
    errors = []
    for col in COLUMNS:
        if col == "商品URL":
            continue
        value = row.get(col) or ""
        if RAW_IMEI.search(value) or RAW_SERIAL.search(value.upper()):
            errors.append(f"{line}行目 {col}: 番号そのものらしき文字列があります。区分だけを記録してください")
    checks = [
        ("取得元", SITES), ("機種", MODELS), ("状態", CONDITIONS),
        ("IMEI記載", EXPOSURE), ("シリアル記載", EXPOSURE), ("記載箇所", LOCATIONS),
    ]
    for col, allowed in checks:
        if row[col] not in allowed:
            errors.append(f"{line}行目 {col}: 「{row[col]}」は不正な値です")
    if not row["価格"].isdigit():
        errors.append(f"{line}行目 価格: 数字のみで記入してください")
    try:
        datetime.fromisoformat(row["確認日時"])
    except ValueError:
        errors.append(f"{line}行目 確認日時: ISO形式（例 2026-10-14T15:30+09:00）で記入してください")
    exposed = row["IMEI記載"] in EXPOSED or row["シリアル記載"] in EXPOSED
    if exposed and row["記載箇所"] == "-":
        errors.append(f"{line}行目 記載箇所: 記載ありの場合は箇所を記入してください")
    return errors


def rate(n, total):
    return f"{n}/{total} ({n / total:.0%})" if total else "0/0"


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("csv_path")
    parser.add_argument("--target", type=int, default=50)
    args = parser.parse_args()

    with open(args.csv_path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames != COLUMNS:
            sys.exit(f"列が想定と異なります: {reader.fieldnames}")
        rows = list(reader)

    errors, seen, kept = [], set(), []
    excluded = Counter()
    for i, row in enumerate(rows, start=2):
        errors += validate(row, i)
        if row["販売状況"] != "販売中":
            excluded["販売中と確認できない"] += 1
            continue
        key = item_key(row["商品URL"])
        if key in seen:
            excluded["重複"] += 1
            continue
        seen.add(key)
        kept.append(row)

    if errors:
        print("\n".join(errors))
        sys.exit(1)

    total = len(kept)
    print(f"有効件数: {total} / 目標 {args.target}"
          + ("" if total >= args.target else f"（あと {args.target - total} 件）"))
    for reason, n in excluded.items():
        print(f"除外（{reason}）: {n}")

    def summarize(label, group):
        n = len(group)
        imei = sum(r["IMEI記載"] in EXPOSED for r in group)
        serial = sum(r["シリアル記載"] in EXPOSED for r in group)
        either = sum(r["IMEI記載"] in EXPOSED or r["シリアル記載"] in EXPOSED for r in group)
        unknown = sum("未確認" in (r["IMEI記載"], r["シリアル記載"]) for r in group)
        print(f"\n[{label}] {n}件")
        print(f"  IMEI記載あり（伏せ字含む）    : {rate(imei, n)}")
        print(f"  シリアル記載あり（伏せ字含む）: {rate(serial, n)}")
        print(f"  いずれか記載あり              : {rate(either, n)}")
        print(f"  未確認を含む                  : {rate(unknown, n)}")

    summarize("全体", kept)
    by_site = defaultdict(list)
    for r in kept:
        by_site[r["取得元"]].append(r)
    for site in sorted(by_site):
        summarize(site, by_site[site])

    print("\n[記載箇所（いずれか記載ありの商品）]")
    places = Counter(r["記載箇所"] for r in kept
                     if r["IMEI記載"] in EXPOSED or r["シリアル記載"] in EXPOSED)
    for place, n in places.most_common():
        print(f"  {place}: {n}")


if __name__ == "__main__":
    main()
