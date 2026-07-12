---
description: 出力生成と最終検査（Step 9–10）— タイミング調整・SRT 生成・全体整合性監査
argument-hint: "[--skip-timing | --audit-only]"
---

# /review-subtitles — 出力・最終検査フェーズ（Step 9–10）

> **基準ディレクトリ**: 本コマンド内の相対パス（`prompts/` `scripts/` `config/` `templates/` `work/` `input/` `output/` `project-config.yaml` 等）はすべて `subtitle-ja-toolkit/` を基準とする。最初に `cd subtitle-ja-toolkit` してから作業すること。


前提: `/translate-subtitles` 完了（`work/08-polish/` が全バッチ分あること）。

必ず `subtitle-ja-toolkit/CLAUDE.md` と `prompts/00-common-rules.md` を先に読むこと。
$ARGUMENTS: `--skip-timing` で Step 9 を飛ばす、`--audit-only` で Step 10 のみ。

**シリーズモード**（`series.enabled: true`）: 下の手順を `series.episodes` の
**エピソード単位のループ**で回す。共有成果物は `work/_shared/`、各話の統合・
出力は `work/<episode_id>/final.json` と `output/<episode_id>.srt`。全エピソード
完了後に**シリーズ横断の最終監査を 1 回**追加する（glossary・phrase_map・
一人称・印象ドリフトをエピソード間で照合。書式は Step 10 と同じで
`affected_ids` にエピソードプレフィックス、出力 `work/_shared/series-final-audit.json`）。
詳細は CLAUDE.md「シリーズ（複数ファイル）運用」。

## 手順

1. **統合**: Step 8 までの確定訳（polished_text ?? 前工程の final_translation）
   と `work/source.json` の timecode を突き合わせ、
   `work/final.json`（`{id, start, end, text}` の配列）を作る。
   件数と ID が元字幕と完全一致することを機械的に確認する。

2. **Step 9 タイミング調整**（Haiku / low）:
   - まず `python3 scripts/check_constraints.py work/final.json
     subtitle-constraints.yaml` で違反一覧を機械抽出する。
   - 違反のある行（＋前後 1 行）だけをバッチにまとめ、
     `prompts/09-timing-adjust.md` でサブエージェントに調整させる
     （違反ゼロの行は LLM に渡さない）。
   - `needs_shortening` flag の行は Step 8 へ差し戻して縮約し、再検査する。
   - 調整結果を `work/final.json` に適用し（end_time と改行のみ）、
     再度 check_constraints.py を実行して収束を確認する。

3. **字幕生成**: `python3 scripts/srt_tools.py build work/final.json >
   output/translated.srt`（VTT 出力は `--format vtt`）。
   件数・ID・start_time が入力と一致することを最終確認する。

4. **Step 10 最終整合性監査**（Opus / high）:
   - 機械検査を先に行う: glossary / phrase_map の各エントリについて
     Grep で最終訳の全出現箇所を照合する。
   - 文脈検査（一人称・呼称・敬語・関係変化・orthography）は
     `prompts/10-final-audit.md` でサブエージェントに実行させる。
     検査項目別に並列分割してよい。
   - 出力 `work/10-final-audit.json`。

5. **findings の処置**: blocker / major の findings をユーザーに提示し、
   承認された修正のみ適用する（適用時は consistency_risk を再確認し、
   影響範囲があれば該当箇所も検査する）。修正後は SRT を再生成する。

## 検証

- [ ] output/translated.srt の件数・ID・start_time が入力字幕と一致
- [ ] check_constraints.py の findings が 0 件（または needs_shortening として報告済み）
- [ ] Step 10 の findings がすべて severity・evidence 付きで報告された
- [ ] 未承認の自動一括置換を行っていない
