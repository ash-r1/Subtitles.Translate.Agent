#!/usr/bin/env python3
"""バッチ出力の機械検証。件数・ID・順序・original 不改変を検査する。

各工程（Step 5〜9）の出力を書いたら**必ず**これを実行し、FAIL なら再実行する。

使い方:
  python3 scripts/validate_batch.py <入力バッチ.json> <出力バッチ.json>

入力バッチ: srt_tools.py slice の出力（current_batch を持つ）
出力バッチ: 各工程の出力（items を持つ）
終了コード: 0=PASS, 1=FAIL
"""
import json
import sys
from pathlib import Path


def main():
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(2)

    inp = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    out = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))

    src = inp["current_batch"] if "current_batch" in inp else inp["items"]
    items = out["items"]

    if not src or not items:
        print("FAIL")
        print(f"  - 空バッチ: 入力 {len(src)} 件 / 出力 {len(items)} 件（0 件のバッチは不正）")
        sys.exit(1)

    errors = []

    if len(items) != len(src):
        errors.append(f"件数不一致: 入力 {len(src)} 件 / 出力 {len(items)} 件")

    declared = out.get("item_count")
    if declared is not None and declared != len(items):
        errors.append(f"item_count 宣言 ({declared}) と items.length ({len(items)}) が不一致")

    for i, (s, o) in enumerate(zip(src, items)):
        if str(s["id"]) != str(o["id"]):
            errors.append(f"[{i}] ID 不一致: 入力 {s['id']} / 出力 {o['id']}")
        src_text = s.get("text", s.get("original", ""))
        out_orig = o.get("original")
        if out_orig is not None and out_orig.replace("\n", " ") != src_text.replace("\n", " "):
            errors.append(f"[id={o['id']}] original が入力原文と一致しない")
        # PASS 行の不変性（review 系のみ）
        if o.get("status") == "PASS" and "draft" in o and "final_translation" in o:
            if o["final_translation"] != o["draft"]:
                errors.append(f"[id={o['id']}] PASS なのに final_translation が draft と異なる")

    if errors:
        print("FAIL")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)
    print(f"PASS ({len(items)} 件, ids {items[0]['id']}..{items[-1]['id']})")


if __name__ == "__main__":
    main()
