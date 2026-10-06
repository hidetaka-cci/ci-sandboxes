# 確信度検証報告（質問再設計 × 実 PR diff）

## 判定

**dynamic config への組み込みは見送り。**  
確信度 ≥ 0.9 の回答は **0 / 119（0%）**。質問を作り直しても、このリポジトリの実 PR 群ではルーティングに使える水準に届かない。

## 実施内容

| 項目 | 内容 |
|------|------|
| Pipeline | [#178](https://app.circleci.com/pipelines/github/hidetaka-cci/ci-sandboxes/178) `phase=confidence` |
| 方式 | C（restore_cache）+ `HF_HUB_OFFLINE=1` |
| Decider | `StrandsAgents/strands-decider-2B-hobson-v19` @ `bb282d786bc251fd4e3068de3ada9ddbb38127cd` |
| Base | `Qwen/Qwen3.5-2B-Base` @ `b1485b2…`（refs/main ピン済み） |
| Diffs | 17 件（PR #1–12 + commit 5 件） |
| 質問 | behavior_change / risk + suites を 5 つの noul に分割（説明付き） |

C の再現性修正も同時に入れた（`versions.env` に `DECIDER_REVISION`、prefetch で refs/main ピン、offline executor）。Verify ステップは成功。

## 結果サマリ

| 指標 | 値 |
|------|-----|
| 回答数 | 119（17 diffs × 7 問） |
| 確信度 ≥ 0.9 | **0** |
| ≥ 0.8 | **0**（noul derived / risk とも） |
| ≥ 0.7 | noul derived: 0 / risk: 4 |
| noul derived 中央値 | 0.43（max 0.65） |
| risk confidence 中央値 | 0.68（max 0.76） |
| ジョブ時間 | 4m45s（load ~4.1s offline） |

### 質問別（derived / confidence）

| 質問 | confident@0.9 | 備考 |
|------|---------------|------|
| behavior_change | 0/17 | 多くが 0.5 前後 |
| risk | 0/17 | 最高でも 0.76 |
| need_unit | 0/17 | コード差分でやや高いが max~0.52 |
| need_smoke | 0/17 | |
| need_integration | 0/17 | |
| need_e2e | 0/17 | 方向は低め（妥当寄り）だが確信度不足 |
| need_config | 0/17 | config PR で p は上がるが derived < 0.64 |

方向性は一部もっともらしい（例: `pr-07` で need_unit/smoke 高め、`pr-02` で need_config 高め）が、**「0.9 未満ならフルテスト」ルールだと常にフルテスト**になる。

## 結論

1. **配布方式 C は成立**（オフライン + revision 固定も今回確認）。
2. **Decider を setup の判定器として使うのは、現状のモデル×この用途では精度（確信度）が足りない。**
3. 紹介・組み込みの前に必要なのは配布の最適化ではなく、別モデル／別プロンプト戦略／閾値緩和の再設計。緩和するなら「確信度」ではなく人間レビュー前提の弱いヒント用途に落とす必要がある。

Artifact: `docs/validation/strands-decider-distro/artifacts/confidence/bench-out/confidence-report.json`
