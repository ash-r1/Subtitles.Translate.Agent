# 検証用ケースブック

`samples/input/sample.srt`（自作の海上保安ドラマ風 30 行）に、日本語字幕で
問題になる 10 事例を埋め込んである。各事例について、不適切な直訳・改善訳・
判断根拠・検出すべき工程を示す。期待される中間成果物は `samples/expected/` にある。

登場人物（expected/02 の profile 要約）:

- **Reyes 艦長**（capt_reyes・女性 high）: 指揮官。簡潔な常体・命令形。
  部下を姓＋役職で呼ぶ → 終盤は Cole を「ダニー」と名で呼ぶ（関係変化）
- **Cole 少尉 / Danny**（ens_cole・男性 high）: 若手。公的には「自分/です・ます」、
  私的（Morgan 相手）には「俺/常体」
- **Okafor 機関長**（chief_okafor・男性 medium）: ベテラン。**怒っても敬語を
  崩さない**。決め台詞 "Steady as she goes."
- **Morgan**（op_morgan・**gender unknown**）: 通信士。軽口・常体
- **遭難者**（unknown）: 無線の声。話者確定不可

---

## 事例 1: 同じ `you` が省略・名前・役職・「君」・「お前」に分かれる

| 字幕 | 原文 | 不適切な直訳 | 改善訳 | 判断 |
|---|---|---|---|---|
| 4 | Can **you** play it back? | あなたはそれを再生できますか？ | 再生できるか | 部下への指示。二人称は省略（判断順①） |
| 9 | I need **you** on the forward deck | 私はあなたが前甲板に必要です | コール少尉 前甲板へ | 呼びかけ済みの相手。名指し＋省略 |
| 18 | **You** okay? **You** look pale | あなたは大丈夫？あなたは青ざめている | ダニー　大丈夫？　顔色悪いよ | 親しい同僚間。両方省略 |
| 19 | Worry about **yourself** | あなた自身を心配しなさい | お前こそ心配しろ | 対等で親しい男性の強がり。「お前」 |
| 20 | **you** were right | あなたが正しかった | 君が正しかった | 上官→年長の部下への労い。「君」 |
| 22 | Are **you** out of your mind? | あなたは正気を失ったのですか？ | 正気ですか | 叱責。省略（Okafor は敬語維持） |
| 30 | **You** too, Captain. | あなたもです、艦長 | 艦長も | 役職呼称で代替 |

- 適用した人物設定: relationship_map の各組の `default_address`
- 関連 prompt: `04-translate.md`（判断順序 4・6）、`00-common-rules.md` 7-2
- 自動検査: Step 6 `unnecessary_pronoun` / 「あなた」の残存を検出

## 事例 2: 同じ人物が公的/私的で一人称・敬語を変える（Cole）

- 原文: [10] "Aye, Captain." / [23] "The line was fouled, Chief!" （公的）
  [19] "I told you I'd be fine."（私的・Morgan へ）
- 不適切な直訳: 全部「了解です」調で統一（人物内で場面差が消える）
- 改善訳: [10]「了解しました」 [25]「はい 機関長」（公的・ですます）/
  [19]「大丈夫だって言っただろ」（私的・常体）
- 適用した人物設定: `first_person_rules: {formal: 自分/省略, casual: 俺}`、
  `politeness_rules`: 対上官=です・ます、対 Morgan=常体
- 関連 prompt: `02-character-analysis.md`（registerVariants）、`04-translate.md`
- 自動検査: Step 6 `register_scene`（場面と丁寧さの不一致）

## 事例 3: 怒っても敬語を崩さない人物（Okafor）

- 原文: [24] "I do not care if it was on fire. You will follow procedure."
- 不適切な直訳: 「燃えてたって知るか。手順に従え！」（怒り=乱暴と決めつけ）
- 改善訳: 「燃えていても同じです　手順には従ってもらいます」
- 適用した人物設定: `emotion_rules.angry.politeness: 敬語を崩さない`、
  `sentence_ending: 「〜してもらいます」で圧をかける`（evidence: sub:21,24）
- 判断理由: 原文も短縮形なしの "I do not care" / "You will" で統制された怒り
- 関連 prompt: `02-character-analysis.md`（emotion_rules）、`06-voice-consistency-review.md`
- 自動検査: Step 6 `emotion_mismatch`（乱暴化した訳を profile 違反として検出）

## 事例 4: 親しくなるにつれて呼称が変わる

- 原文: [9] "Ensign Cole" →（救助成功後）[29] "Nice work today, Danny."
- 不適切な直訳: 全編「コール少尉」で統一（変化の演出が消える）／
  逆に全編「ダニー」（規律が消える）
- 改善訳: [9]「コール少尉」→ [29]「よくやった ダニー」
- 適用した人物設定: relationship_map `changes_over_time`、
  `valid_range: sub:1-28 は姓＋役職 / sub:29- は名`
- 関連 prompt: `02-character-analysis.md` 4.3、`09-final-audit.md`（relationship_change）
- 自動検査: Step 9 が valid_range 境界前後の呼称切替を検査。
  「揺れ」ではなく「意図された変化」として findings にしないこと

## 事例 5: 決め台詞が複数回出る

