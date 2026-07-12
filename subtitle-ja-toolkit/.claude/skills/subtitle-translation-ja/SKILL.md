---
name: subtitle-translation-ja
description: 日本語字幕翻訳の実行（Step 4）。人物設定・関係・用語集に基づき、ゼロ代名詞と自然な日本語台詞を優先したバッチ翻訳を行う。分析工程（Step 1–3）の成果物が前提。
---

# Subtitle Translation JA（Step 4）

バッチ単位で字幕を日本語へ翻訳するスキル。

## 実行手順

1. `subtitle-ja-toolkit/prompts/00-common-rules.md` と
   `prompts/04-translate.md` を読む。
2. `scripts/srt_tools.py slice` でバッチを切り、各バッチに Step 1–3 の
   成果物（登場人物分のみ抜粋可）・前方確定訳・後方原文 preview・
   scene context を添えて翻訳する。
3. 出力を `work/04-translation/batch-NNN.json` に書き、
   `scripts/validate_batch.py` で件数・ID・original 不改変を検証する。

## 翻訳の判断順序（要点）

意味単位の復元 → 話者/相手の確認 → 意図・感情 → 一人称/呼称/敬語の選択 →
自然な日本語文 → 不要代名詞の削除 → 行への再分割 → 用語統一 → 件数検証。

## 絶対規則

- `I`/`you` を機械的に表面化しない。「あなた」は最後の手段。
- 後続字幕の内容語を先取りしない。前方確定訳を再翻訳しない。
- glossary の official/confirmed 訳語は強制。
- speaker unknown の行に人物固有口調を使わない（中立訳＋flag）。
- 訳文フィールドに注釈・タグを混ぜない。新発見は new_findings へ。
