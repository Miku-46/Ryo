# 04 招待関連の状態遷移（仮説版 v0）

凡例: 実線＝規約/観測に根拠あり予定、`?` 付き＝**推測（サーバー側条件を含む）**。観測後に証拠IDを付与して更新する。

```mermaid
stateDiagram-v2
    [*] --> LinkTapped: 招待リンクをタップ
    LinkTapped --> Browser: App Links未検証/未インストール
    LinkTapped --> AppLaunched: App Links検証済 & インストール済
    Browser --> Store: ダウンロード誘導
    Store --> FirstLaunch: インストール後初回起動
    FirstLaunch --> AttributionResolved: 招待情報の引継ぎ?（方式は不明）
    AppLaunched --> DeepLinkRouted: intent-filter → ルーター
    AttributionResolved --> Auth
    DeepLinkRouted --> Auth: 未ログイン
    DeepLinkRouted --> BindRequest: ログイン済
    Auth --> BindRequest: 新規登録/ログイン完了
    BindRequest --> Rejected: クライアント検証NG?（形式・期限）
    BindRequest --> ServerCheck: 紐付け要求
    ServerCheck --> Rejected: 新規でない/自己招待/地域/年齢/上限?（サーバー判定・推測）
    ServerCheck --> TaskInProgress: 紐付け成功
    TaskInProgress --> PendingReview: Engagement Actions完了（例: チェックイン）
    TaskInProgress --> Rejected: 期限超過?
    PendingReview --> Rewarded: 審査通過（24h目安・TERMS-RP）
    PendingReview --> Rejected: 不正判定/資格取消（TERMS-RP §4）
    Rewarded --> [*]
    Rejected --> [*]
```

## 模擬システムとの対応
| 図の状態 | `mock_invite.State` |
|---|---|
| DeepLinkRouted / AttributionResolved | `LINK_OPENED`（`open_link`） |
| ServerCheck 成功 | `BOUND` → `TASK_IN_PROGRESS`（`bind`） |
| PendingReview / Rewarded / Rejected | 同名（`evaluate`） |

模擬システムは「インストール前後の引継ぎ方式」「不正判定」を**再現しない**（不明かつ再現の必要なし）。
