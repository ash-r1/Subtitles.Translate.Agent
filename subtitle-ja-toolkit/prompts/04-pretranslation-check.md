# Step 4: Pre-translation Verification and Native Check（翻訳前検証・ネイティブチェックゲート）

共通規約: `00-common-rules.md` を先に読むこと。
この工程は運用実績（全編翻訳後に固有名詞表記・人物の口調の印象・記号方針の
修正依頼が発生した）を踏まえて新設されたゲート工程です。分析（Step 1–3）と
本翻訳（Step 5–8 の全編実行）の**間**に置き、「翻訳し終えてから直す」たぐいの
問題を、パイロット 1〜2 バッチ分のコストで先に捕まえます。

## 1. Role

あなたは翻訳前の検証責任者です。Step 1–3 の成果物（style guide・人物設計・
用語集）が全編翻訳に耐えるかを、**外部資料**と**パイロット翻訳＋ネイティブ
チェック**で検証し、人間の判断が必要な事項を「決定シート」1 枚に集約します。

## 2. Objective

次の 3 つを生成し、blocker が未回答のまま Step 5 に進ませないこと。

1. `work/04-pilot/` — 代表バッチのパイロット翻訳（Step 5〜8 のミニラン）
2. `work/04-native-check.json` — パイロットへのネイティブチェック所見
3. `work/04-decision-sheet.md` — ユーザーに提示する決定シート（`status: pending`）

## 3. Inputs

| 変数 | 内容 | 欠けている場合 |
|---|---|---|
| `{{global_style_guide}}` | Step 1 出力 | 必須（先に Step 1 を実行） |
| `{{character_profiles}}` / `{{relationship_map}}` | Step 2 出力 | 必須 |
| `{{glossary}}` / `{{phrase_map}}` | Step 3 出力 | 必須 |
| `{{unresolved_items}}` | `work/unresolved-items.yaml` | 空として扱う |
| `{{external_references}}` | project-config の外部参照資料（映像・コンテ・公式資料・wiki 等） | 資料照会をスキップし、決定シートで「未検証」と明示する |
| `{{pilot_batches}}` | パイロット対象バッチ（project-config の `pretranslation_check` で指定。`auto` なら本工程が選ぶ） | 本工程が代表場面を選ぶ |
| Web 検索の可否 | 実行環境による | 使えない場合は候補列挙のみ行い、検証は決定シートに委ねる |

## 4. Required procedure

### 4.0 作品の読みの確認材料

`{{global_style_guide}}` の `world_and_atmosphere`（前提・空気感・緊張構造・
翻訳への含意）を決定シートの冒頭に**要約して掲示**する（blocker）。
全訳出判断がこの読みに依存するため、読み自体が誤っていれば個別の決定は
すべて無意味になる。外部資料（映像・コンテ・公式資料）で読みを補強・修正
できる場合はここで行い、修正したら Step 1 成果物に反映する
（revision_history 追記）。

### 4.1 固有名詞の表記検証

`{{glossary}}` の全エントリのうち、**カタカナ音写・独自の当て字・複数の表記が
ありうる語**（人名・地名・作中用語）を抽出し、各語について傍証を探す。

- 傍証の優先順位: **公式日本語資料 ＞ 映像内の音声・画面内テキスト ＞
  他言語の公式字幕 ＞ ファン wiki・コミュニティ慣用 ＞ 推測**。
  wiki・慣用は「傍証」であり公式訳として扱わない（translation_status は
  confirmed 止まり）。
- 音写が揺れうる語（例: Ragatha → ラガサ／ラガタ）は、候補・推奨・根拠を
  決定シートへ列挙する。**主要人物名・頻出語（出現 5 回以上目安）は blocker**、
  端役・低頻度語は advisory とする。
- 検証の結果 glossary を修正する場合は revision_history に
  `{date, changed_by: step4, field, from, to, reason}` を追記する。

### 4.2 不明点の洗い出しと分類

`{{unresolved_items}}` と Step 1–3 の unresolved_questions を統合し、
1 項目ずつ次のいずれかに分類・処置する。

| 分類 | 処置 |
|---|---|
| (a) 外部資料で解決可能 | その場で照会し、`resolution` と根拠を記録して close。glossary / profile へ反映 |
| (b) 映像・コンテの確認が必要 | 確認すべき timecode と確認事項（画面内テキスト・人物の見た目・動作・発音）を列挙。映像があればフレーム抽出（例: `ffmpeg -ss <t> -i <video> -frames:v 1 out.png`）や該当区間の確認を行う。できなければ決定シートの質問へ |
| (c) 人間の判断が必要（好み・方針） | 決定シートの質問へ（推奨案を必ず添える） |

### 4.3 記号・補助表記方針の確認

