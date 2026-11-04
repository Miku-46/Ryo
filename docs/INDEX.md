# TikTok Lite 招待フロー解析 — 目次

| ファイル | 内容 | 状態 |
|---|---|---|
| [00_environment.md](00_environment.md) | 検証環境・対象バージョン | 端末情報待ち |
| [capture_checklist.md](capture_checklist.md) | ADB観測手順（観測のみ） | 準備済 |
| [01_static_analysis.md](01_static_analysis.md) | intent-filter・ルーティング・エラー処理 | APK解析結果待ち |
| [02_observations.md](02_observations.md) | ログ整理（観測事実／推測の分離） | ログ待ち |
| [03_terms_vs_ui.md](03_terms_vs_ui.md) | 公開規約とアプリ表示の照合 | 規約側のみ記入 |
| [04_state_machine.md](04_state_machine.md) | 状態遷移図 | 仮説版 |
| [05_evidence.md](05_evidence.md) | 証拠一覧 | 規約分のみ |
| [06_open_questions.md](06_open_questions.md) | 未解明事項 | 随時更新 |

## 方針
- 観測は自分の端末・自分（および同意した友人）のアカウントのみ。第三者サービスへの改変リクエストは送らない。
- 端末識別子の偽装、TLSピンニング等の検知回避、報酬の不正取得は行わない。
- APK・逆コンパイル全文・未マスクのログは `private_inputs/`（git管理外）に置く。リポジトリには要約・短い引用・マスク済み抜粋のみ。
- 記述には必ず区分を付ける: **【事実】**（証拠IDあり）／**【推測】**（根拠と確度を併記）。

## ツール
```bash
python3 -I tools/redact.py <log>                                # マスキング
python3 -I tools/logcat_timeline.py <logcat> --case case01 --pkg <PKG>  # タイムライン化
python3 -I tools/manifest_links.py <AndroidManifest.xml>         # ディープリンク一覧
python3 -m pytest -q                                            # 模擬招待システムのテスト
```
