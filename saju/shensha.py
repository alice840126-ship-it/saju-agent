#!/usr/bin/env python3
"""saju.shensha — 사주 신살·귀인 자동 판정.

판정 대상 (공개 명리학 공식):
  - 천을귀인 — 일간별 2개 지지
  - 도화/역마/화개살 — 년·일지 삼합국 기준
  - 양인살 — 일간별 1개
  - 백호대살 — 7개 특정 갑자
  - 괴강살 — 4개 특정 갑자
  - 공망 — 일주 순(旬) 기준 2개 지지
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, List

CHEONEUL_GWIIN = {
    "甲": ["丑", "未"], "戊": ["丑", "未"], "庚": ["丑", "未"],
    "乙": ["子", "申"], "己": ["子", "申"],
    "丙": ["亥", "酉"], "丁": ["亥", "酉"],
    "壬": ["卯", "巳"], "癸": ["卯", "巳"],
    "辛": ["寅", "午"],
}

SAMHAP_GROUPS = {
    "水": {"members": {"申", "子", "辰"}, "도화": "酉", "역마": "寅", "화개": "辰"},
    "火": {"members": {"寅", "午", "戌"}, "도화": "卯", "역마": "申", "화개": "戌"},
    "金": {"members": {"巳", "酉", "丑"}, "도화": "午", "역마": "亥", "화개": "丑"},
    "木": {"members": {"亥", "卯", "未"}, "도화": "子", "역마": "巳", "화개": "未"},
}

YANGIN = {
    "甲": "卯", "丙": "午", "戊": "午", "庚": "酉", "壬": "子",
    "乙": "辰", "丁": "未", "己": "未", "辛": "戌", "癸": "丑",
}

BAEKHO = {"甲辰", "乙未", "丙戌", "丁丑", "戊辰", "壬戌", "癸丑"}
GOEGANG = {"庚辰", "庚戌", "壬辰", "壬戌", "戊戌", "戊辰"}

SUN_60 = [
    (["甲子", "乙丑", "丙寅", "丁卯", "戊辰", "己巳", "庚午", "辛未", "壬申", "癸酉"], ["戌", "亥"]),
    (["甲戌", "乙亥", "丙子", "丁丑", "戊寅", "己卯", "庚辰", "辛巳", "壬午", "癸未"], ["申", "酉"]),
    (["甲申", "乙酉", "丙戌", "丁亥", "戊子", "己丑", "庚寅", "辛卯", "壬辰", "癸巳"], ["午", "未"]),
    (["甲午", "乙未", "丙申", "丁酉", "戊戌", "己亥", "庚子", "辛丑", "壬寅", "癸卯"], ["辰", "巳"]),
    (["甲辰", "乙巳", "丙午", "丁未", "戊申", "己酉", "庚戌", "辛亥", "壬子", "癸丑"], ["寅", "卯"]),
    (["甲寅", "乙卯", "丙辰", "丁巳", "戊午", "己未", "庚申", "辛酉", "壬戌", "癸亥"], ["子", "丑"]),
]


def gongmang_branches(day_pillar: str) -> List[str]:
    for sun, gm in SUN_60:
        if day_pillar in sun:
            return gm
    return []


def find_shensha(result: Dict[str, Any]) -> Dict[str, Any]:
    p = result["pillars"]
    day_stem = p["day_stem"]
    day_branch = p["day_branch"]
    year_branch = p["year_branch"]
    day_pillar = p["day_pillar"]

    branches_present = [(pos, p.get(f"{pos}_branch")) for pos in ("year", "month", "day", "hour")]
    branches_present = [(pos, b) for pos, b in branches_present if b]

    out: Dict[str, Any] = {}

    gwiin_targets = CHEONEUL_GWIIN.get(day_stem, [])
    out["천을귀인"] = {
        "target_branches": gwiin_targets,
        "found_at": [pos for pos, b in branches_present if b in gwiin_targets],
        "meaning": "쉽게 말해 인생의 결정적 순간에 나타나는 귀인이란다",
    }

    for ref_label, ref_branch in [("년지", year_branch), ("일지", day_branch)]:
        for group_name, g in SAMHAP_GROUPS.items():
            if ref_branch in g["members"]:
                for sal_kind in ("도화", "역마", "화개"):
                    target = g[sal_kind]
                    found = [pos for pos, b in branches_present if b == target]
                    if found:
                        key = f"{sal_kind}살({ref_label} 기준)"
                        out.setdefault(key, []).append({
                            "target_branch": target,
                            "found_at": found,
                        })
                break

    yangin_target = YANGIN.get(day_stem)
    if yangin_target:
        found = [pos for pos, b in branches_present if b == yangin_target]
        if found:
            out["양인살"] = {"branch": yangin_target, "found_at": found,
                          "meaning": "쉽게 말해 칼처럼 날카로운 강한 기운이지"}

    pillars_60 = [(pos, p.get(f"{pos}_pillar")) for pos in ("year", "month", "day", "hour")]
    bh = [(pos, pl) for pos, pl in pillars_60 if pl and pl in BAEKHO]
    if bh:
        out["백호대살"] = [{"pos": pos, "pillar": pl} for pos, pl in bh]

    gg = [(pos, pl) for pos, pl in pillars_60 if pl and pl in GOEGANG]
    if gg:
        out["괴강살"] = [{"pos": pos, "pillar": pl} for pos, pl in gg]

    gm = gongmang_branches(day_pillar)
    if gm:
        found = [pos for pos, b in branches_present if b in gm and pos != "day"]
        out["공망"] = {
            "branches": gm,
            "found_at": found,
            "meaning": "쉽게 말해 그 자리는 비어 있어 결과가 잘 맺히지 않는 자리란다",
        }

    return out


def format_shensha(shensha: Dict[str, Any]) -> str:
    if not shensha:
        return "【신살】 없음"
    lines = ["【신살·귀인】"]
    for k, v in shensha.items():
        if isinstance(v, dict):
            if v.get("found_at"):
                lines.append(f"  ✓ {k}: {v['found_at']}")
            elif k == "천을귀인":
                lines.append(f"  · {k}: 명식엔 없음 (대운·세운에서 만날 수 있다)")
        elif isinstance(v, list):
            for item in v:
                if "pos" in item:
                    lines.append(f"  ✓ {k}: {item['pos']}주({item['pillar']})")
                else:
                    lines.append(f"  ✓ {k}: {item['found_at']} (대상 {item['target_branch']})")
    return "\n".join(lines)


def _selftest() -> int:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from saju.agent import calc
    passed, total = 0, 0

    total += 1
    assert gongmang_branches("己未") == ["子", "丑"]
    print("  ✓ 공망: 己未 → 子丑")
    passed += 1

    # 합성 명식: 일간 甲 + 일지 卯(양인) + 시지 丑(천을귀인) → 양인·천을귀인 동시 활성
    total += 1
    fake_result = {
        "pillars": {
            "year_stem": "庚", "year_branch": "申",
            "month_stem": "戊", "month_branch": "寅",
            "day_stem": "甲", "day_branch": "卯",
            "hour_stem": "乙", "hour_branch": "丑",
            "year_pillar": "庚申", "month_pillar": "戊寅",
            "day_pillar": "甲卯", "hour_pillar": "乙丑",
        }
    }
    s = find_shensha(fake_result)
    assert "천을귀인" in s and "hour" in s["천을귀인"]["found_at"]
    print("  ✓ 천을귀인 시지(甲일간 → 丑·未 중 丑 활성)")
    passed += 1

    total += 1
    assert "양인살" in s and "day" in s["양인살"]["found_at"]
    print("  ✓ 양인살 일지(甲일간 → 卯) 활성")
    passed += 1

    # 실데이터 smoke test — calc()로 만들어진 결과에 find_shensha 적용 시 에러 없는지
    total += 1
    r = calc(year=1990, month=5, day=15, hour=14, minute=0,
             longitude=126.978, time_mode="approx")
    s2 = find_shensha(r)
    assert isinstance(s2, dict)
    fmt = format_shensha(s2)
    assert "신살" in fmt or "신살·귀인" in fmt
    print(f"  ✓ 실 명식 신살 산출 ({len(s2)}종)")
    passed += 1

    total += 1
    txt = format_shensha(s)
    assert "천을귀인" in txt
    print("  ✓ format")
    passed += 1

    print(f"✅ selftest passed: {passed}/{total}")
    return 0 if passed == total else 1


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "selftest":
        sys.exit(_selftest())
    elif len(sys.argv) > 1 and sys.argv[1] == "demo":
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
        from saju.agent import calc
        r = calc(year=1990, month=5, day=15, hour=14, minute=0,
                 longitude=126.978, time_mode="approx")
        print(format_shensha(find_shensha(r)))
    else:
        print(__doc__)
