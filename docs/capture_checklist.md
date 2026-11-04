# ADB 観測チェックリスト（観測のみ）

## 事前
- [ ] 友人から、ログ取得・画面録画について同意を得た（友人端末を使う場合は特に）
- [ ] 友人は規約上の「新規ユーザー」に本当に該当する（作為的に新規を作らない）
- [ ] 端末の時刻を自動設定にし、PCとのずれを記録

## 環境記録（PowerShell）
```powershell
adb devices -l
adb shell getprop ro.build.version.release
adb shell getprop ro.product.model
adb shell pm list packages | findstr /i musically
adb shell dumpsys package <PKG> | findstr /i "versionName versionCode"
adb shell pm get-app-links <PKG>                 # Android 12+
adb shell dumpsys package <PKG> > pkg_dump.txt
```

## ケースごと（case01, case02, …）
```powershell
adb logcat -c
adb logcat -v threadtime > caseNN_logcat.txt     # 別ウィンドウ
adb shell screenrecord /sdcard/caseNN.mp4        # 別ウィンドウ（最大180秒）
# --- 操作 ---
adb shell dumpsys activity activities > caseNN_activities.txt
adb shell dumpsys window | findstr mCurrentFocus
adb pull /sdcard/caseNN.mp4
```

## ケース案
| ID | 前提 | 操作 | 記録するもの |
|---|---|---|---|
| case01 | 未インストール | 招待リンクをタップ → ストア → インストール → 起動 | 遷移先、コード入力欄の有無 |
| case02 | インストール済・未ログイン | 招待リンクをタップ | 起動Activity、ログイン誘導 |
| case03 | インストール済・ログイン済（新規友人） | 招待リンクをタップ | 紐付け画面・タスク表示 |
| case04 | 招待側本人の端末 | 自分のリンクをタップ | 自己招待時の表示（**確定操作はしない**） |
| case05 | 期限・地域等で対象外が見込まれる場合 | 表示を観察 | エラー文言の原文 |

## メモ様式（ケースごと）
```
case: case01 / 開始 10:00:00 / 終了 10:03:00
操作: 10:00:05 LINEでリンクをタップ → 10:00:07 ブラウザ表示 → ...
画面文言（原文）: 「……」
```

## mitmproxy について
- 通ればフローを保存（`private_inputs/` へ）。**証明書ピンニングで通らない場合は回避せず**、logcat・dumpsys・画面録画で進める（方針は試行後に再検討）。
