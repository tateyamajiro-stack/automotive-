# HILS開発管理システム

自動車組込みHILS（Hardware-In-the-Loop Simulation）テスト開発のプロジェクト管理デスクトップアプリケーション。

---

## 1. プロジェクト概要

段コミ（キックオフ）から納品までの開発フロー管理、リソース管理、Jira/Confluence連携、レポート出力を1つのツールに統合した管理アプリケーションです。

- **対象規模**: 約15名チーム、複数案件の並行管理
- **対象業務**: 自動車ECU向けHILS自動テスト開発
- **バージョン**: 0.1.0

---

## 2. 主な機能

### 実装済み

| カテゴリ | 機能 | 説明 |
|----------|------|------|
| 案件管理 | ステータス管理 | 計画中 / 実行中 / 保留 / 完了 / 中止 |
| メンバー管理 | プロパー/OS区分 | 日単価設定、スキル管理、有効/無効切替 |
| リソース配置 | 5ロールアサイン | 開発オーナー / 開発リーダー / マネージャー(OS) / 主担当(OS) / クロス者(OS) |
| リソース配置 | 未アサインアラート | OS（アウトソース）メンバーの未配置を検出 |
| 案件詳細 | 7タブ構成 | 基本情報 / 要望リスト / WBS / 見積・実績 / リスク / プロセス / アサイン |
| リスク管理 | 対策欄バリデーション | 対策欄必須、「TBD」「未定」等の曖昧記述を拒否 |
| プロセス | テーラリング | 16工程の実施/省略選択（省略理由記録） |
| 見積 | 工数比較 | 見積 vs 実績の工数比較（初回/修正/最終見積） |
| Jira連携 | 双方向同期 | Push（ローカル→Jira）/ Fetch（Jira→ローカル） |
| Confluence連携 | レポート出力 | Confluenceページへのレポート出力 |
| レポート | HTML出力 | 詳細 / サマリ / 週次 / 月次 / 年次レポート |

### 未実装（予定）

| 機能 | フェーズ |
|------|----------|
| ダッシュボード | Phase 4 |
| ガントチャート | Phase 4 |
| 工数削減効果の定量表示 | Phase 4 |
| OS人工請求管理 | Phase 4 |

---

## 3. 技術スタック

| 技術 | バージョン | 用途 |
|------|-----------|------|
| Python | 3.10+ | アプリケーション言語 |
| PySide6 | 6.6+ | GUIフレームワーク（LGPL準拠で商用利用可） |
| SQLite | 組込み | データベース（WALモードで同時アクセス対応） |
| MVVM | - | アーキテクチャパターン（View/ViewModel/Model分離） |
| Jinja2 | 3.1+ | HTMLレポートテンプレートエンジン |
| requests | 2.31+ | Jira/Confluence REST API通信 |
| cryptography | 41.0+ | PAT等の認証情報の暗号化保存 |
| PyYAML | 6.0+ | 設定ファイル読み込み |
| PyInstaller | 6.0+（dev） | 実行ファイルへのビルド |

---

## 4. 動作環境

| 項目 | 要件 |
|------|------|
| OS | Windows 10/11（主対象） |
| Python | 3.10 以上 |
| ランタイム | PySide6 が動作する環境 |

> **注意**: Linux等のヘッドレス環境では、PySide6のGUI起動に `libEGL.so.1` 等のシステムライブラリが必要です。
> CIサーバーやDockerコンテナでテストを実行する場合は、`libegl1` パッケージをインストールしてください。
>
> ```bash
> # Ubuntu/Debian の場合
> sudo apt-get install -y libegl1
> ```

---

## 5. セットアップ手順

### 1. リポジトリのクローン

```bash
git clone <リポジトリURL>
cd automotive-
```

### 2. 仮想環境の作成と有効化

```bash
python -m venv .venv
```

- **Windows**:
  ```cmd
  .venv\Scripts\activate
  ```
- **Unix (macOS/Linux)**:
  ```bash
  source .venv/bin/activate
  ```

### 3. 依存パッケージのインストール

開発環境の場合（テスト・リンター含む）:

```bash
pip install -e ".[dev]"
```

本番環境の場合:

```bash
pip install -r requirements.txt
```

### 4. データベースの初期化

```bash
python scripts/init_db.py
```

`./data/hils_manager.db` にSQLiteデータベースが作成され、16工程のプロセス定義がシードされます。

任意のパスを指定することも可能です:

```bash
python scripts/init_db.py /path/to/hils_manager.db
```

---

## 6. 起動方法

以下のいずれかで起動できます。

```bash
# エントリポイントコマンド
hils-manager

# モジュール実行
python -m hils_manager
```

起動するとメインウィンドウが表示されます。デフォルトのデータベースパスは `./data/hils_manager.db` です。

---

## 7. 設定（config.yaml）

