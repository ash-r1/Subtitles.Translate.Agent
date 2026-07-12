# Subtitles Translate Agent（日本語字幕翻訳ツールキット）

外国語字幕を自然な日本語字幕へ翻訳するための、Claude Code / Claude Cowork 向け
エージェント実行型ツールキット。

本体は **[`subtitle-ja-toolkit/`](subtitle-ja-toolkit/README.md)** にある。
使い方・工程・設計はそちらの README と
[`subtitle-ja-toolkit/CLAUDE.md`](subtitle-ja-toolkit/CLAUDE.md) を参照。

## クイックスタート

リポジトリルートで Claude Code を起動し:

```
/analyze-subtitles subtitle-ja-toolkit/input/source.srt   # Step 1–3: 分析
/translate-subtitles                                      # Step 4–7: 翻訳＋監査
/review-subtitles                                         # Step 8–9: 出力・最終監査
```

（コマンドは `.claude/commands/` にあり、作業は `subtitle-ja-toolkit/` を
基準ディレクトリとして行われる）

## 来歴

このリポジトリは元々 C# 製の Multi-Agent 字幕翻訳エンジンだった。
その 6 段階パイプラインのプロンプトを抽出・分析して日本語字幕向けに
9 工程へ再構成したのが本ツールキットであり、C# 実装は役目を終えたため
削除済み（git 履歴、および
[`subtitle-ja-toolkit/source-prompts/`](subtitle-ja-toolkit/source-prompts/)
の抽出記録に残っている）。
