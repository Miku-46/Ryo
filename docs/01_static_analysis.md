# 01 静的解析（APK）

> 入力: `private_inputs/jadx_out/`（git管理外）。ここには要約・短い引用のみ記載。

## 1. ディープリンク／App Links（`tools/manifest_links.py` の出力を貼る）
_未取得_

## 2. 文字列リソース（招待・エラー文言）
抽出例: `grep -nE "invite|referral|invitation|reward" resources/res/values-ja/strings.xml`

| リソース名 | 文言（ja） | 証拠ID |
|---|---|---|

## 3. ルーティング／画面遷移
検索例: `grep -rlnE "invite|referral|inviter" sources/ | head`、ルーター登録（`//` スキーム文字列、`@RouterUri` 相当のアノテーション、`schema` 定数）

| 入口（URI/Intent） | 受け手クラス | 遷移先 | 根拠（クラス:行） | 区分 |
|---|---|---|---|---|

## 4. エラー処理
| エラーコード/条件 | 表示文言 | 分岐箇所 | クライアント判定か | 区分 |
|---|---|---|---|---|

**注意**: クライアント側で表示が分岐していても、判定自体がサーバー側なら「サーバー判定（推測）」と記載する。
