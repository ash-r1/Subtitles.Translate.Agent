#!/usr/bin/env python3
"""日本語字幕の物理制約チェック（Step 8 の機械検査部分）。

CPS・行長・最小表示時間・ギャップを subtitle-constraints.yaml の値で検査し、
違反を JSON で報告する。判断（改行位置の選択・延長量）はエージェントが行い、
数値検査はこのスクリプトが行う。

使い方:
  python3 scripts/check_constraints.py work/final.json subtitle-constraints.yaml

依存: PyYAML があれば YAML を読む。なければ簡易パーサで主要キーのみ読む。
"""
import json
import re
import sys
import unicodedata
from pathlib import Path


def load_constraints(path):
    text = Path(path).read_text(encoding="utf-8")
    try:
        import yaml  # type: ignore
        return yaml.safe_load(text)
    except ImportError:
        # 簡易フォールバック: "key: 数値" の行だけ拾ってフラットに返す
        flat = {}
        for line in text.splitlines():
            m = re.match(r"\s*([a-z_]+):\s*([0-9.]+)\s*(#.*)?$", line)
            if m:
                flat[m.group(1)] = float(m.group(2))
        return {
            "reading_speed": {"max_cps": flat.get("max_cps", 7.0),
                              "comfortable_cps": flat.get("comfortable_cps", 4.0)},
            "line_length": {"max_chars_per_line": flat.get("max_chars_per_line", 15),
                            "max_lines": int(flat.get("max_lines", 2))},
            "timing": {"min_duration_ms": flat.get("min_duration_ms", 1200),
                       "min_gap_ms": flat.get("min_gap_ms", 50)},
            "char_counting": {"fullwidth": flat.get("fullwidth", 1.0),
                              "halfwidth": flat.get("halfwidth", 0.5),
                              "space": flat.get("space", 0.5)},
        }


def to_ms(tc):
    h, m, rest = tc.split(":")
    s, ms = re.split(r"[,.]", rest)
    return ((int(h) * 60 + int(m)) * 60 + int(s)) * 1000 + int(ms)


def char_weight(ch, rules):
    if ch in ("\n",):
        return 0.0
    if ch == " " or ch == "　":
        return rules.get("space", 0.5)
    return (rules.get("fullwidth", 1.0)
            if unicodedata.east_asian_width(ch) in ("F", "W", "A")
            else rules.get("halfwidth", 0.5))


def effective_len(text, rules):
    return sum(char_weight(c, rules) for c in text)


def main():
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(2)
    items = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    c = load_constraints(sys.argv[2])
    cc = c["char_counting"]
    findings = []

    for i, item in enumerate(items):
        text = item["text"]
        dur_ms = to_ms(item["end"]) - to_ms(item["start"])
        n = effective_len(text, cc)
        cps = n / (dur_ms / 1000.0) if dur_ms > 0 else float("inf")

        if cps > c["reading_speed"]["max_cps"]:
            findings.append({"id": item["id"], "type": "cps_exceeded",
                             "cps": round(cps, 2),
                             "limit": c["reading_speed"]["max_cps"]})
        lines = text.split("\n")
        if len(lines) > c["line_length"]["max_lines"]:
            findings.append({"id": item["id"], "type": "too_many_lines",
                             "lines": len(lines)})
        for line in lines:
            ln = effective_len(line, cc)
            if ln > c["line_length"]["max_chars_per_line"]:
                findings.append({"id": item["id"], "type": "line_too_long",
                                 "length": ln,
                                 "limit": c["line_length"]["max_chars_per_line"],
                                 "line": line})
        if dur_ms < c["timing"]["min_duration_ms"] and n > 3:
            findings.append({"id": item["id"], "type": "too_short_duration",
                             "duration_ms": dur_ms})
        if i + 1 < len(items):
            gap = to_ms(items[i + 1]["start"]) - to_ms(item["end"])
            if gap < c["timing"]["min_gap_ms"]:
                findings.append({"id": item["id"], "type": "gap_violation",
                                 "gap_ms": gap})

    print(json.dumps({"total": len(items), "findings": findings},
                     ensure_ascii=False, indent=2))
    sys.exit(1 if findings else 0)


if __name__ == "__main__":
    main()
