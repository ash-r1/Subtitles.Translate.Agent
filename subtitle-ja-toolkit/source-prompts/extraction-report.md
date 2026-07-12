# プロンプト抽出レポート

調査日: 2026-07-12
調査ブランチ: `main`（コミット `064743c 增加润色步骤` 時点）

## 1. 調査範囲と結論

`src/` 以下の全 C# ファイルを調査した。LLM へ送信されるプロンプトは
`Agents/Step1〜Step6` の 6 つの `GetPrompt()` がすべてであり、
それ以外に system prompt・再試行専用プロンプト・隠れた指示文は存在しない。

| ファイル | LLM プロンプト | 備考 |
|---|---|---|
| `Agents/Step1_DirectorAgent.cs` | あり (`GetPrompt`, L77) | 作品分析・スタイルガイド生成 |
| `Agents/Step2_GlossaryAgent.cs` | あり (`GetPrompt`, L67) | 用語集生成 |
| `Agents/Step3_TranslatorAgent.cs` | あり (`GetPrompt`, L240) | バッチ翻訳（スライディングウィンドウ） |
| `Agents/Step4_ReviewerAgent.cs` | あり (`GetPrompt`, L77) | 回訳による意味監査（Step3 から各バッチ直後に呼ばれる） |
| `Agents/Step5_PolisherAgent.cs` | あり (`GetPrompt`, L229) | 用語強制＋潤色 |
| `Agents/Step6_TimingAdjusterAgent.cs` | あり (`GetPrompt`, L153) | end_time 延長 |
| `Agents/AgentBase.cs` | なし | JSON 抽出（```json フェンス許容）と Token 記録のみ |
| `AgentEngine.cs` | なし | ワークフロー編成のみ |
| `Models/*` / `Utils/*` / `Program.cs` | なし | 入出力整形のみ |

再試行は「同一プロンプトの再送」であり（Step3 L68–98 など）、修正指示を追加する
再試行プロンプトは存在しない。

原文プロンプトは `original/extracted-prompts.md` に保存した。

## 2. パイプライン構造（元実装）

```
Step1 Director ──▶ Step2 Glossary ──▶ Step3 Translator ──(バッチ毎)──▶ Step4 Reviewer
                                            │ (全バッチ完了後)
                                            ▼
                                      Step5 Polisher ──▶ Step6 TimingAdjuster ──▶ SRT 出力
```

- バッチサイズ既定 20、前方文脈 2 行（訳付き）、後方文脈 2 行（原文プレビュー）
- 件数・ID 検証は C# 側で実施（件数不一致 → 例外 → 同一プロンプト再送）
- Step1/2 は字幕全文を 1 回で処理（`[開始秒]テキスト` 形式）

## 3. プロンプト別分析

### Step 1: Director（作品全体分析）

- **役割**: カテゴリ・トーン・文体指示・呼称方針・要約・背景の 6 フィールドを生成
- **入力変数**: `target_language`, `subtitle_content`
- **出力**: JSON オブジェクト 1 個（```json フェンス許容）
- **依存**: なし（起点）。出力は Step2/3/5 が Markdown 化して参照
- **問題点**:
  - `pronoun_rules` が自由記述 1 欄しかなく、人物×相手ごとの呼称を表現できない
  - 字幕表記方針（句読点・記号・改行）を決めるフィールドがない
  - 「JSON Only」と「Markdown タグは許す」が矛盾気味
  - Adult カテゴリの例示など、用途特化の残骸がある
- **残すべき設計**: 「翻訳せず方針だけ決める」役割分離、English keys + 対象言語 values
- **変更**: 日本語字幕表記方針（句読点・記号・ルビ・話者記号）、敬語の基本方針、
  語彙水準、避ける表現、視聴者想定を追加。人物関連は新設 Step2（人物分析）へ移管

### Step 2: Glossary（用語集）

- **役割**: character/location/terminology の対訳表生成
- **入力変数**: `global_style_guide`, `subtitle_content`, `target_language`
- **出力**: JSON（3 つの map）
- **依存**: Step1 の結果。出力は Step3/5 が参照
- **問題点**:
  - **「Must infer Gender」と断定を強制**しており、不明でも推測が事実化する
  - gender が he/she の訳し分け（中国語の 他/她）のためだけに設計されている
  - 人物の口調・一人称・敬語を持つ場所がない（`context_note` 1 欄のみ）
  - 中国語例（纽约・瑞文戴尔・威廉·布彻）がそのまま埋め込まれている
  - 参照側（Step3/5）の見出し名 `Character Mapping` / `Terminology Map` /
    `Terminology Table` が `ToMarkdown()` の実出力と揺れている
- **残すべき設計**: 一般語の抽出禁止、aliases の統合、空配列の扱い、
  category に応じた訳し分け戦略
- **変更**: gender に `gender_confidence` を追加し「不明なら unknown」を明文化。
  読み（`name_reading`）、公式訳の優先、確定訳/暫定訳の区別、evidence ID を追加。
  話し方情報は character profile（新 Step2）へ分離し、glossary は用語対訳に専念

### Step 3: Translator（バッチ翻訳）

- **役割**: スライディングウィンドウでバッチ翻訳
- **入力変数**: `target_language`, `global_style_guide`, `glossary`,
  `preceding_context`, `following_context`, `current_batch`,
  `batch_item_count`, `first_item_id`, `last_item_id`
- **出力**: JSON 配列（`id`, `original`, `initial_translation`）
- **依存**: Step1/2 の結果。出力は Step4→5→6 へ
- **問題点**:
  - 話者情報が一切なく、`pronoun_rules` の自由記述 1 欄だけで訳し分けを行う
  - 「代名詞 (It/He/They) の指示対象を明確化せよ」= 代名詞の表面化を促す設計。
    日本語のゼロ代名詞と正反対
  - Gender から he/she を選ぶ指示（中国語向け）
  - 前後文脈が既定 2 行と狭く、意味単位がバッチ境界で切れる
  - `original` をエコーさせる設計は検証に有効だが、原文改変の検出は C# 側任せ
- **残すべき設計**: 意味単位の復元→翻訳→再分割（Semantic Fusion）、
  前方=確定訳/後方=原文プレビューの非対称文脈、件数と ID 範囲の明示、
  用語集の強制適用
- **変更**: speaker map / character profiles / relationship map / phrase map を
  入力に追加。一人称・呼称・敬語の決定手順を明文化。ゼロ代名詞を原則化。
  `speaker_id` / `emotion` / `confidence` / `review_flags` の内部フィールドを追加

### Step 4: Reviewer（意味監査）

- **役割**: 回訳による意味検査（錯訳・漏訳・幻覚のみ、潤色禁止）
- **入力変数**: `target_language`, `current_batch`（{id, original, draft}）
- **出力**: JSON 配列（`status: PASS/FIXED`, `critique`, `final_translation`）
- **依存**: Step3 の各バッチ直後に実行
- **問題点**:
  - **出力件数が「恰好 20 条」と固定値でハードコード**。バッチが 20 件でない場合
    プロンプトと実件数が矛盾する（C# 側は実件数で検証するため、モデルが 20 件に
    合わせると必ず失敗する）
  - プロンプト本文が中国語で、「的」で終わる断片の例など**中国語前提の規則**
  - Chain of Thought の実行を明示指示（思考過程の開示要求に近い）
  - スタイルガイド・用語集を参照しないため、固有名詞の誤りを検出できない
  - 話者の取り違えを検査する材料がない
- **残すべき設計**: 意味監査と潤色の分離、意群跨行（enjambment）保護、
  「不完全な断片を補完するな」原則、PASS 時は draft と完全一致
- **変更**: 件数は `{{batch_item_count}}` 変数化。中国語規則を日本語規則
  （助詞止め・連用中止の許容）へ置換。CoT 開示要求を「短い構造化された検査根拠」
  へ変更。誤訳カテゴリを拡張（否定反転・数量・指示対象・話者・皮肉）。
  glossary と speaker map を入力に追加

### Step 5: Polisher（用語強制＋潤色）

- **役割**: Phase1 用語準拠 + Phase2 表現潤色
- **入力変数**: `target_language`, `glossary`, `style_instruction`,
  `pronoun_rules`, `preceding_context`, `current_batch`, `batch_item_count`
- **出力**: JSON 配列（`polished_text` は変更なし時 null）
- **依存**: Step3/4 の結果全件に対して実行
- **問題点**:
  - 「Correct pronouns (he/she) based on Gender」— 中国語向け設計の中核。
    日本語では代名詞をむしろ削るべき
  - 潤色と用語準拠と代名詞修正が 1 工程に混在し、潤色が意味や人物像を変えても
    検出する工程がない
  - 人物別の口調一貫性（一人称・語尾・敬語）を検査する観点が存在しない
  - `note` に「Use Chinese or Target Language」という中国語前提の指示が残る
  - 見出し `Terminology Map` は Step2 実出力の `Terminology Table` と不一致
- **残すべき設計**: 変更なし時 `null` を返す（差分最小化）、enjambment 保護、
  前バッチの磨き済み訳を文脈に使う、optimization_tag による変更理由の分類
- **変更**: 「口調・一貫性の監査」（新 Step6）と「日本語仕上げ」（新 Step7）に分割。
  用語強制は監査側へ、潤色側には意味・人物像・固定訳の変更禁止を明記

### Step 6: TimingAdjuster（表示時間調整）

- **役割**: end_time の延長のみ（Rushed 判定 → gap 充填）
- **入力変数**: `current_batch`（{id, text, start_time, end_time, next_line_start_time}）
- **出力**: JSON 配列（`action: KEEP/EXTEND`, `adjusted_end`, `reason`）
- **依存**: 最終訳確定後
- **問題点**:
  - 「10 chars / 1.5s / 1.2s / 50ms / 1-2 seconds」が**プロンプト内に固定値**で埋込
  - 「looks like a lot of characters」という曖昧な視覚基準（CPS 計算を放棄）
  - C# 定数 `ComfortableCps=5.0` 等が定義されながらプロンプトで未使用
  - 改行位置・一行文字数・分割バランスの検査がない（日本語字幕で最重要の観点）
- **残すべき設計**: start_time 不変・重なり禁止・安全バッファ、KEEP/EXTEND +
  理由の構造化
- **変更**: CPS・行長・最小表示時間などは設定ファイル
  （`subtitle-constraints.yaml`）から変数で注入。日本語の改行規則
  （助詞残し禁止・固有名詞/数値単位の分断禁止・意味の切れ目優先）を追加

## 4. 元実装から意図的に変えた点（横断）

1. **6 工程 → 9 工程へ再編**
   - 旧 Step1 → 新 Step1（Director）: 人物関連を分離し、字幕表記方針を追加
   - **新 Step2（話者・人物分析）を新設**: speaker map / character profiles /
     relationship map / address map / phrase map / unresolved list を生成。
     旧実装で `pronoun_rules` 1 欄と `gender` に潰れていた情報を構造化する
   - 旧 Step2 → 新 Step3（Glossary）: 用語対訳に専念、公式訳優先と暫定訳区別を追加
   - 旧 Step3 → 新 Step4（Translation）: 人物・関係・フレーズ情報を入力に追加
   - 旧 Step4 → 新 Step5（Semantic Review）: 固定 20 件を撤廃、日本語規則化
   - **新 Step6（口調・一貫性監査）を新設**: 旧実装に存在しない工程。
     一人称・呼称・敬語・語尾・決め台詞の人物内/人物間一貫性を検査
   - 旧 Step5 → 新 Step7（Polisher）: 用語強制を監査側へ移し、純粋な日本語仕上げに
   - 旧 Step6 → 新 Step8（Timing）: 固定値を設定ファイル化、改行規則を追加
   - **新 Step9（最終整合性監査）を新設**: 作品全体を通した表記・呼称・関係変化の検査
2. **gender 中心設計の廃止**: gender は文法情報の一つに格下げし、
   `gender_confidence` と「gender だけから口調を決めない」規則を全工程に明記
3. **代名詞方針の反転**: 「he/she を正しく訳せ」→「日本語ではゼロ代名詞を優先し、
   省略で曖昧になる場合のみ名前・役職で補う」
4. **中国語前提の除去**: 例文・規則・出力例をすべて英日ペアに置換
5. **固定件数の廃止**: すべて `{{batch_item_count}}` / `{{first_item_id}}` /
   `{{last_item_id}}` を参照
6. **CoT 開示要求の除去**: 旧 Step4 の「Audit Workflow (Chain of Thought)」を、
   判断手順（内部で行う）と、出力する短い構造化根拠（`critique` / `evidence_ids` /
   `confidence`）に分離
7. **Markdown フェンスの扱いを統一**: 全工程「フェンスなしの生 JSON のみ」に統一
   （エージェント実行では Write ツールでファイルに直接書くため、フェンス許容の
   曖昧さ自体を排除）
8. **実行主体の変更**: C# の逐次実行 → Claude Code のエージェント＋ファイル中間
   表現。各工程の入出力はすべて `work/` 以下のファイルに永続化し、再実行・調整を
   可能にする

## 5. 変数対応表

| 旧（C# 補間） | 新（標準変数） |
|---|---|
| `_context.Request.TargetLanguage` | `{{target_language}}` |
| `_context.FormattedSubtitle` | `{{subtitle_content}}` |
| `Step1_DirectorResult.ToMarkdown()` | `{{global_style_guide}}` |
| `Step2_GlossaryResult.ToMarkdown()` | `{{glossary}}` |
| `precedingContextStr` | `{{preceding_context}}` |
| `followingContextStr` | `{{following_context}}` |
| `currentBatchStr` / `draftJson` / `currentBatchJson` / `inputData` | `{{current_batch}}` |
| `batchData.CurrentBatch.Count` / `currentBatch.Count` | `{{batch_item_count}}` |
| `batchData.CurrentBatch.First().Index` | `{{first_item_id}}` |
| `batchData.CurrentBatch.Last().Index` | `{{last_item_id}}` |
| （なし・新設） | `{{source_language}}`, `{{subtitle_format}}`, `{{scene_context}}`, `{{speaker_map}}`, `{{character_profiles}}`, `{{relationship_map}}`, `{{phrase_map}}`, `{{subtitle_constraints}}`, `{{project_config}}` |
