# subtitle-ja-toolkit — 日本語字幕翻訳パイプライン

## このプロジェクトの目的

外国語（主に英語）字幕を**自然な日本語字幕**へ翻訳するための、
エージェント実行型のプロンプト・ツールキット。このリポジトリに元々あった
C# アプリの 6 段階パイプラインを、日本語字幕向けに 9 工程へ拡張し、
Claude Code / Cowork から直接実行できるファイル一式として再構成したもの。
元の C# 実装は抽出完了後に削除済み（git 履歴と `source-prompts/` に記録が残る）。

コマンド・スキルはリポジトリルートの `.claude/` にあり、相対パスは本ディレクトリ
（`subtitle-ja-toolkit/`）を基準とする。`.claude/` が使えない環境（Cowork 等）
でも、この CLAUDE.md と README.md の手順だけで全工程を実行できる。
各工程の詳細指示は `prompts/01`〜`09` にあり、実行時は該当ファイルを読み、
`{{variable}}` を実データで置換して従う。

## ファイルの置き場所

| 種別 | 場所 | 扱い |
|---|---|---|
| 入力字幕 | `input/`（例: `input/source.srt`） | **読み取り専用。絶対に変更しない** |
| プロジェクト設定 | `project-config.yaml`（`config/project-config.example.yaml` をコピー） | 実行前に用意 |
| 字幕制約 | `subtitle-constraints.yaml`（`config/subtitle-constraints.example.yaml` をコピー） | 実行前に用意 |
| 中間成果物 | `work/` | 各工程が生成・更新（下表） |
| 最終出力 | `output/`（例: `output/translated.srt`） | Step 8 統合後に生成 |

## 工程と入出力

実行順は 1→9。各工程は「読むファイル」だけを読み、「更新してよいファイル」
だけを書く。プロンプトは対応する `prompts/NN-*.md` を使う。

| 工程 | プロンプト | 読む | 更新してよい |
|---|---|---|---|
| 1 Director | `01-director.md` | input, project-config | `work/01-global-analysis.json` |
| 2 Character | `02-character-analysis.md` | input, 01, project-config | `work/02-character-analysis.json`, `work/scene-context.yaml`, `work/unresolved-items.yaml` |
| 3 Glossary | `03-glossary.md` | input, 01, 02, 公式資料 | `work/03-glossary.json`, `work/unresolved-items.yaml` |
| 4 Translate | `04-translate.md` | input, 01–03, constraints, 前バッチ確定訳 | `work/04-translation/batch-*.json` |
| 5 Semantic Review | `05-semantic-review.md` | 04 の当該バッチ, 01–03 | `work/05-semantic-review/batch-*.json` |
| 6 Voice Review | `06-voice-consistency-review.md` | 05 通過訳, 02, 03 | `work/06-voice-review/batch-*.json` |
| 7 Polish | `07-polish-ja.md` | 06 通過訳, 01–03 | `work/07-polish/batch-*.json` |
| 8 Timing | `08-timing-adjust.md` | 07 通過訳＋timecode, constraints | `work/08-timing/batch-*.json`, `output/translated.srt` |
| 9 Final Audit | `09-final-audit.md` | output 全件, 01–03, unresolved | `work/09-final-audit.json` |

Step 4〜7 はバッチ単位のパイプラインで、バッチごとに 4→5→6→7 を通してから
次のバッチへ進む（前方文脈に「磨き済み確定訳」を使えるようにするため）。
Step 8 は全バッチ確定後に実行する。

## 不変条件（全工程共通）

1. **元字幕を変更しない**: `input/` 配下は読み取り専用。
2. **ID と timecode を保持する**: ID は文字列として保持し、順序・欠番を変えない。
   timecode を変更できるのは Step 8 の `end_time` 延長のみ（`start_time` 不変・
   重なり禁止）。
3. **原文を改変しない**: `original` フィールドは常に入力の完全なエコー。
4. **件数検証**: 各バッチ工程の出力後、`item_count == items.length ==` 入力件数、
   ID 範囲・順序の一致を **必ず `scripts/validate_batch.py` で機械的に検証**する。
   不一致なら該当バッチを再実行。
5. **フォーマット**: 中間成果物は生 JSON（フェンスなし）。設定・テンプレートは
   YAML。字幕 I/O は **SRT / WebVTT**（`scripts/srt_tools.py` が両対応。
   `project-config.yaml` の `subtitle_format` で指定）。**ASS は未対応**のため、
   事前に `srt_tools.py convert` 等で SRT/VTT へ変換してから投入する。
   ASS 由来の話者欄情報がある場合は Step 2 の speaker map の初期値として使う。
   出力字幕の改行は Step 8 の `line_broken_text` を使う。
6. **低確信度の記録**: confidence: low の推測はすべて
   `work/unresolved-items.yaml` に記録する。後続工程はそれを事実として扱わない。
7. **人物設定を無断で確定しない**: 話者・性別・関係が不明な場合、`unknown` の
   まま進める。断定するには字幕内の証拠（evidence_ids）が必要。

## profile / glossary の更新手順

翻訳中（Step 4）や監査中（Step 6）に人物・用語の新情報を発見した場合:

