#!/usr/bin/env python3
"""saju.daewoon — 대운 계산 (10년 단위 인생 흐름).

원리:
  1. 양남음녀(년간 陽 + 男 / 년간 陰 + 女) → 순행
     음남양녀(년간 陰 + 男 / 년간 陽 + 女) → 역행
  2. 대운수: 출생일 ↔ 가장 가까운 절기(節)까지의 거리(일수) ÷ 3
     - 순행: 출생일 → 다음 절(節)까지 일수
     - 역행: 직전 절(節) → 출생일까지 일수
  3. 월주 기준 ±1씩 60갑자 진행 (8~10개 대운 = 80~100세까지)

명리학에서 '節'(절)만 사용 (氣는 제외): 입춘·경칩·청명·입하·망종·소서·입추·백로·한로·입동·대설·소한.

sajupy의 calendar_data.csv를 절기 데이터 소스로 사용.
"""
from __future__ import annotations

import csv
import sys
from datetime import date, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

STEMS = "甲乙丙丁戊己庚辛壬癸"
BRANCHES = "子丑寅卯辰巳午未申酉戌亥"

# 12절(節) — 월주가 바뀌는 절기. 氣는 제외.
JEOL_TERMS_HANJA = {
    "立春", "驚蟄", "淸明", "立夏", "芒種", "小暑",
    "立秋", "白露", "寒露", "立冬", "大雪", "小寒",
}
YANG_STEMS = {"甲", "丙", "戊", "庚", "壬"}


