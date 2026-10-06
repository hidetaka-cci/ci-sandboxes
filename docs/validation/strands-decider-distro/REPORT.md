# Strands Decider 配布方式比較 — 検証報告

## 判定（結論）

| 方式 | 判定 |
|------|------|
| **A** 毎回 HF 取得 | 動作する。ジョブ全体の中央値 ~2.0 分 |
| **B** 独自イメージ | **難しい → 今回は不採用** |
| **C** restore_cache | **採用候補**。ジョブ全体の中央値 ~1.5 分。A より約 30 秒速い |

B を打ち切った理由:

1. **Spin-up だけで負けている** — 焼き込みイメージ（~3.9 GiB pull）に **約 2 分 20 秒**。A/C のジョブ全体より長い。
2. **オフライン読み込みが素直に成立しない** — Hub cache / Xet / `refs/main` / `$HOME` と `/opt` の配置など、プラン想定より実装が重い。
3. レジストリも一時 `ttl.sh` 頼みで、運用品質のイメージ配布まで含めるとさらにコストが乗る。

プランの採用ルール（判定一致かつ許容時間内で中央値最小）に照らし、**C を採用**する。

## 環境

| 項目 | 値 |
|------|------|
| Project | `gh/hidetaka-cci/ci-sandboxes` |
| Branch | `validation/strands-decider-distro-compare` |
| Pipeline definition | `verify-strands-decider-distro` (`85ff31e3-0144-416d-af88-efb0dc7b4b28`) |
| Resource class | Docker X-large |
| strands-decider | `0.1.0` |
| Decider Hub | `StrandsAgents/strands-decider-2B-hobson-v19` |
| Base | `Qwen/Qwen3.5-2B-Base` @ `b1485b2fa6dfa1287294f269f5fb618e03d52d7c` |

## Step 0（前提）

Pipeline [#160](https://app.circleci.com/pipelines/github/hidetaka-cci/ci-sandboxes/160) / job `step0-preflight`

| 項目 | 結果 |
|------|------|
| peak RSS | **~11.2 GB** → X-large 16 GB に収まる |
| オフライン読込 | 成功（ピン留め revision を prefetch 後 `HF_HUB_OFFLINE=1`） |
| `config.base_revision` | loader 上は `null` のまま。snapshot path でピンを確認 |

## Step 1（準備）

- C キャッシュ保存: 成功（`strands-decider-cache-{{ checksum versions.env }}`）
- B イメージ: ttl.sh へ push 自体はできたが、オフライン推論まで安定させられず打ち切り

## Step 2（本計測）— A/C を 3 回（並列ワークフロー）

プランの「5 回・時間帯ずらし」は未完了。方向性は 3 回で十分出たため、B 打ち切りに合わせてここで区切る。

### ジョブ壁時計（主要ステップ）

| Run | 方式 | Spin-up | pip / restore | bench | ジョブ合計（概算） |
|-----|------|---------|---------------|-------|-------------------|
| 1 | A | 4.5s | install 68s | 46s | **~2.0 min** |
| 1 | C | 1.8s | restore 40s | 45s | **~1.5 min** |
| 1 | B | **143s** | — | fail | spin だけで超過 |
| 2 | A | 2.6s | install 71s | 46s | **~2.0 min** |
| 2 | C | 6.3s | restore 35s | 52s | **~1.6 min** |
| 2 | B | **138s** | — | fail | spin だけで超過 |
| 3 | A | 2.1s | install 69s | 54s | **~2.1 min** |
| 3 | C | 4.3s | restore 40s | 47s | **~1.6 min** |
| 3 | B | **139s** | — | fail | spin だけで超過 |

### ベンチ内訳（中央値）

| 方式 | load | infer 小 | infer 大 | peak RSS |
|------|------|----------|----------|----------|
| A | 14.0s | 4.9s | 20.1s | ~11.2 GB |
| C | 4.9s | 5.1s | 24.5s | ~11.1 GB |

ボトルネック差は主に **A の pip install（~70s） vs C の restore_cache（~40s）**。推論時間は同程度。

### 判定結果の一致

A/C で small/large とも一致（例: small `noul=0.467`, risk≈1.17, suites→integration）。B は未計測。

### 許容時間（setup 追加 2 分）

A・C ともジョブ全体が約 1.5〜2.1 分で、提案の「追加 2 分」には収まる。

## 採用（配布方式）

**方式 C（restore_cache）を配布手段としては採用。**  
ただし続く確信度検証の結果、**dynamic config への組み込み自体は見送り**（詳細は `CONFIDENCE-REPORT.md`）。

フォローアップで実施済み:

- C に `HF_HUB_OFFLINE=1` と Decider revision ピンを追加
- 実 PR 17 件 × 質問再設計で確信度 ≥ 0.9 を測定 → **0/119**

## 参照

- Config: `.circleci/validation/strands-decider-distro/config.yml`
- ハーネス: `validation/strands-decider-distro/`
- Artifacts: `docs/validation/strands-decider-distro/artifacts/`
