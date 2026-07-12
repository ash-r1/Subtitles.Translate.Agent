---
name: pretranslation-native-check
description: 翻訳前検証・ネイティブチェックゲート（Step 4）。固有名詞表記の外部資料照会（映像・コンテ・公式資料・wiki）、不明点の洗い出し、パイロット翻訳＋ネイティブチェックを行い、決定シートをユーザーに提示する。全編翻訳（Step 5）の前の必須ゲート。
---

# Pre-translation Native Check（Step 4）

> **基準ディレクトリ**: 本スキル内の相対パスはすべて `subtitle-ja-toolkit/` を基準とする。最初に `cd subtitle-ja-toolkit` してから作業すること。


「翻訳し終えてから直す」たぐいの問題（固有名詞のカタカナ表記・SDH 記号の
扱い・人物の口調の印象）を、全編翻訳の前にパイロット 1〜2 バッチ分のコストで
捕まえるゲート工程。

## 実行手順

1. `prompts/00-common-rules.md` と `prompts/04-pretranslation-check.md` を読む。
2. glossary のカタカナ音写・独自表記の全語について傍証を探す。優先順位:
   **公式日本語資料 ＞ 映像の音声・画面内テキスト ＞ 他言語公式字幕 ＞
   ファン wiki ＞ 推測**（資料は project-config の `external_references`）。
3. `work/unresolved-items.yaml` の各項目を (a) 外部資料で解決 /
   (b) 映像・コンテ確認が必要（timecode 列挙、可能ならフレーム抽出）/
   (c) 人間の判断が必要、に分類して処置する。
4. 代表 1〜2 バッチをパイロット翻訳（Step 5〜8 のミニラン、成果物は
   `work/04-pilot/` のみ）し、**別文脈のエージェント**に日本語のみを渡して
   ネイティブチェックさせる（→ `work/04-native-check.json`）。
5. 結果を `work/04-decision-sheet.md`（`templates/decision-sheet.md` 準拠、
   `status: pending`）に集約し、ユーザーに提示して回答を待つ。
6. 回答を glossary / style guide / profile に反映（revision_history 追記）し、
   `status: approved` に更新する。パイロット訳は破棄する。

## 絶対規則

- blocker 未回答のまま Step 5（全編翻訳）を開始しない。
- 傍証未確認の表記を「公式」と記載しない。wiki は official として扱わない。
- 決定シートの全質問に推奨案を添える（ユーザーへの丸投げ禁止）。
- ネイティブチェック担当に原文・profile・glossary を渡さない
  （「日本語として自然か」だけを見させる）。
- パイロット訳を本番成果物（`work/05-translation/` 等）へ流用しない。
