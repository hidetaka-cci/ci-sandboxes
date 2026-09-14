# Smarter Testing 検証レポート（記事1: Test Impact Analysis）

検証日: 2026-09-11  
検証リポジトリ: [hidetaka-cci/ci-sandboxes](https://github.com/hidetaka-cci/ci-sandboxes)  
CircleCI プロジェクト: `gh/hidetaka-cci/ci-sandboxes`（パイプライン定義 `Chunk` / `.circleci/config.yml`）  
テストフレームワーク: Vitest 4.1.10（test atom 2件: `src/counter.test.ts`, `src/math.test.ts`）

## 検証環境

| 項目 | 値 |
|---|---|
| test-suites.yml | `name: ci tests`, LCOV analysis, `test-impact-analysis: true` |
| ローカル doctor | 全7チェック pass（discover 2 atoms, analysis 2 atoms） |
| CI パイプライン定義 ID | `d88112d3-0b0d-4efe-96c4-a4720e3e42c7`（`Chunk`） |

## ステップ1: doctor 検証

| チェック | 結果 |
|---|---|
| test-suite configuration exists | pass |
| detect test runner | pass |
| test-suite configuration is valid | pass |
| discover command can discover test atoms | pass（2 test atoms） |
| run command can run discovered test atoms | pass（2 test atoms） |
| file-mapper | skipped（全 atom がファイルのため不要） |
| analysis command can analyze test atoms | pass（2 test atoms） |

- ローカル: `circleci testsuite doctor "ci tests"` → 全チェック pass
- CI: [Pipeline #91 / doctor job](https://app.circleci.com/pipelines/gh/hidetaka-cci/ci-sandboxes/91) → 全チェック pass（ジョブ所要時間 14秒）

## ステップ2: analysis（1回目）と selection（2回目）

### 1回目 — main ブランチ（analysis + 全テスト実行）

| 項目 | 値 |
|---|---|
| パイプライン | [#91](https://app.circleci.com/pipelines/gh/hidetaka-cci/ci-sandboxes/91) |
| ブランチ | `main` |
| コマンド | `circleci testsuite run "ci tests"`（デフォルト: analyze=impacted, run=all） |
| test ジョブ所要時間 | **15秒**（02:04:45 → 02:05:00 UTC） |
| testsuite ステップ所要時間 | **5秒** |
| 発見 test atom 数 | 2 |
| 選択 test atom 数 | **2**（impact data 未存在のため全件選択） |
| スキップ test atom 数 | 0 |
| analysis 実行 | 2 test atoms を **2.1秒** で分析 |
| impact data | version 91 に更新 |

ログ抜粋:
```
Selecting all test atoms, no impact analysis available
Selected 2 test atoms, Skipped 0 test atoms
Analyzing 2 test atoms
Analyzed 2 tests in 2.105s
Updated test impact data in 12ms
```

### 2回目 — feature ブランチ（selection のみ）

| 項目 | 値 |
|---|---|
| パイプライン | [#93](https://app.circleci.com/pipelines/gh/hidetaka-cci/ci-sandboxes/93) |
| ブランチ | `feature/tia-verify-selection` |
| 変更ファイル | `src/math.ts`（コメント追加のみ） |
| コマンド | `circleci testsuite run "ci tests" --analyze-tests=none` |
| test ジョブ所要時間 | **20秒** |
| testsuite ステップ所要時間 | **3秒** |
| 発見 test atom 数 | 2 |
| 選択 test atom 数 | **1**（`src/math.test.ts`） |
| スキップ test atom 数 | **1**（`src/counter.test.ts`） |
| analysis 実行 | **なし** |

ログ抜粋:
```
- 1 test atoms impacted by modified files
Selected 1 test atoms, Skipped 1 test atoms in 2ms
Not running analysis
Not updating test impact data, analysis not enabled
```

### ステップ2 比較まとめ

| 指標 | 1回目（analysis） | 2回目（selection） | 差分 |
|---|---|---|---|
| 選択 test atom 数 | 2 | 1 | -50% |
| testsuite ステップ | 5秒 | 3秒 | -40% |
| analysis 時間 | 2.1秒 | 0秒 | 省略 |

初回 analysis は全 atom にカバレッジ計測が走るため testsuite ステップが長くなる（5秒 vs 3秒）。2回目以降は変更ファイルに関係する test atom だけが選択され、analysis 自体はスキップされる。

## ステップ2b: フィーチャーブランチでの impact data 更新

`--analyze-tests` のデフォルトは feature branch で `none`。明示的に `impacted` を渡すと impact data が更新されることを確認した。

### フラグなし（`--analyze-tests=none`、Pipeline #93）

```
Not running analysis
Not updating test impact data, analysis not enabled
```

### フラグあり（`--analyze-tests=impacted`、Pipeline #95）

| 項目 | 値 |
|---|---|
| パイプライン | [#95](https://app.circleci.com/pipelines/gh/hidetaka-cci/ci-sandboxes/95) |
| ブランチ | `feature/tia-verify-analyze` |
| 変更ファイル | `src/math.ts` |
| test ジョブ所要時間 | **16秒** |
| testsuite ステップ所要時間 | **4秒** |
| 選択 test atom 数 | 1 |
| analysis 実行 | 1 test atom を **1.2秒** で分析 |
| impact data | version 95 に更新 |

ログ抜粋:
```
Patching test impact data version: 95
Analyzing 1 test atoms
Running impact analysis for src/math.test.ts
Analyzed 1 tests in 1.235s
Updated test impact data in 10ms
```

**結論**: フィーチャーブランチではデフォルトで impact data は更新されない。`--analyze-tests=impacted` を明示すると、変更に関係する test atom だけ analysis され impact data が更新される。

## 想定外の挙動・注意点

1. **ci-sandboxes のデフォルト webhook パイプライン**: main への push 時、複数のパイプライン定義（validation 系）が同時に起動し config not found エラーになる。TIA 検証はパイプライン定義 `Chunk`（ID: `d88112d3-...`）を API で明示トリガーして実行した。
2. **full-test-run-paths の自動追加**: `test-impact-analysis: true` 有効化時、`.circleci/*.yml` と `package.json` 等が自動的に full-test-run-paths に追加される（ログの Suite Configuration に表示）。記事セクション5で説明する際の実測根拠になる。
3. **discover コマンド**: ローカル/CI とも `vitest` ではなく `npx vitest` が必要（PATH に vitest が無いため）。

## ステップ3・4（記事2・3向け、未実施）

本セッションでは記事1のステップ1・2・2bのみ実施。以下は記事2（Dynamic Test Splitting）・記事3（Auto-Rerun）の検証時に追記する。

- ステップ3: `parallelism > 1` + `dynamic-test-splitting: true` → Timings タブの分布
- ステップ4: 意図的失敗 + `max-auto-rerun` → rerun 表示

参考: 同一 org 内の `demo-magicpod-hotel-example-site` には DTS + TIA + analysis ジョブが既に構成済み（`.circleci/test-suites.yml` に `dynamic-test-splitting: true`）。

## 記事執筆向け実測値（引用候補）

- 初回 analysis（2 test atoms）: testsuite ステップ 5秒、analysis 部分 2.1秒
- selection（1/2 atoms 選択）: testsuite ステップ 3秒（analysis なし）
- feature branch + `--analyze-tests=impacted`: analysis 1 atom 1.2秒、impact data 更新あり
- `Selecting tests...` ログに選択理由が表示される（modified files: 1 atom など）
