#!/usr/bin/env python3
"""saju.compatibility — 두 사람 사주 궁합 분석.

분석 차원 (단순화):
  1. 일주 합/충 — 일지(배우자궁) 간 관계
  2. 오행 보완 — 한쪽 약한 오행을 상대가 채워주는가
  3. 십신 작용 — 상대 일간이 나에게 어떤 십신인가 (정관·편관·정인 등)
  4. 띠(년지) 합/충

⚠️ 명리 궁합은 학파별 해석 다름. 본 모듈은 표면 신호만 출력 → LLM이 풀이.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from saju.agent import STEM_ELEMENT, BRANCH_ELEMENT, SHENG, KE, ten_god

# 지지 육합
YUKHAP = {("子", "丑"), ("寅", "亥"), ("卯", "戌"), ("辰", "酉"), ("巳", "申"), ("午", "未")}
# 지지 충
CHUNG = {("子", "午"), ("丑", "未"), ("寅", "申"), ("卯", "酉"), ("辰", "戌"), ("巳", "亥")}
# 천간 합
CHEONGAN_HAP = {("甲", "己"): "土", ("乙", "庚"): "金", ("丙", "辛"): "水",
                ("丁", "壬"): "木", ("戊", "癸"): "火"}


def _pair_key(a: str, b: str, table) -> bool:
    return (a, b) in table or (b, a) in table


def _cheongan_hap_get(a: str, b: str):
    return CHEONGAN_HAP.get((a, b)) or CHEONGAN_HAP.get((b, a))


def analyze_compatibility(person_a: Dict[str, Any], person_b: Dict[str, Any]) -> Dict[str, Any]:
    """두 saju.agent.calc() 결과를 받아 궁합 신호 dict 반환."""
    pa, pb = person_a["pillars"], person_b["pillars"]

    # 1. 일주 합/충
    day_signal = []
    if _pair_key(pa["day_branch"], pb["day_branch"], YUKHAP):
        day_signal.append("일지 육합 (배우자궁 친화)")
    if _pair_key(pa["day_branch"], pb["day_branch"], CHUNG):
        day_signal.append("일지 충 (배우자궁 충돌·자극)")
    cg = _cheongan_hap_get(pa["day_stem"], pb["day_stem"])
    if cg:
        day_signal.append(f"일간 합 → {cg} 합화 (강한 결속)")

    # 2. 띠 합/충
    year_signal = []
    if _pair_key(pa["year_branch"], pb["year_branch"], YUKHAP):
        year_signal.append("년지 육합 (집안 친화)")
    if _pair_key(pa["year_branch"], pb["year_branch"], CHUNG):
        year_signal.append("년지 충 (띠 충 — 가풍 차이)")

    # 3. 오행 보완
    fa = person_a["five_elements"]["distribution"]
    fb = person_b["five_elements"]["distribution"]
    a_lacks = [el for el, c in fa.items() if c == 0]
    b_lacks = [el for el, c in fb.items() if c == 0]
    a_supplied_by_b = [el for el in a_lacks if fb.get(el, 0) >= 2]
    b_supplied_by_a = [el for el in b_lacks if fa.get(el, 0) >= 2]

    # 4. 상대 일간이 나에게 어떤 십신인가
    a_to_b_god = ten_god(pa["day_stem"], pb["day_stem"])
    b_to_a_god = ten_god(pb["day_stem"], pa["day_stem"])

    # 점수 (단순)
    score = 50
    score += 15 * len(day_signal)  # 일주 작용
    score += 5 * len(year_signal)
    score += 10 * len(a_supplied_by_b)
    score += 10 * len(b_supplied_by_a)
    if any("충" in s for s in day_signal + year_signal):
        score -= 10
    score = max(0, min(100, score))

    return {
        "day_signal": day_signal,
        "year_signal": year_signal,
        "element_supply": {
            "a_lacks_supplied_by_b": a_supplied_by_b,
            "b_lacks_supplied_by_a": b_supplied_by_a,
        },
        "ten_god_view": {
            "b_is_to_a": a_to_b_god,
            "a_is_to_b": b_to_a_god,
        },
        "score_simple": score,
        "_note": "표면 신호 합산 — 실제 궁합은 용신 호환·대운 흐름까지 봐야 정확하다",
    }


def format_compatibility(c: Dict[str, Any], name_a: str = "갑", name_b: str = "을") -> str:
    lines = [f"【궁합 분석: {name_a} ↔ {name_b}】"]
    lines.append(f"  단순 점수: {c['score_simple']}/100")
    if c["day_signal"]:
        lines.append("  일주 작용:")
        for s in c["day_signal"]:
            lines.append(f"    · {s}")
    if c["year_signal"]:
        lines.append("  띠 작용:")
        for s in c["year_signal"]:
            lines.append(f"    · {s}")
    es = c["element_supply"]
    if es["a_lacks_supplied_by_b"]:
        lines.append(f"  {name_b}이(가) {name_a}에게 보태는 오행: {', '.join(es['a_lacks_supplied_by_b'])}")
    if es["b_lacks_supplied_by_a"]:
        lines.append(f"  {name_a}이(가) {name_b}에게 보태는 오행: {', '.join(es['b_lacks_supplied_by_a'])}")
    tv = c["ten_god_view"]
    lines.append(f"  십신 시각: {name_a}에게 {name_b}은 {tv['b_is_to_a']}, {name_b}에게 {name_a}은 {tv['a_is_to_b']}")
    lines.append(f"  ⚠ {c['_note']}")
    return "\n".join(lines)


def _selftest() -> int:
    from saju.agent import calc
    passed, total = 0, 0

    # 익명 표본 A: 1990.05.15 14:00 서울
    a = calc(year=1990, month=5, day=15, hour=14, minute=0, longitude=126.978, time_mode="approx")
    # 익명 표본 B: 1992.08.20 12:00 서울
    b = calc(year=1992, month=8, day=20, hour=12, minute=0, longitude=126.978, time_mode="approx")

    total += 1
    c = analyze_compatibility(a, b)
    assert "score_simple" in c
    assert 0 <= c["score_simple"] <= 100
    print(f"  ✓ 점수: {c['score_simple']}/100")
    passed += 1

    total += 1
    assert "ten_god_view" in c
    print(f"  ✓ 십신 시각: {c['ten_god_view']}")
    passed += 1

    total += 1
    txt = format_compatibility(c, "갑", "을")
    assert "궁합" in txt
    print("  ✓ format")
    passed += 1

    # 일간합 케이스: 甲↔己
    total += 1
    fake_a = {"pillars": {"day_stem": "甲", "day_branch": "子", "year_branch": "子"},
              "five_elements": {"distribution": {"木": 2, "火": 0, "土": 0, "金": 0, "水": 6}}}
    fake_b = {"pillars": {"day_stem": "己", "day_branch": "丑", "year_branch": "丑"},
              "five_elements": {"distribution": {"木": 0, "火": 0, "土": 4, "金": 2, "水": 2}}}
    c2 = analyze_compatibility(fake_a, fake_b)
    assert any("일간 합" in s for s in c2["day_signal"])
    assert any("일지 육합" in s for s in c2["day_signal"])
    print(f"  ✓ 갑기합·자축합 시너지: {c2['score_simple']}")
    passed += 1

    print(f"✅ selftest passed: {passed}/{total}")
    return 0 if passed == total else 1


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "selftest":
        sys.exit(_selftest())
    else:
        print(__doc__)