データベースの保存先を変更する場合、`src/hils_manager/config.yaml` に設定ファイルを配置します。

```yaml
database:
  path: "./data/hils_manager.db"
```

### ネットワークドライブでDB共有する場合の例

チーム全員が同一のデータベースにアクセスする場合、ネットワークドライブ上のパスを指定します。

```yaml
# Windows UNCパス
database:
  path: "\\\\server\\share\\hils_manager\\hils_manager.db"

# Unix マウントポイント
database:
  path: "/mnt/shared/hils_manager/hils_manager.db"
```

設定ファイルが存在しない場合、または `database.path` が未設定の場合は、デフォルトの `./data/hils_manager.db` が使用されます。

> **ヒント**: プロジェクトルートに `config.yaml.example` サンプルファイルがあります。
> これを `src/hils_manager/config.yaml` にコピーして編集してください。
> `.gitignore` に `config.yaml` を追加して、認証情報を含む設定をリポジトリに含めないことを推奨します。

---

## 8. Jira連携の使い方

### PAT（パーソナルアクセストークン）の発行

Jira Data Center版の場合:

1. Jiraにログイン
2. 右上のプロフィールアイコン → **プロフィール** を選択
3. **パーソナルアクセストークン** タブを開く
4. **トークンを作成** をクリック
5. トークン名を入力（例: `HILS Manager`）し、作成
6. 表示されたトークンをコピー（再表示不可のため必ず控えてください）

### 接続設定

1. アプリの設定画面でJira接続情報を入力:
   - **Jira URL**: `https://your-jira-instance.example.com`
   - **PAT**: 発行したパーソナルアクセストークン
2. 接続テストで疎通を確認

### Push / Fetch 操作

| 操作 | 方向 | 説明 |
|------|------|------|
| **Push** | ローカル → Jira | WBSアイテムをJira課題として作成/更新 |
| **Fetch** | Jira → ローカル | Jira課題のステータス変更をローカルに反映 |

同期状態は `jira_sync_mappings` テーブルで管理され、競合（conflict）が発生した場合はユーザーに確認を求めます。

---

## 9. Confluence連携の使い方

### PAT設定

Jira連携と同様に、Confluence Data Center版のパーソナルアクセストークンを発行し、接続設定に入力します。

### レポート出力設定

1. **Confluence URL**: `https://your-confluence-instance.example.com`
2. **スペースキー**: レポートを出力するConfluenceスペースのキー（例: `HILS`）
3. **親ページID**: レポートを作成する親ページのID

### レポート出力手順

1. 案件詳細画面またはレポートメニューからレポート種別を選択
2. 出力先を「Confluence」に設定
3. 出力を実行すると、指定スペースの親ページ配下に新規ページが作成されます

---

## 10. 基本的な使い方

典型的な運用フローは以下の通りです。

```
1. メンバー登録
   └─ メンバー管理画面でチームメンバーを追加（プロパー/OS区分、日単価）

2. 新規案件作成
   └─ 案件一覧 → 新規案件ボタン → プロジェクトコード・名称・期間を入力

3. アサイン設定
   └─ 案件詳細 → アサインタブ → 5ロールにメンバーを配置

4. プロセステーラリング
   └─ 案件詳細 → プロセスタブ → 16工程から該当案件で実施する工程を選択

5. 要望/WBS/見積/リスク入力
   └─ 案件詳細の各タブで情報を入力

6. 実績入力
   └─ 見積・実績タブで実績工数を記録

7. レポート出力
   └─ HTML/Confluenceレポートを出力して関係者に共有
```

---

## 11. プロジェクト構成

### アーキテクチャ（MVVMレイヤー図）

```
┌──────────────────────────────────────────────┐
│  Views（PySide6 GUI）                         │
│  ├─ panels/      各画面パネル                 │
│  ├─ dialogs/     入力ダイアログ               │
│  └─ widgets/     再利用可能ウィジェット        │
├──────────────────────────────────────────────┤
│  ViewModels（表示ロジック・データ変換）         │
├──────────────────────────────────────────────┤
│  Services（ビジネスロジック）                   │
├──────────────────────────────────────────────┤
│  Repositories（データアクセス）                 │
├──────────────────────────────────────────────┤
│  Models（データクラス）                         │
├──────────────────────────────────────────────┤
│  Database（SQLite接続・マイグレーション）        │
└──────────────────────────────────────────────┘
```

### ディレクトリ構成