1. その場では **profile / glossary を直接書き換えない**。
   Step 4 は `new_findings`、Step 6 は `profile_revision_candidates` に記録する。
2. バッチ完了ごと（または数バッチごと）に、蓄積した候補をレビューし、
   採用するものを `work/02-character-analysis.json` / `work/03-glossary.json` に
   反映する。
3. 反映時は必ず該当エントリの `revision_history` に
   `{date, changed_by, field, from, to, reason}` を追記する（変更履歴を残す）。
4. 反映した変更が**既に翻訳済みのバッチ**に影響する場合、影響範囲の ID を
   `work/unresolved-items.yaml` に記録し、Step 9 の検査対象とする
   （大きい変更なら該当バッチを 4〜7 で再実行する）。

**優先順位**: 公式訳（project-config の official_references）＞ glossary
（official > confirmed > provisional）＞ character profile ＞ 各工程の裁量。
glossary と profile が矛盾したら、作業を止めて矛盾を記録し、どちらかを
revision 手順で修正してから続行する。

## バッチ処理

Claude が一度に全字幕を扱えない場合（通常そうする）、
`project-config.yaml` の `batching` に従いバッチ処理を行う。

各バッチのプロンプトに含めるもの:

- 前方の**確定訳**（`preceding_context_lines` 行。Step 7 まで通った訳を優先）
- 現在の翻訳対象（`current_batch`）
- 後方の**原文 preview**（`following_context_lines` 行）
- 該当範囲の scene context（`work/scene-context.yaml` から）
- 登場人物 profile（当該バッチに登場する人物のみ抜粋してよい）
- relationship map（同上）・glossary・phrase map
- `batch_item_count` / `first_item_id` / `last_item_id`

**バッチ境界で文が切れる場合**（`review_flags: ["sentence_spans_batch"]` や
後方 preview で判明した場合）、その文の意味単位を含むまで文脈範囲を広げる
（`expand_to_sentence_boundary: true`）。

## サブエージェント運用

各工程は独立した文脈で実行できるため、サブエージェント（Task/Agent）に
委譲する。割り当ての既定（`project-config.yaml` の `agents` で上書き可）:

| 工程 | モデル | effort | 理由 |
|---|---|---|---|
| 1 Director | Opus | high | 全体像の把握と方針決定。1 回きりで影響が全工程に及ぶ |
| 2 Character | Opus | high | 最も推論負荷が高い（話者同定・人物設計）。品質が翻訳全体を決める |
| 3 Glossary | Sonnet | medium | 抽出中心。判断は 1–2 の成果物に依拠できる |
| 4 Translate | Sonnet | high | 品質と分量のバランス。難所（皮肉・関係変化の山場）だけ Opus に切り替えてもよい |
| 5 Semantic Review | Sonnet | medium | 意味照合はパターン化されている。翻訳と**別のエージェント文脈**で行うこと（自己審査を避ける） |
| 6 Voice Review | Sonnet | medium | profile との照合が中心。同じく翻訳と別文脈で |
| 7 Polish | Opus | medium | 日本語の質感の最終責任。差分は小さいが感度が要る |
| 8 Timing | Haiku | low | 文字数・CPS・改行の機械的検査。ロジック中心で安価に大量処理 |
| 9 Final Audit | Opus | high | 作品全体の横断検査。文脈量が最大 |

運用上の注意:

- Step 4 と Step 5/6 を**同一エージェントの同一文脈で続けて実行しない**
  （自分の訳を自分で審査すると検出率が下がる）。
- バッチ間の直列依存（前方確定訳）があるため、Step 4〜7 の**バッチ並列化は
  行わない**。並列化してよいのは Step 9 の検査項目別分割と、
  Step 2 の人物別 profile 深掘りのみ。
- 文字数計算・件数検証・SRT 入出力のような機械処理は LLM にやらせず、
  Python スクリプト（Bash 実行）で行う。判断だけをエージェントに残す。

## 失敗時の再実行

- **JSON が invalid / 件数不一致**: 同一工程・同一バッチを再実行する。
  再実行プロンプトには「前回の出力は件数が N 件で入力 M 件と不一致だった。
  入力と同数・同 ID・同順で出力し直すこと」を追記する。
- **工程の途中で中断した場合**: `work/` の該当ディレクトリを見て最後に完成した
  バッチを特定し、次のバッチから再開する（完成済みバッチは再実行しない）。
- **上流成果物（01〜03）を修正した場合**: 影響する下流バッチのみ 4〜7 を
  再実行する。どの範囲に影響するかは glossary/profile の evidence_ids から
  判定し、判断に迷ったら Step 9 を先に流して findings で特定する。

## クイックスタート（コマンドが使える環境）

```
/analyze-subtitles input/source.srt      # Step 1–3
/translate-subtitles                     # Step 4–7（バッチループ）
/review-subtitles                        # Step 8–9 と出力生成
/run-full-pipeline input/source.srt      # 上記すべて
```

`.claude/commands` が使えない環境では、上の「工程と入出力」の表の順に、
各 `prompts/NN-*.md` を読んで手動で実行する（README.md に詳細手順あり）。
