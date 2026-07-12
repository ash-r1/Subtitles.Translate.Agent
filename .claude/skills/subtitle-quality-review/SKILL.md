---
name: subtitle-quality-review
description: 字幕品質検査（Step 6–10）。意味監査・口調一貫性監査・日本語仕上げ・タイミング調整・最終整合性監査を実行する。翻訳結果（Step 5 出力）が前提。
---

# Subtitle Quality Review（Step 6–10）

> **基準ディレクトリ**: 本スキル内の相対パスはすべて `subtitle-ja-toolkit/` を基準とする。最初に `cd subtitle-ja-toolkit` してから作業すること。


翻訳結果を 3 種の独立した観点で検査・仕上げるスキル。
**観点を混ぜないこと**が元設計から引き継いだ中核方針。

| 工程 | プロンプト | 見るもの | 見ないもの |
|---|---|---|---|
| 6 意味監査 | `prompts/06-semantic-review.md` | 誤訳・漏訳・幻覚・否定・数量・話者取り違え | 文体・自然さ |
| 7 口調監査 | `prompts/07-voice-consistency-review.md` | profile への適合・一貫性 | 意味・好み |
| 8 仕上げ | `prompts/08-polish-ja.md` | 自然さ・リズム・簡潔さ | 意味変更・人物像変更 |
| 9 タイミング | `prompts/09-timing-adjust.md` | CPS・行長・改行位置・表示時間 | 語句の変更 |
| 10 最終監査 | `prompts/10-final-audit.md` | 作品全体の整合性 | 局所の再翻訳 |

## 実行手順

1. `prompts/00-common-rules.md` と該当工程のプロンプトを読む。
2. Step 6/7 は**翻訳を行ったエージェントとは別の文脈**で実行する。
3. 各バッチ出力後に `scripts/validate_batch.py` で検証する
   （PASS 行の訳が入力と完全一致することも検査される）。
4. Step 9 は先に `scripts/check_constraints.py` で違反行を機械抽出し、
   違反行だけを LLM に渡す。
5. Step 10 の findings は自動適用せず、severity 付きでユーザーに報告する。

## 絶対規則

- 文体の好みで FIXED にしない（Step 6）。profile に規則根拠のない修正を
  しない（Step 7）。変更不要行は null / 完全一致で返す（Step 8）。
- 件数は常に入力件数。固定値を仮定しない。
- profile 側が怪しいときは字幕を直さず profile_revision_candidate に分離。