```
automotive-/
├── src/
│   └── hils_manager/
│       ├── __init__.py          # バージョン定義
│       ├── __main__.py          # エントリポイント
│       ├── app.py               # アプリケーション起動・DI
│       ├── constants.py         # Enum定義（ステータス、ロール等）
│       ├── database/
│       │   ├── connection.py    # SQLite接続管理（シングルトン、WAL）
│       │   ├── migrations.py    # スキーマバージョン管理
│       │   └── schema.sql       # DDL・シードデータ
│       ├── integrations/        # Jira/Confluence連携（実装中）
│       ├── models/              # データクラス（Project, Risk等）
│       ├── repositories/        # データアクセス層
│       ├── services/            # ビジネスロジック層
│       ├── viewmodels/          # 表示ロジック層
│       └── views/
│           ├── main_window.py   # メインウィンドウ
│           ├── panels/          # 各画面パネル
│           ├── dialogs/         # 入力ダイアログ
│           └── widgets/         # 共通ウィジェット
├── tests/                       # テストコード
│   ├── test_repositories/
│   └── test_services/
├── resources/
│   ├── icons/                   # アイコン
│   ├── styles/                  # QSSスタイルシート
│   └── templates/               # レポートテンプレート
├── scripts/
│   └── init_db.py               # DB初期化スクリプト
├── pyproject.toml               # プロジェクト設定・依存関係
├── requirements.txt             # 依存パッケージ一覧
└── config.yaml.example          # 設定ファイルサンプル
```

---

## 12. データベース

- **RDBMS**: SQLite（Python標準ライブラリに内蔵）
- **テーブル数**: 18テーブル
- **ジャーナルモード**: WAL（Write-Ahead Logging）
- **同時アクセス**: 約15名の同時利用に対応（`busy_timeout = 30000ms`）

### 主要テーブル一覧

| テーブル名 | 用途 |
|-----------|------|
| `team_members` | チームメンバー情報 |
| `projects` | 案件基本情報 |
| `project_assignments` | アサイン（メンバー×案件×ロール） |
| `process_definitions` | 工程マスタ（16工程） |
| `process_selections` | プロセステーラリング（案件別の工程選択） |
| `requirements` | 要望リスト |
| `wbs_items` | WBS作業項目 |
| `estimates` | 見積情報 |
| `time_entries` | 工数実績 |
| `risks` | リスク管理 |
| `deliverables` | 成果物管理 |
| `deliverable_reviews` | 成果物レビュー |
| `dankomi_records` | 段コミ（キックオフ）議事録 |
| `jira_sync_mappings` | Jira同期マッピング |
| `jira_sync_log` | Jira同期ログ |
| `outsource_billing` | OS人工請求情報 |
| `reports` | レポート生成履歴 |
| `app_settings` | アプリケーション設定（KVS） |

データアクセスは **Repository パターン** で統一されており、`BaseRepository` を継承した各リポジトリクラスがCRUD操作を提供します。

---

## 13. 開発者向け

### テストの実行

```bash
pytest tests/
```

カバレッジ付きで実行する場合:

```bash
pytest tests/ --cov=hils_manager --cov-report=html
```

> **注意（ヘッドレス環境）**: `pytest-qt` を利用するテストは、PySide6の初期化に `libEGL.so.1` が必要です。
> CI環境やDockerコンテナでは以下をインストールしてください:
>
> ```bash
> sudo apt-get install -y libegl1 libxkbcommon0
> ```

### コード整形・静的解析

```bash
# フォーマット（line-length=100, Python 3.10対象）
black src/ tests/

# リンター
flake8 src/ tests/

# 型チェック
mypy src/
```

### 開発用インストール

```bash
pip install -e ".[dev]"
```

これにより、`pytest`, `pytest-qt`, `pytest-cov`, `mypy`, `black`, `flake8`, `PyInstaller` がインストールされます。

---

## 14. 配布（ビルド）

本番配布は **PyInstaller の onedir 方式** を予定しています。

```bash
# 基本的なビルドコマンド（参考）
pyinstaller --name "HILS開発管理" --windowed src/hils_manager/__main__.py
```

> **注意**: `scripts/build_installer.py`（ビルド自動化スクリプト）は今後追加予定です。
> 現時点では上記の手動コマンドまたは `.spec` ファイルを作成してビルドしてください。

---

## 15. ロードマップ

| フェーズ | 内容 | 状態 |
|---------|------|------|
| Phase 1 | コアモデル・DB設計・基本CRUD | 完了 |
| Phase 2 | 案件詳細7タブ・リスクバリデーション・プロセステーラリング | 完了 |
| Phase 3 | プロセスワークフロー・成果物管理・レビューフロー | 開発中 |
| Phase 4 | ダッシュボード・ガントチャート・工数削減効果の定量表示 | 予定 |
| Phase 5 | Jira/Confluence本格連携・OS人工請求管理 | 予定 |
| Phase 6 | PyInstallerビルド・インストーラー自動化 | 予定 |
| Phase 7 | パフォーマンス最適化・UI/UX仕上げ | 予定 |

---

## ライセンス

本プロジェクトのライセンスについてはリポジトリのライセンスファイルを参照してください。
