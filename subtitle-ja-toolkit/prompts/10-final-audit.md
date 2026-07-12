# Step 10: Final Consistency Audit（最終整合性監査）

共通規約: `00-common-rules.md` を先に読むこと。
この工程は元 C# 実装には存在しない新設工程です。バッチ単位の工程（5〜9）では
検出できない**作品全体をまたぐ不整合**を最後に検査します。

## 1. Role

あなたは納品前の最終監査員です。全字幕・全中間成果物を横断して整合性を検査し、
修正候補を**影響範囲付きで**報告します。

## 2. Objective

作品全体を通して次を検査すること。

- 人名表記・固有名詞の揺れ（glossary との全件照合）
- 一人称・呼称・敬語の人物内一貫性（relationship の valid_range と
  `character_arc` の phase を考慮）
- 決め台詞・反復表現の統一（phrase_map との照合）
- 人物別語彙の一貫性（prohibited_vocabulary の混入）
- 時系列による関係変化が呼称に反映されているか
- punctuation・記号の作品内統一（orthography との照合）
- 数字・単位の表記統一（漢数字/算用数字、全角/半角）
- その他の表記揺れ（同語異表記: 「わかる/分かる」等）
- 未解決事項（unresolved-items）が放置されたまま断定訳になっていないか
- 低確信度（low confidence）の推測に依存した訳が flag 付きで残っているか
- **決定シートの決定事項の反映**（Step 4 の `work/04-decision-sheet.md` で
  確定した表記・記号方針が全編に適用されているか。例: 取り除くと決めた
  `[効果音]` 表記の残存、旧表記の取りこぼし）
- **印象ドリフト**（日本語のみを視聴者として通読し、各人物の台詞から受ける
  印象が profile の意図と、作品全体の空気感が `world_and_atmosphere` の意図と
  一致するか。例: 気弱設計の人物が断言調に読める、皮肉屋の台詞が弱腰に
  読める、落差が演出の作品が平坦なトーンに均されている。作品の途中で
  印象が**意図せず**変質していないか。`character_arc` で設計された変化は
  逆に「伝わっているか」を見る）

## 3. Inputs

| 変数 | 内容 | 欠けている場合 |
|---|---|---|
| 最終訳全件（`work/09-timing/` 統合結果 or 出力 SRT） | 必須 | — |
| `{{glossary}}` / `{{phrase_map}}` | 照合基準 | 該当検査をスキップし報告 |
| `{{character_profiles}}` / `{{relationship_map}}` / `{{speaker_map}}` | 照合基準 | 同上 |
| `{{global_style_guide}}` | orthography 基準 | 同上 |
| `templates/unresolved-items.yaml` の実体 | 未解決一覧 | 同上 |
| `work/04-decision-sheet.md` | Step 4 で確定した決定事項 | 該当検査をスキップし報告 |

全字幕が一度に読めない場合は、まず**機械的に検査可能な項目**
（固有名詞・数字・記号・決め台詞の文字列照合）を Grep 等のツールで全件検査し、
文脈依存の項目（敬語・呼称・関係変化）は人物別・関係別にまとめて検査する。

## 4. Required procedure

1. glossary の全エントリについて、最終訳での使用箇所を検索し、
   target と異なる表記の箇所を列挙する。
2. phrase_map の全エントリについて、出現箇所の訳を突き合わせ、
   allowed_variants 外の揺れを列挙する。
3. 人物ごとに発話を集め、一人称・語尾・敬語のドリフトを検査する。
   relationship map に `changes_over_time` がある組は、変化点（valid_range 境界）
   の前後で呼称が正しく切り替わっているかを確認する。
4. orthography・数字・記号の統一を検査する。
5. unresolved-items の各項目について、放置されたまま断定訳になっていないか
   確認し、残存するものを `remaining_unresolved` に列挙する。
   決定シートの blocker 決定事項（表記・記号方針）は Grep で全件照合する。
6. 印象ドリフト検査は**訳文の日本語のみ**（原文を伏せて）を人物別に通読して
   行う。可能なら別文脈のサブエージェントに委譲する（Step 4 のネイティブ
   チェックと同じ要領。ただしここでは profile の意図との照合まで行う）。
7. 発見事項ごとに修正候補を作るが、**局所修正が別の箇所との整合性を壊さないか**
   を必ず確認する（例: 呼称を直すと関係変化の演出が壊れる場合は、
   単純置換ではなく該当範囲全体の方針を提示する）。
8. 修正は自動適用せず、`severity` 付きの findings として報告する
   （適用の判断は実行者＝メインエージェント/ユーザーが行う）。

## 5. Japanese-specific rules

- 「揺れ」と「意図された変化」を区別する。呼称・口調の変化が relationship map
  の changes_over_time、profile の emotion_rules、または `character_arc` の
  phase 移行で説明できるなら、それは揺れではない（人物の成長・変化は
  主人公・メインキャラクターでは物語として典型的であり、矯正対象ではない）。
  findings にする前に必ず該当規則を確認する。逆に、arc が設計されているのに
  phase 移行が訳文に現れていない（全編同じ口調に均されている）ことも
  findings とする。
- 同語異表記は作品内で多数派に統一する提案を基本とし、人物の書き分け
  （教養差の演出等）が profile にある場合は例外とする。

## 6. Prohibited behavior

- 訳文の自動一括置換（提案のみ。適用は実行者の判断）
- 意図された変化（関係・感情由来）を「揺れ」として矯正すること
- 新しい訳語・新しい口調規則の発明（既存の glossary / profile が唯一の基準）
- 根拠（evidence_ids）のない findings

## 7. Output schema

出力先: `work/10-final-audit.json`（生 JSON、フェンスなし）。

```json
{
  "checked_items": ["glossary", "phrase_map", "first_person", "address",
                    "politeness", "orthography", "numbers", "spelling_variants",
                    "relationship_changes", "unresolved", "low_confidence",
                    "decision_sheet", "impression_drift"],
  "skipped_items": [{"item": "…", "reason": "入力欠如"}],
  "findings": [
    {
      "finding_id": "F-001",
      "category": "named_entity | catchphrase | first_person | address | politeness | vocabulary | orthography | number | spelling_variant | relationship_change | unresolved_left | low_confidence_dependency | decision_sheet_violation | impression_drift",
      "severity": "blocker | major | minor",
      "description": "1〜3 文",
      "affected_ids": ["sub:42", "sub:118"],
      "current_texts": {"42": "…", "118": "…"},
      "proposed_fix": "修正案（範囲方針の場合はその説明）",
      "consistency_risk": "この修正が影響しうる他の箇所。なければ null",
      "evidence_ids": ["sub:…"],
      "rule_ref": "glossary#capt_reyes | profile:… | style_guide.orthography.… "
    }
  ],
  "remaining_unresolved": [ /* unresolved-items のうち残存するもの */ ],
  "summary": {"total_findings": 0, "blocker": 0, "major": 0, "minor": 0}
}
```

## 8. Validation checklist

- [ ] glossary・phrase_map の全エントリを照合した（サンプリングした場合は明記）
- [ ] findings すべてに severity・affected_ids・rule_ref がある
- [ ] 意図された変化を findings にしていない（changes_over_time を確認済み）
- [ ] consistency_risk を各修正案で検討した
- [ ] 訳文を直接書き換えていない
- [ ] JSON が valid で、フェンス・説明文が付いていない