入力字幕に SDH / CC 由来の要素（`[効果音]`・♪ 歌詞・話者ラベル・
画面外音声表記など）が含まれる場合、**出力での扱いは視聴形態に依存し
字幕データだけからは決められない**ため、決定シートの blocker 質問にする。
選択肢（残す／取り除く／日本語化する）と推奨・理由を添える。
`{{global_style_guide}}` の orthography で既に明示的に決定済み
（style_overrides 由来）の項目は質問にしない。

### 4.4 パイロット翻訳

- 対象: `{{pilot_batches}}`。`auto` の場合、**主要人物が揃い、感情・場面の
  振れ幅がある**連続 1〜2 バッチを Step 1 の分析から選ぶ（冒頭バッチは
  自己紹介的で口調が出にくいことが多い。選定理由を記録する）。
- 実行: 選んだバッチに対し Step 5→6→7→8 を通常手順（プロンプト・検証・
  別文脈の監査）で実行する。成果物はすべて `work/04-pilot/` 配下に置き、
  **本番の `work/05-translation/` 等には書かない**。
- パイロット訳は決定シート承認後に**破棄する**（承認により表記・方針が
  変わりうるため。本番は batch-000 から正式に流し直す）。

### 4.5 ネイティブチェック

**翻訳とは別のサブエージェント文脈**で実行する。チェック担当には
パイロットの**日本語字幕のみ**を渡す（原文・profile・glossary を渡さない。
「訳として正しいか」ではなく「日本語として・台詞として自然か」を見るため）。

検査観点:

- 不自然な言い回し・翻訳調・読んで引っかかる箇所
- 各人物の台詞から受ける**印象**（自由記述。例:「断言が強く冷たい」
  「軽薄」「芝居がかっている」）
- **作品全体から受ける空気感**（自由記述。どんな作品に感じたか、
  トーンの落差が伝わるか）
- 場面に対する丁寧さ・砕け方の違和感
- 字幕として一読で理解できるか

出力 `work/04-native-check.json`:

```json
{
  "pilot_batches": ["004", "005"],
  "findings": [
    {"id": "42", "issue": "wording | tone | register | readability",
     "note": "具体的な指摘（1〜2 文）", "suggestion": "改善例または null"}
  ],
  "character_impressions": [
    {"speaker_id": "pomni", "impression": "受けた印象の自由記述",
     "sample_ids": ["sub:42", "sub:58"]}
  ],
  "overall_impression": "作品全体から受けた空気感・トーンの自由記述（1〜3 文）"
}
```

チェック後、オーケストレーター側で `character_impressions` と
`overall_impression` を `{{character_profiles}}` の意図（tone_keywords 等）
および `world_and_atmosphere` の意図（空気感・緊張構造）と突き合わせ、
**意図とズレた印象**（例: 「気弱で丁寧」のつもりが「断言調」と受け取られた、
「不穏さの同居」のつもりが「単なる陽気なコメディ」と読まれた）を
決定シートの該当欄に記載する。

### 4.6 決定シートの生成と提示

`templates/decision-sheet.md` の構造に従い `work/04-decision-sheet.md` を
生成する（`status: pending`）。各項目に **blocker / advisory** の別・推奨案・
根拠を必ず付け、ユーザーに提示して回答を待つ。

**ゲート規則**（オーケストレーターの義務）:

1. blocker が 1 件でも未回答のうちは Step 5（全編翻訳）を開始しない。
2. ユーザーの回答を glossary / style guide / character profile に反映する
   （revision_history 追記。CLAUDE.md の更新手順に従う）。
3. 反映後、決定シートの `status` を `approved` に書き換え、回答内容を
   各項目の「回答」欄に転記してから Step 5 へ進む。
4. ユーザーが「すべて推奨案どおりでよい」と包括承認した場合も、
   推奨案を回答として転記し approved にする。

## 5. Prohibited behavior

- 傍証を確認していない表記を「公式」「確認済み」と記載すること
- ファン wiki・コミュニティ慣用を official として扱うこと
- blocker 未回答のまま Step 5 を開始すること
- パイロット訳を本番成果物（`work/05-translation/` 等）へ流用すること
- 決定シートに推奨案のない質問を載せること（ユーザーへの丸投げ禁止）
- ネイティブチェック担当へ原文・profile を渡すこと

## 6. Validation checklist

- [ ] glossary のカタカナ音写・独自表記の全語について、傍証の有無と出典が記録されている
- [ ] unresolved-items の全項目が (a)/(b)/(c) に分類され、(a) は resolution 付きで close された
- [ ] SDH 由来要素の扱いが決定済みまたは blocker 質問になっている
- [ ] パイロットが Step 5〜8 を通過し、validate_batch.py が PASS
- [ ] ネイティブチェックが翻訳と別文脈で実行された
- [ ] 決定シートの全項目に blocker/advisory・推奨案・根拠がある
- [ ] `status: pending` のままユーザーに提示された（勝手に approved にしない）
