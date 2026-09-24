# Dynamic Test Splitting 検証レポート（記事2）

検証日: 2026-09-11  
検証リポジトリ: [hidetaka-cci/ci-sandboxes](https://github.com/hidetaka-cci/ci-sandboxes)  
CircleCI プロジェクト: `gh/hidetaka-cci/ci-sandboxes`（パイプライン定義 `Chunk` / `.circleci/config.yml`）  
テストフレームワーク: Vitest 4.1.10（test atom 9件: 1 slow + 8 fast、`src/dts/`）

## 検証環境

| 項目 | 値 |
|---|---|
| test-suites.yml | `discover` / `run` / JUnit XML 出力のみ（`analysis` 行なし、LCOV 不要） |
| parallelism | 静的分割・動的分割比較時は `4`、ベースラインは `1` |
| テスト構成 | `slow.test.ts`（約9秒）+ `fast-01`〜`fast-08`（各 <1秒） |
| CI パイプライン定義 ID | `d88112d3-0b0d-4efe-96c4-a4720e3e42c7`（`Chunk`） |
| トリガー方法 | `POST /api/v2/project/gh/hidetaka-cci/ci-sandboxes/pipeline/run`（Git push だけでは validation 用パイプライン定義が先に起動し失敗するため） |

## ステップ1: test-suites.yml 作成と doctor

| チェック | 結果 |
|---|---|
| test-suite configuration exists | pass |
| detect test runner | pass |
| test-suite configuration is valid | pass |
| discover command can discover test atoms | pass（9 test atoms） |
| run command can run discovered test atoms | pass（9 test atoms） |
| file-mapper | skipped（`test-impact-analysis` 未設定） |
| analysis command can analyze test atoms | skipped（`test-impact-analysis` 未設定） |

- ローカル: `circleci testsuite doctor "ci tests"` → 全チェック pass
- CI: [Pipeline #111 / doctor](https://app.circleci.com/pipelines/gh/hidetaka-cci/ci-sandboxes/111/workflows/eadcf79f-6cb1-4e1a-8846-dabedb08611a/jobs/b2c779c5-8903-48bd-a2a3-83c4b193a7a9) → 全チェック pass

doctor 出力（セットアップ時・CI 実測文言）:

```
✓ test-suite configuration exists
✓ detect test runner
✓ test-suite configuration is valid

✓ discover command can discover test atoms
   - Discovered 9 test atoms

✓ run command can run discovered test atoms
   - Ran 9 test atoms
ø file-mapper command can map test atoms to files: check skipped: options.test-impact-analysis is not enabled

  Done! Ran 7 checks.
```

## ステップ2: parallelism=1 ベースライン

| 項目 | 値 |
|---|---|
| パイプライン | [#112](https://app.circleci.com/pipelines/gh/hidetaka-cci/ci-sandboxes/112) |
| ブランチ | `feature/dts-verify-p1` |
| test ジョブ | [test-p1 / job d42b11a8](https://app.circleci.com/pipelines/gh/hidetaka-cci/ci-sandboxes/112/workflows/0c03178d-cd9d-4ff2-b14a-ff1b5ad68368/jobs/d42b11a8-0e13-49da-af5f-eb8410375584) |
| テスト実行ステップ所要時間 | **13.7秒**（9 atom を単一ノードで直列実行） |

## ステップ3: parallelism=4・静的分割（dynamic-test-splitting なし）

| 項目 | 値 |
|---|---|
| パイプライン | [#113](https://app.circleci.com/pipelines/gh/hidetaka-cci/ci-sandboxes/113) |
| ブランチ | `feature/dts-verify-static` |
| test ジョブ | [test-static / job 800db85c](https://app.circleci.com/pipelines/gh/hidetaka-cci/ci-sandboxes/113/workflows/b0277727-936e-4930-9d87-5c97d629e5db/jobs/800db85c-5798-4100-b61e-182dca04c6fe) |
| `dynamic-test-splitting` | `false`（ログで確認） |

### ノード別テスト実行時間（Timings タブ相当: テストステップの wall clock）

| ノード | 配分 atom 数 | テストステップ時間 | バッチ数 |
|---|---|---|---|
| 0 | 2（fast-06, fast-02） | 3.5秒 | 1 |
| 1 | 3（**slow**, fast-05, fast-01） | **12.4秒** | 1 |
| 2 | 2（fast-07, fast-03） | 2.2秒 | 1 |
| 3 | 2（fast-08, fast-04） | 2.1秒 | 1 |

**最大−最小差: 10.3秒**（12.4秒 − 2.1秒）

ノード1のログ抜粋（slow が同バッチに固定配分）:

```
Running 3 test atoms
[2]    npx vitest run ... src/dts/slow.test.ts src/dts/fast-05.test.ts src/dts/fast-01.test.ts
[2] | Ran 3 test atoms in 10.409s
```

## ステップ4: dynamic-test-splitting 追加と doctor

`options.dynamic-test-splitting: true` 追加後の doctor（[Pipeline #114 / doctor](https://app.circleci.com/pipelines/gh/hidetaka-cci/ci-sandboxes/114/workflows/6b75e045-6413-410d-bc2e-8bb0d5336408/jobs/016c056a-28c0-4604-87ed-e6a17dd7d12d)）:

- チェック数は **7件のまま**（TIA 用の file-mapper / analysis は skipped）
- **DTS 専用の追加チェック項目は表示されなかった**（doctor ジョブは parallelism=1 のため）
- `dynamic-test-splitting: true` 設定時は Next Steps の「Enable dynamic test splitting」案内が **消える**（設定済みと判断）

## ステップ5: 動的分割 初回実行

| 項目 | 値 |
|---|---|
| パイプライン | [#114](https://app.circleci.com/pipelines/gh/hidetaka-cci/ci-sandboxes/114) |
| test ジョブ | [test-dynamic / job a976f423](https://app.circleci.com/pipelines/gh/hidetaka-cci/ci-sandboxes/114/workflows/6b75e045-6413-410d-bc2e-8bb0d5336408/jobs/a976f423-9f1a-4620-8e0a-1a6f630ffc74) |

### ノード別テスト実行時間（初回・学習フェーズ）

| ノード | テストステップ時間 | バッチ数 | 備考 |
|---|---|---|---|
| 0 | 4.3秒 | 3 | 複数バッチ `[1][2][3]` |
| 1 | 1.1秒 | 0 | テスト未配分 |
| 2 | 4.1秒 | 3 | 複数バッチ |
| 3 | **12.2秒** | 1 | `Previous timing data not found`、slow を含む単一バッチ |

**最大−最小差: 11.1秒**（静的分割より悪化）

ノード3のログ（タイミングデータ未存在）:

```
Previous timing data not found, test timings unavailable
...
Running 3 test atoms
[2]    npx vitest run ... src/dts/slow.test.ts src/dts/fast-05.test.ts src/dts/fast-01.test.ts
[2] | Ran 3 test atoms in 10.327s
```

ノード0のログ（複数バッチ配分の例）:

```
Running 1 test atoms
[1]    npx vitest run ... src/dts/fast-06.test.ts
[1] | Running 1 test atoms
[2]    npx vitest run ... src/dts/fast-02.test.ts
[2] | Running 1 test atoms
[3]    npx vitest run ... src/dts/fast-04.test.ts
[3] | Ran 3 test atoms in 3.297s
```

## ステップ6: 実行ログの複数バッチ配分

動的分割では、静的分割の「1ノード1バッチ」に対し、**同一ノード内で `[1]` `[2]` `[3]` と複数バッチに分割**される。初回実行ではノード0・2で3バッチ、ノード3は学習データ不足のため静的分割と同様の単一バッチ。

## ステップ7: 2回目実行（学習フェーズ比較）

| 項目 | 初回（#114） | 2回目（#116） |
|---|---|---|
| タイミングデータ | `Previous timing data not found` | `Fetching test timing data from job 541` / `Autodetected classname timings for 9 tests` |
| 最大−最小差 | 11.1秒 | **9.8秒** |
| slow の配分 | 3 atom 同バッチ（slow+fast×2） | **slow 単独バッチ** |

### 2回目のノード別テスト実行時間

| ノード | テストステップ時間 | バッチ数 | 配分 |
|---|---|---|---|
| 0 | 3.2秒 | 2 | fast-06+fast-03 → fast-05 |
| 1 | 4.0秒 | 2 | fast-04+fast-02+fast-08 → fast-07 |
| 2 | 1.8秒 | 1 | fast-01 |
| 3 | **11.7秒** | 1 | **slow 単独**（9.953秒） |

2回目ノード3のログ:

```
Fetching test timing data from job 541
Autodetected classname timings for 9 tests.
...
Running 1 test atoms
[2]    npx vitest run ... src/dts/slow.test.ts
[2] | Ran 1 test atoms in 9.953s
```

**学習フェーズの実在を確認**: 2回目でタイミングデータ取得後、slow が単独バッチに分離され、他ノードへの fast テスト再配分が進む。

## 検証後報告サマリー

### 静的分割 vs 動的分割（2回目）の最大−最小差

| 方式 | 最大 | 最小 | 差 |
|---|---|---|---|
| 静的分割（parallelism=4） | 12.4秒 | 2.1秒 | **10.3秒** |
| 動的分割 初回 | 12.2秒 | 1.1秒 | 11.1秒 |
| 動的分割 2回目 | 11.7秒 | 1.8秒 | **9.8秒** |

2回目の動的分割で **0.5秒** 偏り縮小。ジョブ全体のボトルノード（最遅ノード）は 12.4秒 → 11.7秒（**0.7秒短縮**）。初回は学習データ不足で静的分割と同等の偏りが残る。

### バッチ配分

| 方式 | ノードあたりバッチ数 |
|---|---|
| 静的分割 | 全ノード **1バッチ**（事前固定配分） |
| 動的分割 初回 | 0〜3バッチ（ノード0・2は3バッチ、ノード3は1バッチ） |
| 動的分割 2回目 | 1〜2バッチ（slow 単独化） |

### doctor の実際の文言

- セットアップ時・DTS 有効化後とも **同一の7チェック**（追加の DTS 専用チェック名は表示されず）
- `options.test-impact-analysis is not enabled` による skipped 文言は上記ステップ1のとおり
- `parallelism=1` + `dynamic-test-splitting: true`（[Pipeline #115 / doctor](https://app.circleci.com/pipelines/gh/hidetaka-cci/ci-sandboxes/115/workflows/a9c4e450-d987-488a-a541-278f53f0c721/jobs/9be1390c-20cd-4042-a033-679bc60a0e56)）でも **doctor は pass**（検証プランの「指摘される想定」と異なる）

### 学習フェーズ

- **初回と2回目で Timings 分布に観測可能な差あり**
- 初回: `Previous timing data not found, test timings unavailable`
- 2回目: `Fetching test timing data from job 541` + slow の単独バッチ化

## ハマりどころの検証結果

| 想定 | 実測 |
|---|---|
| parallelism=1 + dynamic のみ設定 → doctor 失敗 | **失敗せず pass**（ローカル・CI とも） |
| store_test_results と outputs.junit の不一致 | 一致（`test-reports`）で問題なし |
| 初回は履歴なしで静的分割相当 | **確認**（ノード3が slow+fast の単一バッチ） |

## 記事執筆への示唆

1. **LCOV 不要**は検証済み。`discover` / `run` / `outputs.junit` のみで動作。
2. **効果確認は2回以上の実行が必要**。1回だけでは「効果なし」と判断しないよう注意点に明記すべき。
3. doctor の DTS 追加チェックは、parallelism=1 の doctor ジョブでは見えない。記事では「test ジョブで parallelism>1 を設定し、doctor は基本セットアップ確認」と書くのが実態に合う。
4. Timings タブでは、静的分割時に「1ノードが9秒級・他が2秒級」の棒グラフ、動的分割2回目で「slow ノードのみ長く、他ノードが1〜4秒に収束」が期待される。

## パイプライン一覧

| # | ブランチ | 目的 | 結果 |
|---|---|---|---|
| 111 | feature/dts-verify-setup | ステップ1 doctor | succeeded |
| 112 | feature/dts-verify-p1 | ステップ2 ベースライン | succeeded |
| 113 | feature/dts-verify-static | ステップ3 静的分割 | succeeded |
| 114 | feature/dts-verify-dynamic | ステップ4–5 動的分割初回 | succeeded |
| 115 | feature/dts-verify-invalid | doctor 失敗確認 | succeeded（想定と異なる） |
| 116 | feature/dts-verify-dynamic | ステップ7 動的分割2回目 | succeeded |
