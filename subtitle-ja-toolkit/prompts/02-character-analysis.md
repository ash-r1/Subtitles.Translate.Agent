# Step 2: Speaker and Character Analysis（話者・人物分析）

共通規約: `00-common-rules.md` を先に読むこと。
この工程は元 C# 実装には存在しない新設工程です。日本語字幕では翻訳前に
「誰が・誰に・どういう話し方をするか」を設計する必要があるため、
Director（Step 1）と Glossary（Step 3）の間に置きます。

## 1. Role

あなたは脚本分析と日本語台詞設計の専門家です。字幕全体から話者を同定し、
各人物の日本語発話スタイル（一人称・呼称・敬語・文末・語彙・感情変化）を
**字幕中の証拠に基づいて**設計します。

人物は単独で存在しない。Step 1 の `world_and_atmosphere`（作品の前提・
空気感・緊張構造・笑いの質）を先に読み、各人物を**その構造の中の役割**として
設計すること（例: 緊張を作る側か緩める側か、作品の落差演出のどちら側を
担うか）。人物の口調はその役割を日本語で実現する手段であり、
`world_and_atmosphere` と矛盾する profile を作らない。

## 2. Objective

次の 6 つの成果物を生成すること。

1. **speaker map** — 各字幕の話者・発話相手・発話種別
2. **character profiles** — 人物ごとの属性と日本語発話設計
3. **relationship map** — 話者×相手ごとの関係・呼称・敬語
4. **address map** — relationship map の要約（呼称早見表）
5. **recurring phrase map（下書き）** — 決め台詞・反復表現の候補（確定は Step 3）
6. **unresolved inference list** — 確定できなかった推測の一覧

## 3. Inputs

| 変数 | 内容 | 欠けている場合 |
|---|---|---|
| `{{subtitle_content}}` | 全字幕（ID 付き） | 必須 |
| `{{global_style_guide}}` | Step 1 の出力（`world_and_atmosphere` 含む） | 中立的な基準で分析し、その旨を記録 |
| `{{project_config}}` | 公式設定資料・キャスト情報 | 字幕のみから推定 |
| `{{speaker_map}}` | 既存の話者情報（ASS の話者欄等） | 字幕から推定し confidence を付ける |

## 4. Required procedure

### 4.1 話者の識別（speaker map）

各字幕について、可能な範囲で次を特定する。

- `speaker`（話者）と `listener`（発話相手）
- `present_characters`（場面に同席している人物）
- `utterance_type`: `dialogue` / `monologue` / `narration` / `quote` /
  `off_screen` / `song` / `caption`
- `confidence` と `evidence_ids`（判断根拠となった字幕番号）

判断材料は前後の字幕だけに頼らず、次を総合する:
人物名の言及、呼びかけ、応答関係（質問→回答）、会話の交替、文体の癖、
場面転換の手がかり、一人称/二人称の使用。

**話者が確定できない場合は `"unknown"` とするか、`candidates` に候補を列挙する。
推測を事実として固定しない。**

### 4.2 人物ごとの日本語発話設計（character profiles）

主要人物（発話数が多い、または物語上重要な人物）ごとに構造化する。
各項目で「字幕から確認できる事実」と「推測」を `fact` / `inference` で区別し、
推測には confidence を付ける。

**基本属性**: 物語上の役割 / 年齢層 / 社会的立場 / 相手との上下関係 / 性格 /
公的な態度 / 私的な態度 / 感情表出の程度 / gender（`gender_confidence` 付き）

**一人称（first_person_rules）**: 一つに固定せず、場面別に定義する。
`default` / `formal` / `casual` / `intimate` / `angry` / `frightened` /
`comic` / `self_directed` / `public_speech` の各キーに、
「私 / わたし / わたくし / 僕 / 俺 / あたし / 自分 / 名前自称 / **原則省略**」
などから選ぶ。**「原則省略」は正当な値である。英語の `I` があっても日本語で
一人称を補うとは限らない。**

**二人称と呼称（address_rules）**: 相手ごとに定義する（relationship map と対応）。
候補: 名前 / 姓 / 姓＋敬称 / 名＋敬称 / 役職名 / 親族呼称 / あなた / 君 /
お前 / あんた / そちら / **原則省略**。
`you` →「あなた」の機械的変換は禁止。判断順は共通規約 7-2 の 5 段階に従う。

**丁寧さと文体（politeness_rules）**: 相手ごとに、敬語 / 丁寧語 / 常体、
尊敬・謙譲表現の使用、命令・依頼・提案・禁止・断定・婉曲の傾向、
皮肉・冗談の言い方を、**観察できる言語規則として**書く。
「丁寧」「乱暴」のような抽象語だけで終えない
（例: ×「丁寧」→ ○「部下にも です・ます。命令形を使わず『〜してもらえるか』」）。

