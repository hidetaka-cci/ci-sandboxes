# job-groups / serial-group 検証用設定

記事1「GHA の直列化ガンバリズムを CircleCI job-groups で解く」の著者向け検証メモ用。

## ファイル構成

| ファイル | 検証 |
|---|---|
| `01-single-job-serial.yml` | 検証1: 単一ジョブ serial-group |
| `02-job-groups-serial.yml` | 検証2: job-groups + serial-group（核心） |
| `03-project-scoped-serial.yml` | 検証3: プロジェクトスコープ |
| `04-failure-unlock.yml` | 検証4: 失敗時ロック解放 |
| `05-compile-errors/` | 検証5: コンパイルエラー各ケース |
| `06-rerun-behavior.yml` | 検証6: rerun 全体波及 |

## ローカル実行

```bash
./scripts/validate-configs.sh          # 検証0 + 検証5
./scripts/run-cloud-validations.sh     # 検証1-4, 6（CircleCI クラウド）
```

## CircleCI プロジェクト

- 主: `gh/hidetaka-cci/ci-sandboxes`（pipeline definition: job-group）
- 副（検証3）: `gh/hidetaka-cci/vitest-test-splitting`
