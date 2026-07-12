#!/usr/bin/env python3
"""字幕ファイル (SRT / WebVTT) <-> JSON 変換ツール。

エージェントは字幕ファイルを直接編集せず、必ずこのツール経由で決定的に
入出力・変換する。依存: 標準ライブラリのみ。

内部表現（JSON）は形式非依存:
  [{"id": "1", "start": "00:00:01,000", "end": "00:00:02,500",
    "text": "一行目\n二行目"}, ...]
timecode は常に SRT 形式 (HH:MM:SS,mmm) へ正規化して保持する。

使い方:
  parse : SRT/VTT を JSON へ（形式は拡張子と内容から自動判定）
    python3 scripts/srt_tools.py parse input/source.srt > work/source.json
    python3 scripts/srt_tools.py parse input/source.vtt > work/source.json
  build : JSON から字幕ファイルを生成（--format srt | vtt、既定 srt）
    python3 scripts/srt_tools.py build work/final.json > output/translated.srt
    python3 scripts/srt_tools.py build work/final.json --format vtt > output/translated.vtt
  convert : 字幕ファイル形式変換（parse + build の決定的ショートカット）
    python3 scripts/srt_tools.py convert input/source.vtt --format srt > input/source.srt
  slice : JSON をバッチへ分割（前後文脈付き）
    python3 scripts/srt_tools.py slice work/source.json --batch-size 20 \
        --preceding 8 --following 5 --outdir work/batches/

ASS は未対応。事前に SRT/VTT へ変換してから使うこと。
"""
import argparse
import json
import re
import sys
from pathlib import Path

SRT_TIME_RE = re.compile(
    r"(\d{2}):(\d{2}):(\d{2})[,.](\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2})[,.](\d{3})")
# VTT は HH: が省略可能で、ミリ秒は '.'。行末に cue settings が付くことがある
VTT_TIME_RE = re.compile(
    r"(?:(\d{2,}):)?(\d{2}):(\d{2})\.(\d{3})\s*-->\s*(?:(\d{2,}):)?(\d{2}):(\d{2})\.(\d{3})")


def _tc(h, m, s, ms):
    return f"{int(h):02d}:{int(m):02d}:{int(s):02d},{int(ms):03d}"


def detect_format(path, text):
    if text.lstrip("﻿").lstrip().startswith("WEBVTT"):
        return "vtt"
    suffix = Path(path).suffix.lower()
    if suffix == ".vtt":
        return "vtt"
    if suffix == ".srt":
        return "srt"
    # 内容から SRT らしさを判定
    if SRT_TIME_RE.search(text):
        return "srt"
    raise ValueError(f"形式を判定できません（SRT/VTT のみ対応）: {path}")


def parse_srt(text):
    blocks = re.split(r"\r?\n\r?\n+", text.strip())
    items = []
    for block_no, block in enumerate(blocks, 1):
        lines = [l for l in block.splitlines() if l.strip()]
        if len(lines) < 2:
            print(f"警告: ブロック {block_no} が不完全なためスキップ: {block!r}",
                  file=sys.stderr)
            continue
        idx = 0
        if lines[0].strip().isdigit():
            sub_id = lines[0].strip()
            idx = 1
        else:
            sub_id = str(len(items) + 1)
        m = SRT_TIME_RE.search(lines[idx])
        if not m:
            # timecode 行がない = データ欠落。黙って進めず即座に失敗させる
            raise ValueError(
                f"ブロック {block_no} に timecode 行が見つかりません: {lines[idx]!r}")
        g = m.groups()
        items.append({
            "id": sub_id,
            "start": _tc(g[0], g[1], g[2], g[3]),
            "end": _tc(g[4], g[5], g[6], g[7]),
            "text": "\n".join(lines[idx + 1:]),
        })
    return items


def parse_vtt(text):
    text = text.lstrip("﻿")
    blocks = re.split(r"\r?\n\r?\n+", text.strip())
    items = []
    for block_no, block in enumerate(blocks, 1):
        lines = [l for l in block.splitlines() if l.strip()]
        if not lines:
            continue
        head = lines[0].strip()
        # ヘッダー・メタデータブロックは読み飛ばす
        if head.startswith(("WEBVTT", "NOTE", "STYLE", "REGION")):
            continue
        idx = 0
        cue_id = None
        if VTT_TIME_RE.search(lines[0]) is None:
            cue_id = lines[0].strip()
            idx = 1
        if idx >= len(lines):
            print(f"警告: ブロック {block_no} が不完全なためスキップ: {block!r}",
                  file=sys.stderr)
            continue
        m = VTT_TIME_RE.search(lines[idx])
        if not m:
            raise ValueError(
                f"ブロック {block_no} に timecode 行が見つかりません: {lines[idx]!r}")
        g = m.groups()
        items.append({
            "id": cue_id if cue_id and cue_id.isdigit() else str(len(items) + 1),
            "start": _tc(g[0] or 0, g[1], g[2], g[3]),
            "end": _tc(g[4] or 0, g[5], g[6], g[7]),
            "text": "\n".join(lines[idx + 1:]),
        })
    return items


def parse_file(path):
    text = Path(path).read_text(encoding="utf-8-sig")
    fmt = detect_format(path, text)
    items = parse_vtt(text) if fmt == "vtt" else parse_srt(text)
    if not items:
        raise ValueError(f"字幕が 1 件も読み取れませんでした: {path}")
    return items


def build_srt(items):
    out = []
    for i, item in enumerate(items, 1):
        out.append(str(item.get("id", i)))
        out.append(f"{item['start']} --> {item['end']}")
        out.append(item["text"])
        out.append("")
    return "\n".join(out) + "\n"


def build_vtt(items):
    out = ["WEBVTT", ""]
    for i, item in enumerate(items, 1):
        out.append(str(item.get("id", i)))
        out.append(f"{item['start'].replace(',', '.')} --> "
                   f"{item['end'].replace(',', '.')}")
        out.append(item["text"])
        out.append("")
    return "\n".join(out) + "\n"


def build(items, fmt):
    return build_vtt(items) if fmt == "vtt" else build_srt(items)


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
    p.add_argument("subtitle", help="SRT または VTT ファイル")

    b = sub.add_parser("build")
    b.add_argument("json")
    b.add_argument("--format", choices=["srt", "vtt"], default="srt")

    c = sub.add_parser("convert")
    c.add_argument("subtitle", help="SRT または VTT ファイル")
    c.add_argument("--format", choices=["srt", "vtt"], required=True,
                   help="出力形式")

    s = sub.add_parser("slice")
    s.add_argument("json")
    s.add_argument("--batch-size", type=int, default=20)
    s.add_argument("--preceding", type=int, default=8)
    s.add_argument("--following", type=int, default=5)
    s.add_argument("--outdir", default="work/batches")

    args = ap.parse_args()
    if args.cmd == "parse":
        json.dump(parse_file(args.subtitle), sys.stdout,
                  ensure_ascii=False, indent=2)
        print()
    elif args.cmd == "build":
        items = json.loads(Path(args.json).read_text(encoding="utf-8"))
        sys.stdout.write(build(items, args.format))
    elif args.cmd == "convert":
        sys.stdout.write(build(parse_file(args.subtitle), args.format))
    elif args.cmd == "slice":
        items = json.loads(Path(args.json).read_text(encoding="utf-8"))
        slice_batches(items, args.batch_size, args.preceding,
                      args.following, args.outdir)


if __name__ == "__main__":
    main()
