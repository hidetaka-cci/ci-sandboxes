# Same-path 振る舞い判定（確信度基準を choice に揃えた再計測）

レビュー 3 点は JSON と一致。その提案どおり、path-filtering では決まらない同パス差分を、説明付き choice と **choice.confidence ≥ 0.9** だけで測った。

Pipeline [#183](https://app.circleci.com/pipelines/github/hidetaka-cci/ci-sandboxes/183) `phase=same-path`（1m22s、offline C）。

## レビュー指摘の確認（前回 high-conf JSON）

1. noul `p≥0.9` は derived `|2p−1|` では 0.86 / 0.88。choice と同じ 0.9 に揃えると **7/17 → 5/17**。正しい。
2. CI 関連の change-kind は 3 件中 2 件。外れた documentation は効果最大クラス。正しい。
3. 通った change-kind はパスで決定できる。Decider の価値は同パスの振る舞い差。正しい。

## 今回の結果（11 件、人間ラベル）

| 指標 | 値 |
|------|-----|
| 正解 | **10/11（0.91）** |
| TS（src/*.ts） | **6/6** |
| YAML | 4/5（comment を structural と誤判定、c=0.208） |
| **confidence ≥ 0.9** | **0/11** |
| 最高確信度 | yml-new-job **0.794** |
| 危険なスキップ（cosmetic を 0.9 で断言し、実は behavioral） | 0 |

方向は当たる。0.9 では一度も自動実行できない。

## 判定

- path-filtering で足りる問い（md vs src vs .circleci）に Decider を使わない。
- path では決まらない問いでも、**0.9 で act without check は現状不可**。
- 紹介・組み込みは、確信度を下げてヒントにするか、見送り。

Artifact: `docs/validation/strands-decider-distro/artifacts/same-path/bench-out/same-path-behavior.json`
