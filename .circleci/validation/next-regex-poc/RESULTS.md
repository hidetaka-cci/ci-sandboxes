# PoC: `circleci config validate --next` 検知漏れ修正の実機検証

**検証日**: 2026-07-07  
**CLI バージョン**: `0.1.38646+f96353c6 (homebrew)` (`circleci version` 出力)  
**作業ディレクトリ**: `.circleci/validation/next-regex-poc/`  
**実行コマンド形式**: `circleci config validate caseN.yml --next`

## 結果サマリー

| ケース | 使用CLIバージョン | コマンド実行結果（生ログ） | fail/pass | 期待通りか |
| --- | --- | --- | --- | --- |
| 1 | `0.1.38646+f96353c6` | `Error: config compilation contains errors: config compilation contains errors:`<br>`	- Error calling workflow: 'run'`<br>`	- Invalid regular expression: ^(?!I AM HERE).*$: Invalid pattern.`<br>`exit_code=255` | fail | はい |
| 2 | `0.1.38646+f96353c6` | `Error: config compilation contains errors: config compilation contains errors:`<br>`	- Error calling workflow: 'guarded'`<br>`	- Arguments referenced without declared parameters: parameters.something-falsy-by-default-but-sometimes-truthy`<br>`exit_code=255` | fail | **いいえ**（後述） |
| 3 | `0.1.38646+f96353c6` | `Error: config compilation contains errors: config compilation contains errors:`<br>`	- Error calling workflow: 'run'`<br>`	- Invalid regular expression: ^v(?!0\.).*$: Invalid pattern.`<br>`exit_code=255` | fail | はい |
| 4 | `0.1.38646+f96353c6` | `Error: config compilation contains errors: config compilation contains errors:`<br>`	- Error calling workflow: 'test'`<br>`	- Error calling job: 'build'`<br>`	- Invalid regular expression: ^(?!main).*$: Invalid pattern.`<br>`exit_code=255` | fail | はい |

### fail/pass の定義

- **pass**: `Config file at ... is valid.`（否定先読み等が検知されず通過 = 検知漏れ bug）
- **fail**: 上記以外（コンパイルエラー、`exit_code=255` 等）

## ケース別詳細

### ケース1: branches filter × 否定先読み（PR #1893 対応想定）

- **修正前（参考）**: `Config file at - is valid.`（Makoto 2026-06-30 報告）
- **今回**: `Invalid regular expression: ^(?!I AM HERE).*$: Invalid pattern.` で fail
- **stdin 実行** (`cat case1.yml \| circleci config validate - --next`): 同一結果

### ケース2: short circuit（PR #1863 対応想定）

- **修正前（参考）**: `and:` 左オペランド falsy により regex 未評価で pass（Makoto 2026-06-22 報告）
- **期待**: `(?!I AM SNEAKING INTO IT)` のコンパイルエラー
- **今回（Makoto 提示 YAML そのまま）**: パラメータ未宣言エラーで fail。**regex 検証に到達していない**。
- **stdin 実行**: 同一（パラメータ未宣言エラー）
- **`--next` なし** (`circleci config validate case2.yml`): 同一（パラメータ未宣言エラー）

#### ケース2 補足（Makoto YAML 以外 — 参考のみ）

`<< parameters.xxx >>` を `<< pipeline.parameters.xxx >>` に置換した `case2-pipeline-params.yml` では、コンパイルが通り **`Config file at case2-pipeline-params.yml is valid.`（pass, exit_code=0）**。short circuit 内の `(?!I AM SNEAKING INTO IT)` は検出されなかった。`--next` 有無とも同一。

→ Makoto 提示の `case2.yml` そのものでは short circuit 修正の有無を判定できない。パラメータ参照を修正してコンパイル可能にした場合、2026-06-22 指摘の検知漏れが残っている可能性がある。

### ケース3: filters.tags.only（PR #1863 対応想定）

- **今回**: `Invalid regular expression: ^v(?!0\.).*$: Invalid pattern.` で fail

### ケース4: when: matches: 直書き（回帰確認）

- **期待**: 修正前から fail（既存記事 JCF-158 で確認済み）
- **今回**: `Invalid regular expression: ^(?!main).*$: Invalid pattern.` で fail — 回帰なし

## 結論（事実のみ）

1. **ケース1・3**: 否定先読み regex が `--next` で検出された（fail）。2026-06-30 / 2026-06-22 指摘の当該パスについて、今回の CLI では検知漏れは再現しなかった。
2. **ケース4**: 従来通り fail。回帰なし。
3. **ケース2**: Makoto 提示 YAML では short circuit の regex 検証まで到達せず、**期待した検証は完了していない**。補足実験（`pipeline.parameters` 構文）では pass となり、short circuit 検知漏れが残る可能性がある。

**一般化禁止**: 上記は今回試した 4 ケース（+ ケース2 補足 1 件）の結果に限る。

## ファイル一覧

| ファイル | 内容 |
| --- | --- |
| `case1.yml` | branches `only` 否定先読み |
| `case2.yml` | short circuit（Makoto 提示そのまま） |
| `case2-pipeline-params.yml` | ケース2 補足（`pipeline.parameters` 構文） |
| `case3.yml` | tags `only` 否定先読み |
| `case4.yml` | `when: matches:` 回帰 |
| `RESULTS.md` | 本ファイル |
