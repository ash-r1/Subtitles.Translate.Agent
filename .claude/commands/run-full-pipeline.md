---
description: 字幕翻訳の全工程実行（Step 1–9）— 分析→翻訳→監査→出力を一括で
argument-hint: <字幕ファイルパス>
---

# /run-full-pipeline — 全工程実行

> **基準ディレクトリ**: 本コマンド内の相対パス（`prompts/` `scripts/` `config/` `templates/` `work/` `input/` `output/` `project-config.yaml` 等）はすべて `subtitle-ja-toolkit/` を基準とする。最初に `cd subtitle-ja-toolkit` してから作業すること。


対象字幕: $ARGUMENTS

3 つのフェーズを順に実行する。各フェーズの詳細手順は該当コマンドの
ファイルに従う（このコマンドは編成のみを行う）。

1. `.claude/commands/analyze-subtitles.md` の手順（Step 1–3）
2. `.claude/commands/translate-subtitles.md` の手順（Step 4–7）
3. `.claude/commands/review-subtitles.md` の手順（Step 8–9）

## 編成ルール

- フェーズ間で必ず立ち止まり、生成物の要約と未解決事項をユーザーに報告する。
  ただし確認待ちで停止はせず、blocker（例: 話者同定が広範囲に unknown、
  glossary と profile の矛盾）がある場合のみ質問して停止する。
- 中断からの再開時は `work/` の状態を調べ、完成済みの工程・バッチを
  スキップして続きから実行する。
- トークン節約のため、各サブエージェントには「そのバッチに必要な範囲の
  成果物だけ」を渡す（profile は登場人物分のみ、glossary は出現語のみ等。
  抜粋したことを明記する）。
- 終了時に最終報告を出す: 字幕件数 / バッチ数 / FIXED 件数（Step 5・6 別）/
  polish 変更率 / タイミング調整数 / Step 9 findings / 残存 unresolved。
