# サンプル検証レポート

> 註: この検証は Step 4（翻訳前検証ゲート）新設前の 9 工程時代に実施した。
> 工程番号・成果物パスは現行 10 工程の番号に読み替えて更新済みだが、
> `expected/` に Step 4 の成果物（04-pilot / 04-decision-sheet 等）は含まれない。

実施日: 2026-07-12
対象: `samples/input/sample.srt`（自作 30 行）→ `samples/expected/translated.srt`

## 実行した処理

1. `srt_tools.py parse` で 30 件を JSON 化（`work/source.json`）
2. `srt_tools.py slice --batch-size 20 --preceding 8 --following 5` で
   2 バッチに分割（20 件 + 10 件。固定件数に依存しないことを確認）
3. Step 1〜3 を実行（`expected/01`〜`03`。スキーマ適合を確認）
4. バッチごとに Step 5→6→7→8 を実行。各工程後に `validate_batch.py` を実行:

   ```
   05-translation/batch-000: PASS (20 件, ids 1..20)
   05-translation/batch-001: PASS (10 件, ids 21..30)
   06-semantic-review/batch-000: PASS / batch-001: PASS
   07-voice-review/batch-000: PASS / batch-001: PASS
   08-polish/batch-000: PASS / batch-001: PASS
   ```

5. Step 8 確定訳＋元 timecode を統合し `check_constraints.py` を実行 →
   **line_too_long ×10、cps_exceeded ×1（id 24, CPS 7.03）** を機械検出
6. Step 9 で改行 10 件（REBREAK）、id 24 は次行開始 −50ms まで延長
   （EXTEND_REBREAK, end 00:01:02,400 → 00:01:02,550）→ 再検査 **findings 0 件**
7. `srt_tools.py build` で SRT 生成。件数 30・ID・start_time の完全一致を確認
8. Step 10 監査 → blocker 0 / major 0 / minor 1（sub:14-16 の話者推定依存）

## パイプラインが実際に検出・修正した事例

| 字幕 | 問題 | 検出工程 | 修正 |
|---|---|---|---|
| 13 | 皮肉の字義訳「ああ　素晴らしい…」 | Step 6 (`irony`) | 「最高だね　前線か　ついてるよ」 |
| 12 | gender unknown の Morgan に女性語尾「わよ」 | Step 7 (`gender_based_ending`, rule_ref 付き) | 「もうやってる」 |
| 11 | 号令のリズム | Step 8 (`speech_rhythm`) | 「呼びかけを続けろ」→「呼びかけ続けろ」 |
| 24 | CPS 7.03 超過＋行長超過 | Step 9（機械検出） | 改行＋150ms 延長で CPS 6.7 |
| 14-16 | 話者推定（medium）への依存 | Step 10 (`low_confidence_dependency`) | findings として報告（自動修正せず） |

## ケースブック 10 事例のカバレッジ

すべて `samples/casebook.md` の対応表どおり成果物に反映されている
（you の訳し分け: sub:4/9/18/19/20/22/30、公私切替: sub:10/19/25、
怒っても敬語: sub:22/24、呼称変化: sub:9→29、決め台詞: sub:8/28、
皮肉: sub:13、三分割文: sub:14-16、話者不明: sub:5、性別不明: sub:12/18、
I/you 省略: sub:19）。

## 確認できた設計上の性質

- 件数・ID・原文の不変性が全工程で機械検証可能（validate_batch.py）
- PASS 行の完全一致が強制されるため、監査工程の「無断の書き換え」が検出される
- 数値制約はすべて `subtitle-constraints.yaml` 由来（プロンプト内の固定値なし）
- 話者不明・性別不明が最後まで unknown のまま処理でき、断定が発生しない

## 残課題

- `work/` 配下（`source.json`・`batches/`・`final.json` 等）は再現用に
  リポジトリへ含めていない。`samples/expected/` が正となる
- sub:14-16 の話者確定（映像なしでは不能）は open のまま