- 原文: [8][28] "Steady as she goes, ma'am."
- 不適切な直訳: [8]「彼女が行くように安定して」（誤訳）、
  または 2 回で違う訳（「このまま直進します」/「安定航行です」）
- 改善訳: 両方「ようそろ」（操舵号令の定訳）＋敬意は文脈で
- 適用した人物設定: phrase_map `{source_phrase: "Steady as she goes",
  default_translation: "ようそろ", forbidden_variants: [直訳], evidence: sub:8,28}`
- 関連 prompt: `03-glossary.md`（phrase_map）、`09-final-audit.md`（catchphrase）
- 自動検査: Step 9 が phrase_map 全出現を文字列照合し揺れを検出

## 事例 6: 皮肉を逐語訳すると誤る

- 原文: [13] "Oh, great. A storm front. Just what we needed."
- 不適切な直訳: 「ああ、素晴らしい。前線だ。まさに我々に必要なものだ」
  （賞賛に読める）
- 改善訳: 「最高だね　前線か　ついてるよ」（Morgan の軽口として反語を保持)
- 判断理由: 発話意図=不満。日本語の反語表現で再現し、説明は足さない
- 関連 prompt: `04-translate.md` 手順 3、`05-semantic-review.md`（irony）
- 自動検査: Step 5 `error_category: irony`（字義訳を意味エラーとして検出）

## 事例 7: 一文が三つの字幕へ分割される

- 原文: [14] "If we cannot reach them before that front closes in," /
  [15] "every soul on that boat, and I mean every soul," /
  [16] "will be in the water by dawn."
- 不適切な処理: 各行を独立に完結させる（[14]「到達できなければ前線が閉じる」等）、
  または [16] の「夜明けまでに海に投げ出される」を [14] に先取り
- 改善訳: [14]「前線に追いつかれる前に到着できなければ」/
  [15]「あの船の全員が　ええ　一人残らずです」/ [16]「夜明けには海に投げ出されます」
- 判断理由: 文全体を復元してから、意味のまとまり・息継ぎで再分割。
  後続の内容語（海・夜明け）を先取りしない。話者（Okafor・敬語）を 3 行で統一
- 関連 prompt: `04-translate.md` 手順 1・7、`05-semantic-review.md`（跨行保護）
- 自動検査: Step 5 が補完・先取りを `cross_line` として検出

## 事例 8: 話者不明で断定を避けるべき例

- 原文: [5] "...anyone... engine's flooded... we can't hold..."（無線の声）
- 不適切な処理: speaker_map で「男性の漁師」等と断定し、口調を演出する
- 改善処理: `speaker: unknown, utterance_type: off_screen, confidence: low`。
  訳は中立に「…誰か…　機関室が浸水…　もう持たない…」
- 関連 prompt: `02-character-analysis.md` 4.1、`04-translate.md` 手順 2
- 自動検査: validate 時に unknown 行へ人物固有口調が適用されていないこと
  （Step 6 は profile なし話者をスキップし `skipped_no_profile`）

## 事例 9: 性別が不明でも自然な日本語にできる例（Morgan）

- 原文: [12] "Already on it."
- 不適切な処理: gender を勝手に確定し「もうやってるわよ」（女性語）や
  「もうやってるぜ」（男性語）を付与
- 改善訳: 「もうやってる」（性別に依存しない常体。人物差は軽口の速さで表現）
- 適用した人物設定: `gender: unknown, gender_confidence: low`、
  語尾規則は性別非依存に定義
- 関連 prompt: `02-character-analysis.md` 5、`06-voice-consistency-review.md`
  （gender_based_ending）
- 自動検査: Step 6 が「性別だけを根拠にした語尾」を検出

## 事例 10: `I` と `you` を訳文で省略した方が自然な例

- 原文: [19] "I told you I'd be fine. Worry about yourself."
- 不適切な直訳: 「私はあなたに私が大丈夫だと言いました。あなた自身を心配しなさい」
- 改善訳: 「大丈夫だと言っただろ　お前こそ心配しろ」
  （前半の I×2・you×1 はすべて省略しても発話者・相手が文脈で一意。
  後半のみ関係に合う「お前」で対比を出す — 事例 1 の「お前」例を兼ねる）
- 判断理由: 省略しても「誰が何を」は失われない（判断順①で省略可）
- 関連 prompt: `00-common-rules.md` 7-1、`04-translate.md` 手順 6
- 自動検査: Step 6 `unnecessary_pronoun`（残存した「私は/あなた」を検出）

---

## 事例と工程の対応（検出マトリクス）

| 事例 | 主担当工程 | 検出カテゴリ |
|---|---|---|
| 1, 10 | Step 4 予防 / Step 6 検出 | unnecessary_pronoun |
| 2 | Step 2 設計 / Step 6 検出 | register_scene |
| 3 | Step 2 設計 / Step 6 検出 | emotion_mismatch |
| 4 | Step 2 設計 / Step 9 検出 | relationship_change |
| 5 | Step 3 設計 / Step 9 検出 | catchphrase |
| 6 | Step 4 予防 / Step 5 検出 | irony |
| 7 | Step 4 予防 / Step 5 検出 | cross_line |
| 8 | Step 2 予防 / Step 6 保護 | speaker unknown |
| 9 | Step 2 予防 / Step 6 検出 | gender_based_ending |
