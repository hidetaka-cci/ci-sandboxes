# 検証レポート: chunk CLI による CI job 失敗時タスク起動

- **検証日**: 2026-07-09
- **検証者**: hidetaka-cci
- **対象リポジトリ**: hidetaka-cci/ci-sandboxes
- **対象ブランチ**: validation/chunk-task-on-fail-20260708

---

## 1. 検証サマリー

| 主張 | 結果 | 備考 |
|------|------|------|
| 主張A: CI job 内で非対話実行できる | **確認済み** | `CIRCLECI_TOKEN` env var のみで動作 |
| 主張A4: success 時は on_fail が発火しない | **確認済み** | success-control ジョブで確認 |
| 主張B: Web UI に Chunk タスクとして出現する | **確認済み** | CLI 起動タスクが UI に表示 |
| 主張B: デフォルトプロバイダで BYO キー不要 | **確認済み（Web UI での目視確認）** | Anthropic キー未設定で完走 |

---

## 2. 事前準備

### 2-1. 認証設定

`chunk auth status` で CircleCI トークン・Anthropic API キーの両方が Valid であることを確認した。設定は `~/.config/chunk/config.json` に保存済み。

```
CircleCI   ✓ Valid（Config file）
Anthropic  ✓ Valid（Config file）
```

### 2-2. タスク定義 UUID の取得

**問題**: `chunk task config` はインタラクティブ専用（TTY 必須）のため非対話環境では使用不可。`.chunk/run.json` の `definitions` が空の状態では `chunk task run` がエラーになる。

**解決方法**: 以下の手順で UUID を取得した。

1. CircleCI Web UI の Agents 画面（`https://app.circleci.com/agents/...`）からチャットを直接実行
2. 発行された run ID（URL 末尾の UUID）で run 詳細を取得
3. レスポンスの `pipelineDefinitionId` フィールドが definition UUID

```bash
curl -H "Circle-Token: $CIRCLECI_TOKEN" \
  "https://circleci.com/api/v2/agents/runs/{run-id}"
# → { "pipelineDefinitionId": "3125aecb-d02a-4fa0-b113-39752e2f8b9a", ... }
```

**補足**: `--definition` フラグには名前の代わりに UUID を直接渡すことも可能（`.chunk/run.json` の `definitions` が空でも動作する）。

### 2-3. `.chunk/run.json` の設定

```json
{
  "org_id": "0ffedcab-0755-4ea2-a76e-7f8a0b082494",
  "project_id": "23a96b91-80ac-47b3-b0a1-8467a3ea2c92",
  "org_type": "github",
  "definitions": {
    "chat": {
      "definition_id": "3125aecb-d02a-4fa0-b113-39752e2f8b9a",
      "default_branch": "main"
    }
  }
}
```

### 2-4. CircleCI プロジェクト環境変数

CircleCI API（`POST /api/v2/project/{slug}/envvar`）で以下を登録した。

| 変数名 | 値 | 用途 |
|--------|-----|------|
| `CIRCLECI_TOKEN` | 個人 API トークン | chunk CLI の非対話認証 |
| `CHUNK_TASK_DEFINITION` | `chat` | `--definition` に渡す定義名 |

### 2-5. `.circleci/config.yml`

`.circleci/validation/chunk-task-on-fail.yml` をそのままコピーして `config.yml` として配置した。

---

## 3. 検証設定（config.yml 概要）

2つのワークフローを定義した。

| ワークフロー | ジョブ | 目的 |
|------------|--------|------|
| `chunk-task-on-fail` | `on-fail-trigger` | 意図的に失敗させ、`when: on_fail` で `chunk task run` を起動 |
| `chunk-task-success-control` | `success-control` | 成功時に `when: on_fail` が発火しないことを確認 |

`on-fail-trigger` ジョブの step 構成：

```
1. Checkout code
2. Install chunk CLI（GitHub Release から curl でインストール）
3. Intentionally fail          ← exit 1 で意図的失敗
4. Verify chunk auth (on_fail) ← CIRCLECI_TOKEN の存在確認 + chunk auth status
5. Trigger chunk task run (on_fail) ← chunk task run --definition ... --prompt ... --json
```

---

