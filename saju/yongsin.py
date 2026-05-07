#!/usr/bin/env python3
"""saju.yongsin — 용신·기신 후보 도출 (단순화 억부+조후).

⚠️ 단순화 모델 — 실제 명리는 통근/투출/합충/조후/병약 등 복합 판단.
출력은 '후보'로 표시. 풀이 시 LLM이 보강.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, List

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from saju.agent import STEM_ELEMENT, BRANCH_ELEMENT, SHENG, KE, ten_god

ELEMENT_KO = {"木": "목", "火": "화", "土": "토", "金": "금", "水": "수"}

WINTER_BRANCHES = {"亥", "子", "丑"}
SUMMER_BRANCHES = {"巳", "午", "未"}
DRY_BRANCHES = {"辰", "戌"}


def _inseong_element(day_element: str) -> str:
    for k, v in SHENG.items():
        if v == day_element:
            return k
    return ""


def derive_yongsin(result: Dict[str, Any]) -> Dict[str, Any]:
    p = result["pillars"]
    fe = result["five_elements"]
    dist = fe["distribution"]
    total = sum(dist.values())

    day_stem = p["day_stem"]
    day_element = STEM_ELEMENT[day_stem][0]
    inseong = _inseong_element(day_element)
    month_branch = p["month_branch"]

    self_pct = (dist[day_element] + dist[inseong]) / total if total else 0

    if self_pct >= 0.5:
        strength = "신강"
        candidates = [SHENG[day_element], KE[day_element]]
        for k, v in KE.items():
            if v == day_element:
                candidates.append(k)
                break
        rationale = "일간이 강하니 설기(식상)·재성·관성으로 균형을 잡는다"
    elif self_pct <= 0.3:
        strength = "신약"
        candidates = [day_element, inseong]
        rationale = "일간이 약하니 비겁·인성으로 보태야 한다"
    else:
        strength = "중화"
        candidates = []
        rationale = "음양오행이 비교적 균형이라 큰 결함은 없다 — 약한 오행을 보충"

    weakest = fe["weakest"]
    if weakest not in candidates and dist[weakest] == 0:
        candidates.append(weakest)

    johoo = []
    if month_branch in WINTER_BRANCHES and dist["火"] <= 1:
        johoo.append("火 (겨울월 한기 풀기)")
    if month_branch in SUMMER_BRANCHES and dist["水"] <= 1:
        johoo.append("水 (여름월 열기 식히기)")
    if month_branch in DRY_BRANCHES and dist["水"] == 0:
        johoo.append("水 (건조월 윤택)")

    gisin = set()
    for c in candidates:
        for k, v in KE.items():
            if v == c:
                gisin.add(k)
                break

    candidate_tg = []
    for c in candidates:
        for stem, (el, _) in STEM_ELEMENT.items():
            if el == c:
                candidate_tg.append({
                    "element": c,
                    "element_ko": ELEMENT_KO[c],
                    "ten_god_sample": ten_god(day_stem, stem),
                })
                break

    return {
        "strength": strength,
        "self_ratio": round(self_pct, 2),
        "rationale": rationale,
        "yongsin_candidates": candidate_tg,
        "johoo_adjustment": johoo,
        "gisin_candidates": [{"element": g, "element_ko": ELEMENT_KO[g]} for g in gisin],
        "_note": "단순화 억부+조후 — 실제 풀이 시 통근·투출·합충 추가 검토",
    }


def format_yongsin(y: Dict[str, Any]) -> str:
    lines = ["【용신·기신】"]
    lines.append(f"  일간 강약: {y['strength']} (자체비율 {y['self_ratio']*100:.0f}%)")
    lines.append(f"  근거: {y['rationale']}")
    lines.append("  용신 후보:")
    for c in y["yongsin_candidates"]:
        lines.append(f"    · {c['element']}({c['element_ko']}) — {c['ten_god_sample']} 계열")
    if y["johoo_adjustment"]:
        lines.append(f"  조후 보정: {', '.join(y['johoo_adjustment'])}")
    if y["gisin_candidates"]:
        gs = ", ".join(c["element_ko"] for c in y["gisin_candidates"])
        lines.append(f"  기신: {gs}")
    lines.append(f"  ⚠ {y['_note']}")
    return "\n".join(lines)


def _selftest() -> int:
    from saju.agent import calc
    passed, total = 0, 0

    # 표준 표본: 1990.05.15 14:00 서울
    total += 1
    r = calc(year=1990, month=5, day=15, hour=14, minute=0,
             longitude=126.978, time_mode="approx")
    y = derive_yongsin(r)
    assert y["strength"] in ("신강", "신약", "중화")
    assert 0 <= y["self_ratio"] <= 1
    assert isinstance(y["yongsin_candidates"], list)
    assert isinstance(y["johoo_adjustment"], list)
    assert isinstance(y["gisin_candidates"], list)
    print(f"  ✓ 명식 강약: {y['strength']} ({y['self_ratio']})")
    passed += 1

    # 합성 fixture로 火 조후 로직 직접 검증 (겨울월 + 火 부족)
    total += 1
    fake_winter = {
        "pillars": {"day_stem": "甲", "month_branch": "丑"},
        "five_elements": {
            "distribution": {"木": 2, "火": 0, "土": 2, "金": 2, "水": 2},
            "weakest": "火",
        },
    }
    y_w = derive_yongsin(fake_winter)
    assert any("火" in s for s in y_w["johoo_adjustment"]), y_w["johoo_adjustment"]
    print(f"  ✓ 조후 火 보정 (丑월 + 火부족): {y_w['johoo_adjustment']}")
    passed += 1

    # 합성 fixture로 水 조후 로직 직접 검증 (여름월 + 水 부족)
    total += 1
    fake_summer = {
        "pillars": {"day_stem": "甲", "month_branch": "午"},
        "five_elements": {
            "distribution": {"木": 2, "火": 3, "土": 2, "金": 1, "水": 0},
            "weakest": "水",
        },
    }
    y_s = derive_yongsin(fake_summer)
    assert any("水" in s for s in y_s["johoo_adjustment"]), y_s["johoo_adjustment"]
    print(f"  ✓ 조후 水 보정 (午월 + 水부족): {y_s['johoo_adjustment']}")
    passed += 1

    total += 1
    txt = format_yongsin(y)
    assert "용신" in txt
    print("  ✓ format")
    passed += 1

    print(f"✅ selftest passed: {passed}/{total}")
    return 0 if passed == total else 1


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "selftest":
        sys.exit(_selftest())
    elif len(sys.argv) > 1 and sys.argv[1] == "demo":
        from saju.agent import calc
        r = calc(year=1990, month=5, day=15, hour=14, minute=0,
                 longitude=126.978, time_mode="approx")
        print(format_yongsin(derive_yongsin(r)))
    else:
        print(__doc__)
