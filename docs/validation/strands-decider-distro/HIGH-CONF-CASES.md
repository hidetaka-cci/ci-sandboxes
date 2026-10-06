# 高確信度ケース再計測

前回 0/119 はモデル不能ではなく、**問いが弱かった**。分類・ルーティング・事実照合に直して測り直した。

Pipeline [#180](https://app.circleci.com/pipelines/github/hidetaka-cci/ci-sandboxes/180) `phase=cases` / job `high-conf-cases`（4m ではない、**1m29s**、offline C）。

## 結果

**17 回答中 7 件が確信度 ≥ 0.9（41%）。** 値が乗るケースは作れる。

| ケース | 家族 | 結果 | ≥0.9 |
|--------|------|------|------|
| Two plus two equals four | fact noul | p=**0.941** | はい |
| The sky is blue | fact noul | p=**0.929** | はい |
| The sky is green（青だと書いた state） | fact noul | p=0.139 | いいえ |
| sihamba ngokushesha の言語 | choice | **zulu 0.927** | はい |
| 二重課金の返金 intent | choice | **refund 0.980** | はい |
| payouts 失敗チケットの queue | choice | **payments 0.953** | はい |
| math.ts の diff の種類 | choice | **application_code 0.926** | はい |
| approval-demo.yml の種類 | choice | **ci_config 0.956** | はい |
| TIA 検証 md の種類 | choice | application_code 0.466 | いいえ |
| 公式 payouts デモ（urgency/team/score） | official | 0.818 / billing 0.672 / 0.472 | いいえ |
| What's the weather? の tool | tool | get_weather 0.523、has_city 0.202 | いいえ |
| touches_src / touches_circleci | noul パス有無 | 0.807 / 0.831 | いいえ |

## 何が効いたか

- **choice の各選択肢に説明を書く**（`billing — payments, invoices...`）。空文字ラベルは使わない。
- **「テストを回すべきか」ではなく「これは何の変更か」**。パス有無の noul より 3 択分類の方が 0.9 に乗る。
- 公式デモ文は公開 README どおりでも urgency は **0.82** で 0.9 未達。紹介に使うなら intent/routing/change-kind のほうが出る。

## 組み込みへの含意（更新）

- Decider が 0.9 を出せない、ではない。
- **「どの suite を回すか」を独立 noul で聞く設計は 0.9 に届かない。**
- CI に載せるなら、少なくとも今回通った形にする:  
  **change-kind = documentation | application_code | ci_config（説明付き choice）**  
  実 PR の docs 混在（pr-08）はまだ誤分類するので、本番前にラベル付き差分で再測定が必要。

Artifact: `docs/validation/strands-decider-distro/artifacts/high-conf/bench-out/high-conf-cases.json`