## 4. 実行結果

### パイプライン情報

- **パイプライン**: #57（id: `798bdb13-23b5-439c-b070-7481c5a6cf93`）
- **トリガー方法**: カスタム Webhook トリガー（POST `https://internal.circleci.com/private/soc/e/...`）

### ワークフロー結果

| ワークフロー | ステータス | 確認内容 |
|------------|-----------|---------|
| `chunk-task-on-fail` | **failed**（期待通り） | 意図的失敗後に on_fail step が発火 |
| `chunk-task-success-control` | **success** | on_fail step はスキップされた |

### `on-fail-trigger` ジョブ ステップ結果（ジョブ #424）

| ステップ | ステータス |
|---------|-----------|
| Install chunk CLI | success |
| Intentionally fail | **failed** |
| Verify chunk auth (on_fail) | success |
| Trigger chunk task run (on_fail) | **success** |

### `Trigger chunk task run` ステップの出力

```
Using definition: ****
{
  "runId": "8a09b5cc-1f98-4aa9-bbea-9cc72f426018",
  "pipelineId": "95b9d61b-1bce-40d8-b350-348407e01ec1"
}
```

- 定義名はログ上でマスク（`****`）される
- `pipelineId: 95b9d61b-...` は Chunk タスクのパイプライン（#58）と一致

### Chunk タスクパイプライン（#58）

| ワークフロー | ステータス |
|------------|-----------|
| `setup-workflow` | success |
| `chunk-task` | **success** |

CLI から起動した Chunk タスクが CircleCI Cloud 上で正常に実行された。

---

## 5. 確認事項の結論

### 主張A: CI job 内での非対話実行

**確認済み。**

- `CIRCLECI_TOKEN` 環境変数を設定するだけで認証が通る（`chunk auth set` は不要）
- CircleCI ジョブでは `CI=true` が自動設定されるため、インタラクティブプロンプトは抑制される
- `when: on_fail` の step として `chunk task run` を配置し、意図的失敗後に正常起動することを確認

### 主張A4: success 時の非発火

**確認済み。**

`success-control` ジョブ（成功で終了）では `when: on_fail` step が実行されず、ジョブは success のままとなった。

### 主張B: Web UI 可視性とプロバイダ

**確認済み（目視確認含む）。**

- CLI から起動した `runId` に対応する Chunk タスクが Web UI に出現した
- `pipelineId` の一致により CLI 起動タスクとの対応が取れることを確認
- Web UI の Agents チャット（BYO Anthropic キー未設定）で実行したタスクが完走しており、「CircleCI (Powered by Anthropic)」プロバイダでキー不要で動作することを目視確認

---

## 6. ハマりどころ・注意点

| 項目 | 内容 |
|------|------|
| Definition UUID の入手経路 | CLI では取得不可。Web UI でチャットを一度実行 → run 詳細 API の `pipelineDefinitionId` から取得 |
| `chunk task config` の制約 | TTY 必須のインタラクティブコマンド。CI 環境・非対話シェルでは使用不可 |
| `--definition` への UUID 直接渡し | `run.json` の `definitions` が空でも UUID フォーマット文字列をそのまま渡せば動作する |
| ログのマスク | `CHUNK_TASK_DEFINITION` の値はジョブログ上で `****` にマスクされる（CircleCI の env var マスク機能） |
| プロジェクトのパイプライン設定 | カスタムパイプラインが設定されている場合、`config.yml` が自動で使われるとは限らない。Webhook トリガーの設定内容を確認すること |
| `when: on_fail` のスコープ | 同一 job 内の step にのみ有効。workflow レベルで別 job を on_fail 起動する方式とは別 |

---

## 7. 成果物一覧

| ファイル | 内容 |
|---------|------|
| `.circleci/config.yml` | 検証用 CircleCI 設定（on_fail トリガー／success-control） |
| `.circleci/validation/chunk-task-on-fail.yml` | 同上のソース（検証用アーカイブ） |
| `.chunk/run.json` | definition UUID を含むプロジェクト設定 |
| `docs/chunk-task-run-setup.md` | chunk task run 実行前の準備手順書 |
| `docs/chunk-task-run-validation-report.md` | 本レポート |
