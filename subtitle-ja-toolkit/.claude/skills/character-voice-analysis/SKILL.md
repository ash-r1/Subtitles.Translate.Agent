---
name: character-voice-analysis
description: 話者同定と人物の日本語発話設計（Step 2）＋用語集構築（Step 3）。speaker map・character profile・relationship map・glossary・phrase map を生成する。翻訳前の必須工程。
---

# Character Voice Analysis（Step 2–3）

「誰が・誰に・どういう話し方をするか」を字幕の証拠に基づいて設計するスキル。
日本語字幕の品質はこの成果物で決まる。

## 実行手順

1. `subtitle-ja-toolkit/prompts/00-common-rules.md`、
   `prompts/02-character-analysis.md`、`prompts/03-glossary.md` を読む。
2. Step 2: 全字幕と `work/01-global-analysis.json` から
   `work/02-character-analysis.json` を生成する
   （スキーマ: `config/output-schemas/character-analysis.schema.json`、
   構造の参考: `templates/character-profile.yaml` / `relationship-map.yaml`）。
   人物が多ければ speaker map 作成後、人物別の profile 深掘りを
   並列サブエージェントに分割してよい。
3. Step 3: 公式資料を確認してから `work/03-glossary.json` を生成する
   （スキーマ: `config/output-schemas/glossary.schema.json`）。

## 絶対規則

- 話者が確定できない字幕は `unknown` または候補一覧。断定しない。
- gender だけから一人称・語尾・性格を決めない。
- 「省略」は一人称・二人称の正当な値。`you`→「あなた」を既定にしない。
- 誇張役割語（だわ/かしら/じゃ 等）は evidence なしに割り当てない。
- 全規則に evidence_ids。証拠のない感情スタイルは `not_observed`。
- 公式訳 > 確定訳 > 暫定訳。区別を translation_status で明示する。
