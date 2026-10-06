# Strands Decider 配布方式比較 — 実施メモ

## 未確定の解消（本人判断）

| 項目 | 決定 |
|------|------|
| 計測リポジトリ / org | `gh/hidetaka-cci/ci-sandboxes` |
| B のレジストリ | `ttl.sh`（認証不要・TTL 7d）。恒久運用なら ECR/Docker Hub に差し替え |
| 許容時間 | 提案値どおり setup 追加 2 分以内（本計測後に再評価） |
| バージョン | `strands-decider==0.1.0` / `StrandsAgents/strands-decider-2B-hobson-v19` / base rev `b1485b2fa6dfa1287294f269f5fb618e03d52d7c` |

## 起動

```bash
# Step 0
circleci pipeline run --project gh/hidetaka-cci/ci-sandboxes \
  --definition-id <DEF_ID> --branch validation/strands-decider-distro-compare \
  --param phase=step0 --json

# Step 1
circleci pipeline run ... --param phase=prepare --json

# Step 2（時間帯をずらして 5 回）
circleci pipeline run ... --param phase=measure --json
```
