---
description: 字幕翻訳の実行（Step 5–8）— バッチごとに翻訳→意味監査→口調監査→仕上げ
argument-hint: "[開始バッチ番号（再開用）]"
---

# /translate-subtitles — 翻訳フェーズ（Step 5–8）

> **基準ディレクトリ**: 本コマンド内の相対パス（`prompts/` `scripts/` `config/` `templates/` `work/` `input/` `output/` `project-config.yaml` 等）はすべて `subtitle-ja-toolkit/` を基準とする。最初に `cd subtitle-ja-toolkit` してから作業すること。


前提: `/analyze-subtitles` 完了（`work/01`〜`03` が存在すること）。
なければ先にそちらを実行するようユーザーに伝える。

**ゲート確認**: `work/04-decision-sheet.md` を読み、`status: approved` である
ことを確認する。`pending` のまま（または blocker 未回答のまま）本フェーズを
開始してはならない（`pipeline.enable_pretranslation_check: false` の場合のみ
決定シートなしで進んでよい）。パイロット成果物 `work/04-pilot/` は参照のみとし、
本番バッチはすべて batch-000 から正式に実行する。

必ず `subtitle-ja-toolkit/CLAUDE.md` と `prompts/00-common-rules.md` を先に読むこと。

## 手順

1. **バッチ分割**: `python3 scripts/srt_tools.py slice work/source.json
   --batch-size <config> --preceding <config> --following <config>
   --outdir work/batches/` を実行する。
   $ARGUMENTS に開始バッチ番号があればそこから再開する
   （それ以前の完成済みバッチは再実行しない）。

2. **バッチループ**: 各バッチについて 5→6→7→8 を順に実行してから次へ進む。
   前方文脈（preceding_context の訳）には**直前バッチの Step 8 確定訳**を使う。

   - **Step 5 翻訳**（Sonnet / high）: `prompts/05-translate.md` に、
     バッチ・Step 1〜3 成果物・該当 scene・constraints を渡す。
     出力 `work/05-translation/batch-NNN.json`。
   - **検証**: `python3 scripts/validate_batch.py work/batches/batch-NNN.json
     work/05-translation/batch-NNN.json`。FAIL なら件数指摘を添えて再実行
     （最大 3 回）。
   - **Step 6 意味監査**（Sonnet / medium・**Step 5 とは別のサブエージェント**）:
     `prompts/06-semantic-review.md`。出力 `work/06-semantic-review/batch-NNN.json`
     → validate_batch で検証。
   - **Step 7 口調監査**（Sonnet / medium・別サブエージェント）:
     `prompts/07-voice-consistency-review.md`。
     出力 `work/07-voice-review/batch-NNN.json` → 検証。
   - **Step 8 仕上げ**（Opus / medium）: `prompts/08-polish-ja.md`。
     出力 `work/08-polish/batch-NNN.json` → 検証。

3. **バッチ間の反映**: 各バッチ完了後、
   - Step 5 の `new_findings`・Step 7 の `profile_revision_candidates` を確認し、
     採用するものを CLAUDE.md の「profile / glossary の更新手順」に従って
     反映する（revision_history 追記を忘れない）。
   - `sentence_spans_batch` flag があれば、次バッチの前方文脈をその文を含む
     範囲まで広げる。

4. **完了報告**: 全バッチの統計（翻訳数・FIXED 数・flag 数・profile 更新数）を
   まとめて報告する。

## 検証（バッチごと）

- [ ] validate_batch.py が全工程 PASS
- [ ] PASS 行の訳が前工程と完全一致
- [ ] Step 5 と Step 6/7 を同一エージェント文脈で実行していない
