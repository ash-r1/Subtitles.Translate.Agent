---
description: 字幕の作品分析（Step 1–3）— スタイルガイド・人物設計・用語集を生成
argument-hint: <字幕ファイルパス> [project-config.yaml のパス]
---

# /analyze-subtitles — 分析フェーズ（Step 1–3）

対象字幕: $ARGUMENTS（未指定なら `project-config.yaml` の `paths.input_subtitle`）

必ず `subtitle-ja-toolkit/CLAUDE.md` と `subtitle-ja-toolkit/prompts/00-common-rules.md`
を先に読むこと。

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

5. **後処理**
   - 各出力の confidence: low 項目を `work/unresolved-items.yaml` へ転記する。
   - Step 3 の `conflicts` があれば Step 2 との矛盾をユーザーに報告する。
   - 生成物の要約（人物数・関係数・用語数・未解決数）を報告して終了する。

## 検証

- [ ] 3 つの JSON がスキーマに適合（`python3 -c "import json; json.load(open(...))"` で valid 確認）
- [ ] speaker_map 件数 = 字幕件数
- [ ] gender 断定に gender_confidence が付いている
- [ ] low confidence 項目が unresolved-items に転記済み
