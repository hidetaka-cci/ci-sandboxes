# Auto-Rerun Failed Tests 検証レポート（記事3）

検証日: 2026-09-11  
検証リポジトリ: [hidetaka-cci/ci-sandboxes](https://github.com/hidetaka-cci/ci-sandboxes)  
CircleCI プロジェクト: `gh/hidetaka-cci/ci-sandboxes`（パイプライン定義 `Chunk` / `.circleci/config.yml`）  
テストフレームワーク: Vitest 4.1.10（test atom 4件: counter / math / flaky / always-fail）

## 検証環境

| 項目 | 値 |
|---|---|
| test-suites.yml | `name: ci tests`, JUnit XML 出力, `max-auto-rerun: 3` |
| LCOV / TIA | 既存 TIA 検証の土台を流用（analysis 行は残すが、Auto-Rerun 検証ブランチでは `--analyze-tests=none`） |
| ローカル doctor | 全7チェック pass（discover 4 atoms） |
| CI パイプライン定義 ID | `d88112d3-0b0d-4efe-96c4-a4720e3e42c7`（`Chunk`） |

## ステップ1: test-suites.yml 作成と doctor

`.circleci/test-suites.yml` に `discover` / `run` / JUnit XML 出力を設定済み（TIA 検証の土台を拡張）。

| チェック | 結果 |
|---|---|
| test-suite configuration exists | pass |
| detect test runner | pass |
| test-suite configuration is valid | pass |
| discover command can discover test atoms | pass（4 test atoms） |
| run command can run discovered test atoms | pass（4 test atoms） |
| file-mapper | skipped |
| analysis command can analyze test atoms | pass |

- ローカル: `circleci testsuite doctor "ci tests"` → 全チェック pass
- CI: [Pipeline #104 / doctor job](https://app.circleci.com/pipelines/gh/hidetaka-cci/ci-sandboxes/104/workflows/9e008e68-338d-47d7-8cdd-fb6b827f859e/jobs/06bf6f8b-0845-4161-a99e-5169b3d9945d) → 全チェック pass

## ステップ2: JUnit XML 出力（LCOV なしで動作）

| 項目 | 確認結果 |
|---|---|
| `run` コマンド | `--reporter=junit --outputFile="<< outputs.junit >>"` で JUnit XML を出力 |
| LCOV | Auto-Rerun 検証では未使用（`--analyze-tests=none`）。analysis 行は test-suites.yml に残るが、記事3の読者手順としては LCOV 不要 |
| JUnit の test atom 属性 | `com.circleci.test-atom` プロパティが各 testcase に付与されることを確認 |

## ステップ3: max-auto-rerun: 3 追加

`options.max-auto-rerun: 3` を追加後、doctor が pass。CI ログでも `max-auto-rerun: 3` が testsuite 設定に反映されることを確認。

## ステップ4: ローカル testsuite run（flaky テスト）

`AUTO_RERUN_FLAKY_TEST=1 circleci testsuite run "ci tests" --analyze-tests=none --local`

```
Running 4 test atoms
Rerunning failed tests...
Running 1 test atoms  → src/auto-rerun-flaky.test.ts
Reran 1 test atoms in 1 attempts
Exit code: 0
```

初回失敗 → 1回 rerun → 最終 pass を確認。

## ステップ5–6: CI 実行（pass シナリオ）

| 項目 | 値 |
|---|---|
| パイプライン | [#104](https://app.circleci.com/pipelines/gh/hidetaka-cci/ci-sandboxes/104) |
| ブランチ | `feature/auto-rerun-verify-pass` |
| test ジョブ | [job 70e2ffe2](https://app.circleci.com/pipelines/gh/hidetaka-cci/ci-sandboxes/104/workflows/9e008e68-338d-47d7-8cdd-fb6b827f859e/jobs/70e2ffe2-f910-4c80-9a0c-2b0f9cff2a8a) |
| ジョブ outcome | **succeeded**（rerun 後にエラー抑制） |
| Tests タブ URL | [Tests tab](https://app.circleci.com/pipelines/gh/hidetaka-cci/ci-sandboxes/104/workflows/9e008e68-338d-47d7-8cdd-fb6b827f859e/jobs/70e2ffe2-f910-4c80-9a0c-2b0f9cff2a8a/tests) |

ログ抜粋:

```
Running 4 test atoms
Rerunning failed tests...
Running 1 test atoms → src/auto-rerun-flaky.test.ts
Reran 1 test atoms in 1 attempts in 1.06s
```

**Tests タブ相当データ（CLI `testresult list --all`）:**

| classname | name | 1回目 | rerun 後 |
|---|---|---|---|
| src/auto-rerun-flaky.test.ts | 2回目の attempt で成功する flaky テスト | failure | success |
| src/auto-rerun-flaky.test.ts | 常に成功するテスト（rerun 時にも再実行される） | success | success（再実行） |

ジョブは成功表示だが、Tests タブ（または testresult API）を見ると flaky テストの初回 failure と rerun 後 success が記録されている。

## ステップ7: max-auto-rerun 超過後の job 失敗

| 項目 | 値 |
|---|---|
| パイプライン | [#105](https://app.circleci.com/pipelines/gh/hidetaka-cci/ci-sandboxes/105) |
| ブランチ | `feature/auto-rerun-verify-fail` |
| test ジョブ | [job 0a181df1](https://app.circleci.com/pipelines/gh/hidetaka-cci/ci-sandboxes/105/workflows/05e97594-7d0a-45d7-ae99-3ecba4eef56c/jobs/0a181df1-4cbc-4d26-b5cf-f0c0ec54c876) |
| ジョブ outcome | **failed** |

ログ抜粋:

```
Running 4 test atoms
Rerunning failed tests...
Running 1 test atoms → src/auto-rerun-always-fail.test.ts  (rerun 1)
Running 1 test atoms → src/auto-rerun-always-fail.test.ts  (rerun 2)
Running 1 test atoms → src/auto-rerun-always-fail.test.ts  (rerun 3)
Failed rerunning 1 test atoms in 3 attempts in 3.232s
rerun attempt 1 failed
rerun attempt 2 failed
rerun attempt 3 failed
```

testresult API では同一テストが **4回**（初回 + rerun 3回）failure として記録。

## ステップ8: test atom 粒度

Vitest の `--filesOnly` により **1ファイル = 1 test atom**。

pass シナリオで `src/auto-rerun-flaky.test.ts` が rerun 対象になった際:

- rerun コマンドは **ファイル単位**（`src/auto-rerun-flaky.test.ts` のみ）で再実行
- testresult API 上、初回成功だった「常に成功するテスト」も rerun 後に **2回目の success レコード**が残る
- 初回 run では成功していた `counter.test.ts` / `math.test.ts` は rerun されない

→ atom 内の1 testcase が失敗すると、**同一 atom 内の他 testcase も再実行される**ことを確認。

## max-auto-rerun の値による挙動差

| max-auto-rerun | シナリオ | rerun 回数 | 最終 outcome |
|---|---|---|---|
| 1 | always-fail（CI #100 / ローカル） | 1回で打ち止め | job failed |
| 3 | flaky pass（CI #104） | 1回 rerun で pass | job succeeded |
| 3 | always-fail（CI #105） | 3回 rerun 後も fail | job failed |

## ハマりどころ（検証で確認）

1. **doctor と flaky テスト**: doctor の run チェックは auto-rerun を使わないため、常時失敗するテストをそのまま入れると doctor が fail する。検証では `AUTO_RERUN_FLAKY_TEST` / `AUTO_RERUN_FAIL_TEST` 環境変数でテストを有効化。
2. **ジョブ成功表示だけでは rerun に気づけない**: pass シナリオ（#104）ではジョブは succeeded だが、Tests タブ / testresult API で初回 failure が確認できる。
3. **Chunk パイプラインの手動トリガー**: webhook だけでは別パイプライン定義が反応する場合がある。TIA 検証と同様、`circleci pipeline run --definition-id d88112d3-...` で Chunk を明示的にトリガーした。

## Web UI スクリーンショットについて

Cloud Agent 環境から CircleCI Web App への OAuth セッションが取得できず、Tests タブの実画面スクリーンショットは未取得。代わりに上記パイプライン URL と CLI/API 出力（`/opt/cursor/artifacts/`）を証跡とする。

## 関連リンク

- [Auto rerun failed tests 公式ドキュメント](https://circleci.com/docs/guides/test/auto-rerun-failed-tests/)
- [Testsuite configuration reference（max-auto-rerun）](https://circleci.com/docs/guides/test/testsuite-configuration-reference/#max-auto-rerun)
- Pass Tests タブ: https://app.circleci.com/pipelines/gh/hidetaka-cci/ci-sandboxes/104/workflows/9e008e68-338d-47d7-8cdd-fb6b827f859e/jobs/70e2ffe2-f910-4c80-9a0c-2b0f9cff2a8a/tests
- Fail Tests タブ: https://app.circleci.com/pipelines/gh/hidetaka-cci/ci-sandboxes/105/workflows/05e97594-7d0a-45d7-ae99-3ecba4eef56c/jobs/0a181df1-4cbc-4d26-b5cf-f0c0ec54c876/tests