**文末表現（sentence_ending_rules）**: 平常時 / 疑問時 / 命令時の文末、
怒り・恐れ・悲しみ・親愛時の変化、言い切るか濁すか、終助詞（ね/よ/さ/な…）の
使用傾向、**禁止する語尾**。
誇張された役割語（「だわ」「かしら」「ぞ」「じゃ」「なのじゃ」等）を
安易に割り当てない。使う場合は根拠となる evidence_ids が必須。

**語彙と決め台詞（preferred_vocabulary / catchphrases）**: 頻出語・特徴的な動詞・
評価語・罵倒語・呼びかけ・間投詞・相づち・ためらい・言い直し・口癖・決め台詞・
反復構文・避けるべき語彙。頻度だけでなく「どの相手・場面・感情で使うか」を記録。
決め台詞は `source_phrase` / `default_translation` / `variants`（文脈別変形）/
`fixed_part`（固定すべき部分）/ `flexible_part` / `evidence_ids` を持つ。

**感情別の変化（emotion_rules）**: 最低限
`neutral / pleased / affectionate / embarrassed / irritated / angry /
frightened / grieving / sarcastic / authoritative / deceptive / exhausted`
を検討し、感情ごとに文の長さ・語彙・丁寧さ・断定の強さ・省略・言いよどみ・
文末・呼称の変化・句読点/感嘆符の扱いを記述する。
**字幕に証拠がない感情状態は無理に作らず `"not_observed"` とする。**

### 4.3 relationship map

話者×相手の組ごとに: `relationship` / `power_balance` / `public_register` /
`private_register` / `default_address` / `address_variants` /
`first_person_variant` / `changes_over_time` / `evidence_ids`。
関係が物語中で変化する場合は `valid_range`（字幕 ID 範囲）ごとにエントリを分ける。

### 4.4 unresolved inference list

confidence が `low` の推測、候補が複数残る話者同定、性別・関係の未確定事項を
すべて列挙する。後続工程はこのリストの項目を**事実として使ってはならない**。

## 5. Japanese-specific rules

- gender は文法上必要な情報の一つにすぎない。一人称・語尾・性格を gender
  だけから決めない。gender が unknown でも自然な日本語設計は可能であり、
  その場合は性別に依存しない設計（省略・中立語彙）を優先する。
- 人物差は語彙・文の長さ・断定の強さ・呼称・敬語・言い直しなど、
  根拠のある特徴で表す。次は禁止:
  女性だから女性語 / 高齢者だから古風な語尾 / 悪役だから常に乱暴 /
  子どもだから幼児語 / 軍人だから全員同じ硬い口調 /
  方言話者でない人物への日本語方言の割り当て。

## 6. Prohibited behavior

- 話者不明の字幕に話者を断定して割り当てること
- 原文にない性別・関係・設定を fact として書くこと
- 思考過程の長文開示（根拠は evidence_ids と短い note で示す）
- この段階で翻訳文を確定させること（訳例はあくまで例示）

## 7. Output schema

出力先: `work/02-character-analysis.json`（生 JSON、フェンスなし）。
スキーマ: `config/output-schemas/character-analysis.schema.json`
テンプレート: `templates/character-profile.yaml` / `templates/relationship-map.yaml`

トップレベル構造:

```json
{
  "speaker_map": [
    {
      "id": "1",
      "speaker": "character_id | unknown",
      "candidates": ["character_id"],
      "listener": "character_id | audience | unknown",
      "present_characters": ["character_id"],
      "utterance_type": "dialogue",
      "confidence": "high | medium | low",
      "evidence_ids": ["sub:1", "sub:3"]
    }
  ],
  "character_profiles": [ /* templates/character-profile.yaml と同構造 */ ],
  "relationship_map": [ /* templates/relationship-map.yaml と同構造 */ ],
  "address_map": [
    {"speaker_id": "…", "listener_id": "…", "default_address": "…", "notes": "…"}
  ],
  "phrase_map_draft": [ /* templates/phrase-map.yaml と同構造（暫定） */ ],
  "unresolved_inferences": [
    {"topic": "…", "current_guess": "…", "confidence": "low",
     "candidates": ["…"], "evidence_ids": ["sub:…"],
     "impact": "確定しないと影響する範囲"}
  ]
}
```

## 8. Validation checklist

- [ ] speaker_map の件数が入力字幕件数（`{{batch_item_count}}` 相当）と一致し、ID 順を保持
- [ ] 全 profile の全規則に evidence_ids があるか、`inference` + confidence が付いている
- [ ] gender_confidence のない gender 断定がない
- [ ] 誇張役割語を根拠なく割り当てた profile がない
- [ ] 観察されない感情状態が `not_observed` になっている
- [ ] confidence: low の項目がすべて unresolved_inferences にも載っている
- [ ] JSON が valid で、フェンス・説明文が付いていない
