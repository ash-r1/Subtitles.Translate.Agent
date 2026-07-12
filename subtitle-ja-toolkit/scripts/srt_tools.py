#!/usr/bin/env python3
"""SRT <-> JSON 変換ツール。

エージェントは字幕ファイルを直接編集せず、必ずこのツール経由で入出力する。
依存: 標準ライブラリのみ。

使い方:
  parse : SRT を JSON へ（id は SRT の連番を文字列化）
    python3 scripts/srt_tools.py parse input/source.srt > work/source.json
  build : 翻訳結果 JSON から SRT を生成
    python3 scripts/srt_tools.py build work/final.json > output/translated.srt
  slice : JSON をバッチへ分割（前後文脈付き）
    python3 scripts/srt_tools.py slice work/source.json --batch-size 20 \
        --preceding 8 --following 5 --outdir work/batches/

build の入力 JSON 形式（Step 8 統合結果）:
  [{"id": "1", "start": "00:00:01,000", "end": "00:00:02,500",
    "text": "一行目\n二行目"}, ...]
"""
import argparse
import json
import re
import sys
from pathlib import Path

TIME_RE = re.compile(
    r"(\d{2}):(\d{2}):(\d{2})[,.](\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2})[,.](\d{3})")


def parse_srt(path):
    text = Path(path).read_text(encoding="utf-8-sig")
    blocks = re.split(r"\r?\n\r?\n+", text.strip())
    items = []
    for block in blocks:
        lines = [l for l in block.splitlines() if l.strip()]
        if len(lines) < 2:
            continue
        idx = 0
        if lines[0].strip().isdigit():
            sub_id = lines[0].strip()
            idx = 1
        else:
            sub_id = str(len(items) + 1)
        m = TIME_RE.search(lines[idx])
        if not m:
            continue
        start = f"{m.group(1)}:{m.group(2)}:{m.group(3)},{m.group(4)}"
        end = f"{m.group(5)}:{m.group(6)}:{m.group(7)},{m.group(8)}"
        items.append({
            "id": sub_id,
            "start": start,
            "end": end,
            "text": "\n".join(lines[idx + 1:]),
        })
    return items


def build_srt(items):
    out = []
    for i, item in enumerate(items, 1):
        out.append(str(item.get("id", i)))
        out.append(f"{item['start']} --> {item['end']}")
        out.append(item["text"])
        out.append("")
    return "\n".join(out) + "\n"


def slice_batches(items, batch_size, preceding, following, outdir):
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    n = len(items)
    batch_no = 0
    for start in range(0, n, batch_size):
        end = min(start + batch_size, n)
        batch = {
            "batch_id": f"{batch_no:03d}",
            "batch_item_count": end - start,
            "first_item_id": items[start]["id"],
            "last_item_id": items[end - 1]["id"],
            "preceding_context": items[max(0, start - preceding):start],
            "current_batch": items[start:end],
            "following_context": items[end:min(n, end + following)],
        }
        path = outdir / f"batch-{batch_no:03d}.json"
        path.write_text(json.dumps(batch, ensure_ascii=False, indent=2),
                        encoding="utf-8")
        print(f"{path}  items={batch['batch_item_count']} "
              f"ids={batch['first_item_id']}..{batch['last_item_id']}")
        batch_no += 1


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("parse")
    p.add_argument("srt")

    b = sub.add_parser("build")
    b.add_argument("json")

    s = sub.add_parser("slice")
    s.add_argument("json")
    s.add_argument("--batch-size", type=int, default=20)
    s.add_argument("--preceding", type=int, default=8)
    s.add_argument("--following", type=int, default=5)
    s.add_argument("--outdir", default="work/batches")

    args = ap.parse_args()
    if args.cmd == "parse":
        json.dump(parse_srt(args.srt), sys.stdout, ensure_ascii=False, indent=2)
        print()
    elif args.cmd == "build":
        items = json.loads(Path(args.json).read_text(encoding="utf-8"))
        sys.stdout.write(build_srt(items))
    elif args.cmd == "slice":
        items = json.loads(Path(args.json).read_text(encoding="utf-8"))
        slice_batches(items, args.batch_size, args.preceding,
                      args.following, args.outdir)


if __name__ == "__main__":
    main()
