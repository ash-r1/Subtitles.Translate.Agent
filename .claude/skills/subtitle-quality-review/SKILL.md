---
name: subtitle-quality-review
description: 字幕品質検査（Step 5–9）。意味監査・口調一貫性監査・日本語仕上げ・タイミング調整・最終整合性監査を実行する。翻訳結果（Step 4 出力）が前提。
---

# Subtitle Quality Review（Step 5–9）

> **基準ディレクトリ**: 本スキル内の相対パスはすべて `subtitle-ja-toolkit/` を基準とする。最初に `cd subtitle-ja-toolkit` してから作業すること。


翻訳結果を 3 種の独立した観点で検査・仕上げるスキル。
**観点を混ぜないこと**が元設計から引き継いだ中核方針。

| 工程 | プロンプト | 見るもの | 見ないもの |
|---|---|---|---|
| 5 意味監査 | `prompts/05-semantic-review.md` | 誤訳・漏訳・幻覚・否定・数量・話者取り違え | 文体・自然さ |
| 6 口調監査 | `prompts/06-voice-consistency-review.md` | profile への適合・一貫性 | 意味・好み |
| 7 仕上げ | `prompts/07-polish-ja.md` | 自然さ・リズム・簡潔さ | 意味変更・人物像変更 |
| 8 タイミング | `prompts/08-timing-adjust.md` | CPS・行長・改行位置・表示時間 | 語句の変更 |
| 9 最終監査 | `prompts/09-final-audit.md` | 作品全体の整合性 | 局所の再翻訳 |

## 実行手順

1. `prompts/00-common-rules.md` と該当工程のプロンプトを読む。
2. Step 5/6 は**翻訳を行ったエージェントとは別の文脈**で実行する。
3. 各バッチ出力後に `scripts/validate_batch.py` で検証する
   （PASS 行の訳が入力と完全一致することも検査される）。
4. Step 8 は先に `scripts/check_constraints.py` で違反行を機械抽出し、
   違反行だけを LLM に渡す。
5. Step 9 の findings は自動適用せず、severity 付きでユーザーに報告する。

## 絶対規則

- 文体の好みで FIXED にしない（Step 5）。profile に規則根拠のない修正を
  しない（Step 6）。変更不要行は null / 完全一致で返す（Step 7）。
- 件数は常に入力件数。固定値を仮定しない。
- profile 側が怪しいときは字幕を直さず profile_revision_candidate に分離。
