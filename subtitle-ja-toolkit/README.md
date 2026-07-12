# subtitle-ja-toolkit

外国語字幕を**自然な日本語字幕**へ翻訳するための、Claude Code / Claude Cowork
向けプロンプト・ツールキット。

このリポジトリに元々あった C# アプリの 6 段階翻訳パイプラインを解析し、
その処理意図を保ったまま、日本語字幕に必要な工程（話者・人物分析、翻訳前
検証ゲート、口調監査、日本語改行規則、最終整合性監査）を加えて **10 工程**へ
再構成したもの。
実行主体はプログラムではなく **エージェント（Claude）** で、機械的な処理だけを
`scripts/` の小さなツールが担う。C# 実装は抽出完了後に削除済み
（git 履歴と `source-prompts/` の記録に残る）。

## 何ができるか

- 作品に通底する**世界観・雰囲気の読み解き**（前提・緊張構造・笑いの質→
  翻訳への含意）を最初に確定し、以後の全判断の根拠にする
- 逐語訳ではなく、**人物ごとの一人称・呼称・敬語・文末・決め台詞**を設計した
  うえでの日本語字幕翻訳（`I`→「私」・`you`→「あなた」の機械変換を禁止）
- 意味監査（誤訳・否定反転・数量・皮肉）と口調監査（人物らしさ・一貫性）の分離
- **全編翻訳前の検証ゲート**: 固有名詞表記の外部資料照会（映像・コンテ・公式資料）、
  不明点の洗い出し、パイロット翻訳＋ネイティブチェックを行い、人間の判断が
  必要な事項を決定シート 1 枚に集約してから本翻訳に入る
- 字幕 ID・timecode・件数の機械検証、CPS・行長・改行位置の制約チェック
- 全工程の中間表現がファイルに残るため、途中からの再実行・調整が可能

## パイプライン

| # | 工程 | プロンプト | 主な成果物 |
|---|---|---|---|
| 1 | 作品全体分析（Director） | `prompts/01-director.md` | global style guide（世界観・雰囲気の読み・表記方針・敬語基準） |
| 2 | 話者・人物分析 ★新設 | `prompts/02-character-analysis.md` | speaker map / character profiles / relationship map |
| 3 | 用語集・反復表現 | `prompts/03-glossary.md` | glossary / phrase map |
| 4 | 翻訳前検証・ネイティブチェック ★ゲート | `prompts/04-pretranslation-check.md` | 決定シート（表記・記号方針・口調サンプルの人間承認） |
| 5 | 翻訳 | `prompts/05-translate.md` | バッチ別の訳文 |
| 6 | 意味監査 | `prompts/06-semantic-review.md` | 意味エラーの検出・修正 |
| 7 | 口調・一貫性監査 ★新設 | `prompts/07-voice-consistency-review.md` | 人物らしさの検査・修正 |
| 8 | 日本語仕上げ | `prompts/08-polish-ja.md` | 自然さ・リズムの改善 |
| 9 | タイミング・改行調整 | `prompts/09-timing-adjust.md` | 表示時間延長・改行位置 |
| 10 | 最終整合性監査 ★新設 | `prompts/10-final-audit.md` | 作品横断の findings（決定事項の反映・印象ドリフト含む） |

Step 4 は全編翻訳の前に人間の確認を挟む**ゲート工程**（運用で得た教訓の反映）。
固有名詞のカタカナ表記・SDH 記号（`[効果音]` 等）の扱い・人物の口調の方向性は、
翻訳後に指摘されると全編修正になるため、外部資料（映像・コンテ・公式資料・wiki）の
照会とパイロット翻訳＋ネイティブチェックで先に洗い出し、`work/04-decision-sheet.md`
への回答をもらってから本翻訳（Step 5〜）へ進む。

続き物を複数ファイルまとめて訳す場合は**シリーズモード**を使う
（`project-config.yaml` の `series.enabled: true` と `series.episodes` の列挙）。
Step 1–4（分析＋ゲート）はシリーズ全体で 1 回だけ実行して成果物を
`work/_shared/` に共有し、Step 5–10 はエピソード単位のループで回して
`output/<episode_id>.srt` を出す。decision sheet（ゲート）はシリーズで 1 枚、
最後に全話横断の最終監査を 1 回追加する。詳細は `CLAUDE.md`
「シリーズ（複数ファイル）運用」を参照。

全工程の共通規約は `prompts/00-common-rules.md`、運用ルール（ファイル配置・
不変条件・バッチ処理・サブエージェント割り当て・失敗時の再実行）は
`CLAUDE.md` を参照。

## セットアップ

```bash
cd subtitle-ja-toolkit
mkdir -p input work output
cp config/project-config.example.yaml project-config.yaml
cp config/subtitle-constraints.example.yaml subtitle-constraints.yaml
# input/ に字幕（SRT または WebVTT）を置き、project-config.yaml のパスを合わせる
# ASS は未対応。事前に SRT/VTT へ変換すること（他形式からの変換例:
#   python3 scripts/srt_tools.py convert input/source.vtt --format srt > input/source.srt）
```

