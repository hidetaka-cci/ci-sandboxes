# chunk task run × on_fail 検証

`chunk task run` を CI job 失敗時に非対話起動し、Cloud Chunk タスクとして Web UI に現れることを確定するための最小プラン。

## ファイル

| ファイル | 用途 |
|---|---|
| `chunk-task-on-fail.yml` | 検証A（on_fail 起動）+ A4（成功時は発火しない） |
| `../../.chunk/run.json` | `chunk task config` 相当（org / project ID。definitions は空でも UUID 直指定可） |

## セットアップ（著者作業）

| # | 準備 | 完了条件 |
|---|------|---------|
| S1 | 本リポジトリ `gh/hidetaka-cci/ci-sandboxes` を CircleCI に接続 | 済み想定 |
| S2 | 組織で Chunk 有効化・**Allow Chunk tasks** ON・プロバイダ「CircleCI (Powered by Anthropic)」 | 設定画面で確認 |
| S3 | タスク定義 UUID を取得し `CHUNK_TASK_DEFINITION` に登録 | Web UI または `chunk task config` |
| S4 | `.chunk/run.json` をコミット済み（本 PR） | project_id が実行プロジェクトと一致 |
| S5 | `CIRCLECI_TOKEN`（個人 API トークン）をプロジェクト環境変数に登録 | job から参照可能 |

### config の有効化

```bash
cp .circleci/validation/chunk-task-on-fail.yml .circleci/config.yml
git add .circleci/config.yml
git commit -m "Enable chunk-task-on-fail validation config"
git push
```

または CircleCI のパイプライン設定で上記 YAML を参照する。

## 検証ステップ

### A: CI job 内での非対話起動

| # | 操作 | 確認 | 成果物 |
|---|------|------|--------|
| A1 | `chunk task run --help` 等で非対話手段を確認 | **済（PR 内コメント）**: `CIRCLECI_TOKEN` / `CIRCLE_TOKEN`、`CI=true` | help 出力 |
| A2 | パイプライン実行 → Install chunk CLI step | インストール成功 | job ログ |
| A3 | `on-fail-trigger` ジョブ | on_fail step が run ID / pipeline ID（`--json`）を出力 | step ログ |
| A4 | `success-control` ジョブ | on_fail step がスキップされ成功 | job ログ |

### B: Web UI 可視性とプロバイダ

| # | 操作 | 確認 | 成果物 |
|---|------|------|--------|
| B1 | プロバイダ設定・BYO キー未設定 | 前提確認 | スクショ |
| B2 | A3 の run ID / pipeline ID で Chunk タスク一覧を検索 | CLI 起動タスクが UI に出現 | スクショ |
| B3 | Task logs を開く | ログ閲覧可 | スクショ |
| B4 | プロバイダ / トークン枠消費 | BYO キーなしで完走したか | ログ or 設定画面 |

## スクリーンショット取得リスト

1. Chunk 設定（プロバイダ = CircleCI (Powered by Anthropic)、キー未設定）
2. `on-fail-trigger` の on_fail step ログ（run ID / pipeline ID）
3. Chunk タスク一覧に CLI 起動タスク
4. 当該タスクの Task logs

## ハマりどころ

- `chunk task config` は TTY 必須。CI では `CHUNK_TASK_DEFINITION` に UUID を直接渡す。
- `when: on_fail` は **job 内 step** のみ。workflow 別 job 起動とは別。
- `.chunk/run.json` の `project_id` と実行プロジェクトの不一致に注意。
- Chunk Beta の日次トークン上限（40万/日）に注意。

## A1 結論（コード側で先に確定）

| 項目 | 内容 |
|------|------|
| トークン | `CIRCLECI_TOKEN` または `CIRCLE_TOKEN` |
| 非対話 | `CI=true`（CircleCI が自動設定） |
| 出典 | `chunk task run --help`, [chunk-cli docs/CLI.md](https://github.com/CircleCI-Public/chunk-cli/blob/main/docs/CLI.md) |
