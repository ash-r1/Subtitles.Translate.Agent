---
name: subtitle-project-analysis
description: 字幕作品の全体分析（Step 1 Director）。作品種別・語調・視聴者・日本語表記方針・敬語基準を定めたグローバルスタイルガイドを生成する。翻訳開始前に必ず 1 回実行する。
---

# Subtitle Project Analysis（Step 1）

字幕作品全体を読み、後続の全工程が従うスタイルガイドを作るスキル。

## 実行手順

1. `subtitle-ja-toolkit/prompts/00-common-rules.md` と
   `subtitle-ja-toolkit/prompts/01-director.md` を読む。
2. 字幕を `scripts/srt_tools.py parse` で JSON 化して読む
   （長い場合は冒頭・中盤・終盤をサンプリングし、範囲を記録する）。
3. `project-config.yaml` の `style_overrides` と `official_references` を
   最優先で反映する。
4. `prompts/01-director.md` の Required procedure に従い、
   `work/01-global-analysis.json` を生成する
   （スキーマ: `config/output-schemas/global-analysis.schema.json`）。

## この工程でしないこと

- 翻訳しない。人物個別の口調を決めない（それは character-voice-analysis）。
- 字幕にない設定を断定しない。不明は unknown + unresolved_questions。

## 出力の要点

- orthography（句読点・記号・話者表記）を全項目決める
- 敬語の基準線・語彙水準・避ける表現を具体的に書く
- 推測には confidence と evidence_ids を付ける