## 実行例（Claude Code）

リポジトリルートで Claude Code を起動し（コマンドはルートの `.claude/commands/`
に定義され、作業は `subtitle-ja-toolkit/` を基準に行われる）:

```
/analyze-subtitles input/source.srt   # Step 1–4: 分析＋翻訳前検証（決定シート提示で停止）
/translate-subtitles                  # Step 5–8: バッチ翻訳＋三重監査（ゲート承認後）
/review-subtitles                     # Step 9–10: タイミング調整・SRT 生成・最終監査
```

または一括で:

```
/run-full-pipeline input/source.srt
```

`/analyze-subtitles` の最後（Step 4）で `work/04-decision-sheet.md` が提示される。
固有名詞の表記・記号方針・口調サンプルへの回答（または「推奨案どおり」の
包括承認）を返すと、翻訳フェーズへ進める。

途中で止まった場合は同じコマンドを再実行すれば、`work/` の完成済みバッチを
スキップして続きから再開する。用語や人物設定を手で直したいときは
`work/03-glossary.json` / `work/02-character-analysis.json` を編集し、
影響するバッチだけ `/translate-subtitles <バッチ番号>` で再実行する。

## 実行手順（Cowork など `.claude` が使えない環境）

コマンドやスキルがなくても、次の指示だけで全工程を実行できる:

```
subtitle-ja-toolkit/CLAUDE.md を読んで、input/source.srt を日本語字幕に
翻訳してください。工程 1 から 10 まで順に実行し、各工程は対応する
prompts/NN-*.md の指示に従ってください。工程 4 の決定シートは私に提示して
回答を待ってください。
```

エージェントは CLAUDE.md の「工程と入出力」の表に従い、
各工程のプロンプトファイルを読み、`{{variable}}` を実データに置換して実行し、
成果物を `work/` に書く。機械検証は `scripts/` を使う:

```bash
python3 scripts/srt_tools.py parse input/source.srt > work/source.json  # SRT→JSON
python3 scripts/srt_tools.py slice work/source.json --outdir work/batches  # バッチ分割
python3 scripts/validate_batch.py work/batches/batch-000.json \
        work/05-translation/batch-000.json                     # 件数・ID・原文検証
python3 scripts/check_constraints.py work/final.json subtitle-constraints.yaml  # CPS/行長
python3 scripts/srt_tools.py build work/final.json > output/translated.srt  # JSON→SRT
```

## 検証サンプル

`samples/` に 30 行の自作検証字幕と、全工程を実走した期待成果物一式がある。

- `samples/input/sample.srt` — 10 の難所（you の訳し分け・公私の切替・
  怒っても敬語・呼称の変化・決め台詞・皮肉・三分割文・話者不明・性別不明・
  代名詞省略）を含む検証用字幕
- `samples/casebook.md` — 各事例の原文・不適切な直訳・改善訳・判断理由
- `samples/expected/` — 各工程の成果物と最終 SRT（Step 4 ゲート新設前の実走
  のため、`04-pilot/` 等のゲート成果物は含まない）
- `samples/validation-report.md` — 実走ログ（検出・修正された問題を含む）

## ディレクトリ構成

```
subtitle-ja-toolkit/
├── README.md / CLAUDE.md          # 本書・運用ルール
├── config/                        # 設定例と JSON スキーマ
│   ├── project-config.example.yaml
│   ├── subtitle-constraints.example.yaml   # CPS・行長など数値制約（プロンプトに固定値を書かない）
│   └── output-schemas/*.schema.json
├── prompts/00〜10                 # 工程別プロンプト（共通規約含む）
├── templates/*.yaml               # profile・関係・用語集などの構造テンプレート
├── scripts/*.py                   # SRT/VTT 変換・件数検証・制約チェック（標準ライブラリのみ）
├── source-prompts/                # 元 C# プロンプトの抽出結果と分析レポート
│   ├── extraction-report.md
│   └── original/extracted-prompts.md
└── samples/                       # 検証用字幕・ケースブック・期待成果物

# リポジトリルート:
.claude/
├── commands/                      # /analyze-subtitles ほか 4 コマンド
└── skills/                        # 5 スキル
```

## 元実装との関係

抽出した元プロンプト（6 エージェント分・原文のまま）は
`source-prompts/original/extracted-prompts.md`、
各プロンプトの分析（役割・変数・問題点・残した設計・変えた設計）と
意図的な変更の理由は `source-prompts/extraction-report.md` にある。

主な変更点: 固定出力件数（「恰好 20 条」）の廃止、gender だけで口調を決める
設計の廃止、he/she 表面化（中国語向け）から日本語ゼロ代名詞優先への反転、
話者・人物・関係の構造化（自由記述 1 欄からの脱却）、意味監査と口調監査の分離、
CoT 開示要求の除去、数値制約の設定ファイル化。
