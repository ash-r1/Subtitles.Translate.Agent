---
description: 字幕の作品分析＋翻訳前検証（Step 1–4）— スタイルガイド・人物設計・用語集を生成し、決定シートを提示
argument-hint: <字幕ファイルパス> [project-config.yaml のパス]
---

# /analyze-subtitles — 分析＋翻訳前検証フェーズ（Step 1–4）

> **基準ディレクトリ**: 本コマンド内の相対パス（`prompts/` `scripts/` `config/` `templates/` `work/` `input/` `output/` `project-config.yaml` 等）はすべて `subtitle-ja-toolkit/` を基準とする。最初に `cd subtitle-ja-toolkit` してから作業すること。


対象字幕: $ARGUMENTS（未指定なら `project-config.yaml` の `paths.input_subtitle`）

必ず `subtitle-ja-toolkit/CLAUDE.md` と `subtitle-ja-toolkit/prompts/00-common-rules.md`
を先に読むこと。

**シリーズモード**（`project-config.yaml` の `series.enabled: true`）: 下の手順を
`series.episodes` の全話を対象に **1 回だけ**実行する（Step 1–4 はシリーズ共有）。
各話を parse して結合・サンプリングした字幕を Step 1–3 に渡し、成果物は
`work/` ではなく `work/_shared/`（`01`〜`03`・`scene-context`・`unresolved-items`・
`04-*`）に書く。Step 1 は全話をサンプリングして読み、読んだ範囲を
`analysis_coverage` に記録する。evidence の id は `ep02/sub:45` 形式。決定シートは
シリーズで 1 枚、パイロットは代表エピソード（`series.priority_episodes` 優先）から
選ぶ。詳細は CLAUDE.md「シリーズ（複数ファイル）運用」。

## 手順

1. **準備**
   - `project-config.yaml` / `subtitle-constraints.yaml` を読む。なければ
     `config/*.example.yaml` からコピーして既定値で作成し、ユーザーに知らせる。
   - `python3 scripts/srt_tools.py parse <字幕>` で `work/source.json` を生成する
     （入力字幕は読み取り専用。以後 JSON を使う）。
   - `work/` と `work/unresolved-items.yaml`（`templates/unresolved-items.yaml`
     から）を用意する。

2. **Step 1: Director** — サブエージェント（既定: Opus / effort high）に
   `prompts/01-director.md` の指示と字幕全文を渡し、
   `work/01-global-analysis.json` を書かせる。
   スキーマ `config/output-schemas/global-analysis.schema.json` で検証する。

3. **Step 2: Character Analysis** — サブエージェント（Opus / high）に
   `prompts/02-character-analysis.md` と字幕全文・Step 1 結果を渡し、
   `work/02-character-analysis.json` と `work/scene-context.yaml` を書かせる。
   speaker_map の件数が字幕件数と一致することを確認する。
   人物数が多い場合は、まず speaker_map と人物リストを作らせ、
   主要人物ごとの profile 深掘りを**人物別に並列サブエージェント**へ分割してよい。

4. **Step 3: Glossary** — サブエージェント（Sonnet / medium）に
   `prompts/03-glossary.md` と字幕・Step 1/2 結果・公式資料
   （`official_references`）を渡し、`work/03-glossary.json` を書かせる。

5. **中間処理**
   - 各出力の confidence: low 項目を `work/unresolved-items.yaml` へ転記する。
   - Step 3 の `conflicts` があれば Step 2 との矛盾をユーザーに報告する。

6. **Step 4: 翻訳前検証・ネイティブチェックゲート** —
   `prompts/04-pretranslation-check.md` に従う
   （`pipeline.enable_pretranslation_check: false` ならスキップして 7 へ）。
   - 固有名詞表記の傍証探索（`external_references` の映像・コンテ・公式資料・
     wiki、必要なら Web 検索）と unresolved-items の解決試行を行う
     （オーケストレーター: Opus / high）。
   - 代表 1〜2 バッチのパイロット翻訳（Step 5→6→7→8 のミニラン、成果物は
     `work/04-pilot/` のみ）を実行し、**別文脈のサブエージェント**（Opus /
     medium）に日本語のみのネイティブチェックをさせる
     （→ `work/04-native-check.json`）。
   - 結果を `work/04-decision-sheet.md`（`templates/decision-sheet.md` 準拠、
     `status: pending`）に集約する。

7. **報告とゲート**
   - 生成物の要約（人物数・関係数・用語数・未解決数・解決済み数）と
     **決定シートの内容**（作品の読み・blocker 質問・口調サンプル・推奨案）をユーザーに
     提示し、回答を待って終了する。
   - 回答を受けたら glossary / style guide / profile に反映
     （revision_history 追記）し、決定シートを `status: approved` に更新する。
     blocker 未回答のまま `/translate-subtitles` に進んではならない。

## 検証

- [ ] 3 つの JSON がスキーマに適合（`python3 -c "import json; json.load(open(...))"` で valid 確認）
- [ ] speaker_map 件数 = 字幕件数
- [ ] gender 断定に gender_confidence が付いている
- [ ] low confidence 項目が unresolved-items に転記済み
- [ ] 決定シートの全項目に blocker/advisory・推奨案・根拠がある
- [ ] パイロットが validate_batch.py を PASS し、ネイティブチェックが別文脈で実行された