def _load_jeol_terms() -> List[tuple]:
    """sajupy calendar_data.csv에서 절(節)만 추출 → [(date, term_hanja, ...)]."""
    import sajupy
    csv_path = Path(sajupy.__file__).parent / "calendar_data.csv"
    terms = []
    with open(csv_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            t = row.get("solar_term_hanja", "").strip()
            if t in JEOL_TERMS_HANJA:
                d = date(int(row["year"]), int(row["month"]), int(row["day"]))
                terms.append((d, t))
    terms.sort()
    return terms


_TERMS_CACHE: Optional[List[tuple]] = None


def get_jeol_terms() -> List[tuple]:
    global _TERMS_CACHE
    if _TERMS_CACHE is None:
        _TERMS_CACHE = _load_jeol_terms()
    return _TERMS_CACHE


def next_pillar(pillar: str, forward: bool = True) -> str:
    s, b = pillar[0], pillar[1]
    si = STEMS.index(s)
    bi = BRANCHES.index(b)
    if forward:
        return STEMS[(si + 1) % 10] + BRANCHES[(bi + 1) % 12]
    return STEMS[(si - 1) % 10] + BRANCHES[(bi - 1) % 12]


def calc_daewoon(result: Dict[str, Any], gender: str, count: int = 9) -> Dict[str, Any]:
    """대운 계산.

    Args:
        result : saju.agent.calc() 반환값
        gender : 'M' 또는 'F'
        count  : 표시할 대운 개수 (기본 9 → 약 90년치)
    """
    if gender not in ("M", "F"):
        raise ValueError("gender는 'M' 또는 'F'")

    inp = result["input"]
    p = result["pillars"]
    year_stem = p["year_stem"]
    month_pillar = p["month_pillar"]

    is_yang_year = year_stem in YANG_STEMS
    forward = (is_yang_year and gender == "M") or (not is_yang_year and gender == "F")

    birth = date(inp["year"], inp["month"], inp["day"])
    terms = get_jeol_terms()

    if forward:
        nexts = [t for t in terms if t[0] > birth]
        if not nexts:
            raise RuntimeError("절기 데이터 부족")
        target_date, target_term = nexts[0]
        days_diff = (target_date - birth).days
    else:
        prevs = [t for t in terms if t[0] <= birth]
        if not prevs:
            raise RuntimeError("절기 데이터 부족")
        target_date, target_term = prevs[-1]
        days_diff = (birth - target_date).days

    # 대운수 = days ÷ 3 (반올림). 0이면 1로
    daewoon_su = max(1, round(days_diff / 3))

    # 대운 진행
    series = []
    cur = month_pillar
    for i in range(count):
        cur = next_pillar(cur, forward=forward)
        start_age = daewoon_su + i * 10
        end_age = start_age + 9
        series.append({
            "order": i + 1,
            "pillar": cur,
            "stem": cur[0],
            "branch": cur[1],
            "start_age": start_age,
            "end_age": end_age,
        })

    return {
        "gender": gender,
        "direction": "순행" if forward else "역행",
        "rule": _describe_rule(year_stem, gender, forward),
        "daewoon_su": daewoon_su,
        "anchor_term": target_term,
        "anchor_date": target_date.isoformat(),
        "days_to_term": days_diff,
        "series": series,
    }


def _describe_rule(year_stem: str, gender: str, forward: bool) -> str:
    yy = "양" if year_stem in YANG_STEMS else "음"
    gg = "남자" if gender == "M" else "여자"
    return f"년간 {yy}({year_stem}) + {gg} → {'순행' if forward else '역행'}"


def format_daewoon(dw: Dict[str, Any]) -> str:
    lines = ["【대운】"]
    lines.append(f"  방향: {dw['direction']} ({dw['rule']})")
    lines.append(f"  대운수: {dw['daewoon_su']}세 시작 (출생↔{dw['anchor_term']} {dw['days_to_term']}일)")
    lines.append("")
    for d in dw["series"]:
        lines.append(f"  {d['start_age']:>3}~{d['end_age']:>3}세  {d['pillar']}")
    return "\n".join(lines)


def _selftest() -> int:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from saju.agent import calc
    passed, total = 0, 0

    total += 1
    assert next_pillar("乙丑", True) == "丙寅"
    assert next_pillar("乙丑", False) == "甲子"
    print("  ✓ next_pillar 순/역")
    passed += 1

    # 음남 역행: 년간 癸(음) + 남자 → 역행 (합성 케이스로 검증)
    total += 1
    fake_eumnam = {"input": {"year": 1990, "month": 5, "day": 15},
                   "pillars": {"year_stem": "癸", "month_pillar": "乙丑"}}
    dw = calc_daewoon(fake_eumnam, gender="M")
    assert dw["direction"] == "역행", dw
    assert dw["series"][0]["pillar"] == "甲子"  # 월주 乙丑의 역행 첫 = 甲子
    print(f"  ✓ 음남 역행 첫 운: 甲子")
    passed += 1

    # 양남 순행: 년간 甲(양) + 남자 → 순행
    total += 1
    fake_yangnam = {"input": {"year": 2024, "month": 5, "day": 15},
                    "pillars": {"year_stem": "甲", "month_pillar": "己巳"}}
    dw2 = calc_daewoon(fake_yangnam, gender="M")
    assert dw2["direction"] == "순행"
    print(f"  ✓ 양남 순행: 첫 운 {dw2['series'][0]['pillar']}")
    passed += 1

    # 음녀 순행: 년간 癸(음) + 여자 → 순행
    total += 1
    dw3 = calc_daewoon(fake_eumnam, gender="F")
    assert dw3["direction"] == "순행"
    print(f"  ✓ 음녀 순행: 첫 운 {dw3['series'][0]['pillar']}")
    passed += 1

    # 실데이터 smoke test — 대운수 양수, series 개수 일치
    total += 1
    r = calc(year=1990, month=5, day=15, hour=14, minute=0,
             longitude=126.978, time_mode="approx")
    dw_real = calc_daewoon(r, gender="M", count=8)
    assert dw_real["daewoon_su"] >= 1
    assert len(dw_real["series"]) == 8
    print(f"  ✓ 실 명식 대운: {dw_real['direction']} / 대운수 {dw_real['daewoon_su']}세")
    passed += 1

    total += 1
    txt = format_daewoon(dw)
    assert "대운" in txt and "甲子" in txt
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
        print(format_daewoon(calc_daewoon(r, gender="M")))
    else:
        print(__doc__)
