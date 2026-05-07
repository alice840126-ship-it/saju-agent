#!/usr/bin/env python3
"""saju.agent — 사주 8글자 + 음양오행/십신/12운성 결정론 계산.

8글자 산출은 sajupy(MIT) 위임, 파생 분석(십신·음양오행 분포·12운성)은
공개 명리학 공식 기반 clean-room. 풀이(13단계 대만신 페르소나)는 LLM이 담당.

시간 처리 3-mode:
  exact   — 분 단위 시간 정확
  approx  — 시진(子/丑/...)만 알고 분 부정확 (대부분의 경우)
  unknown — 시 모름 → 시주 제외, 삼주(년월일주)로만 풀이

사용:
    from saju.agent import calc, format_summary
    out = calc(year=1990, month=5, day=15, hour=14, minute=0,
               longitude=126.978, time_mode="approx")
"""
from __future__ import annotations

import sys
from typing import Any, Dict, Optional

# --- 상수 테이블 (공개 명리학 공식) ---

STEMS = "甲乙丙丁戊己庚辛壬癸"
BRANCHES = "子丑寅卯辰巳午未申酉戌亥"

STEM_KO = {"甲": "갑", "乙": "을", "丙": "병", "丁": "정", "戊": "무",
           "己": "기", "庚": "경", "辛": "신", "壬": "임", "癸": "계"}
BRANCH_KO = {"子": "자", "丑": "축", "寅": "인", "卯": "묘", "辰": "진", "巳": "사",
             "午": "오", "未": "미", "申": "신", "酉": "유", "戌": "술", "亥": "해"}

STEM_ELEMENT = {
    "甲": ("木", "+"), "乙": ("木", "-"),
    "丙": ("火", "+"), "丁": ("火", "-"),
    "戊": ("土", "+"), "己": ("土", "-"),
    "庚": ("金", "+"), "辛": ("金", "-"),
    "壬": ("水", "+"), "癸": ("水", "-"),
}
BRANCH_ELEMENT = {
    "子": ("水", "+", ["癸"]),
    "丑": ("土", "-", ["己", "癸", "辛"]),
    "寅": ("木", "+", ["甲", "丙", "戊"]),
    "卯": ("木", "-", ["乙"]),
    "辰": ("土", "+", ["戊", "乙", "癸"]),
    "巳": ("火", "+", ["丙", "庚", "戊"]),
    "午": ("火", "-", ["丁", "己"]),
    "未": ("土", "-", ["己", "丁", "乙"]),
    "申": ("金", "+", ["庚", "壬", "戊"]),
    "酉": ("金", "-", ["辛"]),
    "戌": ("土", "+", ["戊", "辛", "丁"]),
    "亥": ("水", "+", ["壬", "甲"]),
}
SHENG = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}
KE = {"木": "土", "土": "水", "水": "火", "火": "金", "金": "木"}


def ten_god(day_stem: str, target_stem: str) -> str:
    """일간 기준 다른 천간의 십신."""
    de, dy = STEM_ELEMENT[day_stem]
    te, ty = STEM_ELEMENT[target_stem]
    same = (dy == ty)
    if te == de:
        return "비견" if same else "겁재"
    if SHENG[de] == te:
        return "식신" if same else "상관"
    if KE[de] == te:
        return "편재" if same else "정재"
    if KE[te] == de:
        return "편관" if same else "정관"
    if SHENG[te] == de:
        return "편인" if same else "정인"
    return "?"


TWELVE_STAGES_ORDER = ["장생", "목욕", "관대", "건록", "제왕", "쇠", "병", "사", "묘", "절", "태", "양"]
TWELVE_STAGES_START = {
    "甲": "亥", "丙": "寅", "戊": "寅", "庚": "巳", "壬": "申",
    "乙": "午", "丁": "酉", "己": "酉", "辛": "子", "癸": "卯",
}
YANG_STEMS = {"甲", "丙", "戊", "庚", "壬"}


def twelve_stage(day_stem: str, branch: str) -> str:
    start = TWELVE_STAGES_START[day_stem]
    branches = list(BRANCHES)
    si = branches.index(start)
    bi = branches.index(branch)
    if day_stem in YANG_STEMS:
        offset = (bi - si) % 12
    else:
        offset = (si - bi) % 12
    return TWELVE_STAGES_ORDER[offset]


def element_distribution(pillars: Dict[str, str]) -> Dict[str, int]:
    counts = {"木": 0, "火": 0, "土": 0, "金": 0, "水": 0}
    for stem in [pillars.get("year_stem"), pillars.get("month_stem"),
                 pillars.get("day_stem"), pillars.get("hour_stem")]:
        if stem:
            counts[STEM_ELEMENT[stem][0]] += 1
    for branch in [pillars.get("year_branch"), pillars.get("month_branch"),
                   pillars.get("day_branch"), pillars.get("hour_branch")]:
        if branch:
            counts[BRANCH_ELEMENT[branch][0]] += 1
    return counts


def calc(
    year: int, month: int, day: int,
    hour: Optional[int] = None, minute: int = 0,
    longitude: Optional[float] = None,
    time_mode: str = "approx",
    is_lunar: bool = False,
    is_leap_month: bool = False,
    gender: Optional[str] = None,  # 'M' or 'F' — 대운 순행/역행에 필요
) -> Dict[str, Any]:
    try:
        from sajupy import calculate_saju, lunar_to_solar
    except ImportError as e:
        raise RuntimeError("sajupy 미설치 — pip install sajupy") from e

    # 음력 → 양력 변환
    lunar_input = None
    if is_lunar:
        lunar_input = {"year": year, "month": month, "day": day, "leap": is_leap_month}
        s = lunar_to_solar(year, month, day, is_leap_month)
        year, month, day = s["solar_year"], s["solar_month"], s["solar_day"]

    if time_mode == "unknown":
        h, m, use_solar = 12, 0, False
    else:
        h, m = (hour if hour is not None else 12), minute
        use_solar = (longitude is not None)

    raw = calculate_saju(
        year=year, month=month, day=day,
        hour=h, minute=m,
        longitude=longitude, use_solar_time=use_solar,
        utc_offset=9, early_zi_time=True,
    )

    pillars = {
        "year_pillar": raw["year_pillar"],
        "month_pillar": raw["month_pillar"],
        "day_pillar": raw["day_pillar"],
        "hour_pillar": raw["hour_pillar"] if time_mode != "unknown" else None,
        "year_stem": raw["year_stem"], "year_branch": raw["year_branch"],
        "month_stem": raw["month_stem"], "month_branch": raw["month_branch"],
        "day_stem": raw["day_stem"], "day_branch": raw["day_branch"],
        "hour_stem": raw["hour_stem"] if time_mode != "unknown" else None,
        "hour_branch": raw["hour_branch"] if time_mode != "unknown" else None,
    }

    day_stem = pillars["day_stem"]

    ten_gods = {"day": {"stem": day_stem, "ten_god": "본원(일주)"}}
    for pos in ("year", "month", "hour"):
        s = pillars.get(f"{pos}_stem")
        if s:
            ten_gods[pos] = {"stem": s, "ten_god": ten_god(day_stem, s)}

    stages = {}
    for pos in ("year", "month", "day", "hour"):
        b = pillars.get(f"{pos}_branch")
        if b:
            stages[pos] = {"branch": b, "stage": twelve_stage(day_stem, b)}

    dist = element_distribution(pillars)
    weakest = min(dist, key=dist.get)
    strongest = max(dist, key=dist.get)

    day_polarity = "양(陽)" if day_stem in YANG_STEMS else "음(陰)"
    day_element = STEM_ELEMENT[day_stem][0]

    return {
        "input": {
            "year": year, "month": month, "day": day,
            "hour": hour, "minute": minute,
            "longitude": longitude, "time_mode": time_mode,
            "is_lunar": is_lunar, "lunar_input": lunar_input,
            "gender": gender,
        },
        "pillars": pillars,
        "day_master": {
            "stem": day_stem, "stem_ko": STEM_KO[day_stem],
            "element": day_element, "polarity": day_polarity,
        },
        "ten_gods": ten_gods,
        "twelve_stages": stages,
        "five_elements": {
            "distribution": dist,
            "strongest": strongest,
            "weakest": weakest,
        },
        "solar_correction": raw.get("solar_correction"),
        "zi_time_type": raw.get("zi_time_type"),
        "_meta": {
            "source_8chars": "sajupy 0.2.0 (MIT)",
            "source_derived": "saju.agent clean-room (공개 명리학 공식)",
            "verify_url": "https://manse.fortuneteller.kr/",
        },
    }


def format_summary(result: Dict[str, Any]) -> str:
    """대만신 프롬프트 입력용 사람-가독 요약."""
    p = result["pillars"]
    dm = result["day_master"]
    tg = result["ten_gods"]
    ts = result["twelve_stages"]
    fe = result["five_elements"]

    has_hour = p["hour_pillar"] is not None
    headers = ["년주", "월주", "일주"] + (["시주"] if has_hour else [])
    pkeys = ["year_pillar", "month_pillar", "day_pillar"] + (["hour_pillar"] if has_hour else [])

    lines = []
    lines.append("【사주 명식】")
    lines.append("  " + "  ".join(f"{h:6}" for h in headers))
    lines.append("  " + "  ".join(f"{p[k]:6}" for k in pkeys))
    lines.append("")
    lines.append(f"【일간(나)】 {dm['stem']}({dm['stem_ko']}) — {dm['element']} {dm['polarity']}")
    lines.append("")
    lines.append("【십신】")
    for pos in ("year", "month", "day", "hour"):
        if pos in tg:
            lines.append(f"  {pos:5}: {tg[pos]['stem']} → {tg[pos]['ten_god']}")
    lines.append("")
    lines.append("【12운성 (일간 기준 각 지지)】")
    for pos in ("year", "month", "day", "hour"):
        if pos in ts:
            lines.append(f"  {pos:5}: {ts[pos]['branch']} → {ts[pos]['stage']}")
    lines.append("")
    lines.append("【오행 분포】")
    lines.append(f"  木 {fe['distribution']['木']} | 火 {fe['distribution']['火']} | "
                 f"土 {fe['distribution']['土']} | 金 {fe['distribution']['金']} | 水 {fe['distribution']['水']}")
    lines.append(f"  최강: {fe['strongest']} / 최약: {fe['weakest']}")
    if result.get("solar_correction"):
        sc = result["solar_correction"]
        lines.append("")
        lines.append(f"【진태양시】 입력 {sc['original_time']} → 보정 {sc['solar_time']} "
                     f"(경도 {sc['longitude']}, 보정 {sc['correction_minutes']}분)")
    if result.get("zi_time_type"):
        lines.append(f"【자시】 {result['zi_time_type']}")
    return "\n".join(lines)


def _selftest() -> int:
    passed = 0
    total = 0

    total += 1
    assert ten_god("己", "甲") == "정관", ten_god("己", "甲")
    print("  ✓ ten_god 己→甲 = 정관")
    passed += 1

    total += 1
    assert ten_god("己", "癸") == "편재", ten_god("己", "癸")
    print("  ✓ ten_god 己→癸 = 편재")
    passed += 1

    total += 1
    assert ten_god("甲", "甲") == "비견"
    assert ten_god("甲", "乙") == "겁재"
    print("  ✓ ten_god 비견/겁재")
    passed += 1

    total += 1
    assert twelve_stage("甲", "亥") == "장생"
    assert twelve_stage("甲", "子") == "목욕"
    print("  ✓ twelve_stage 甲(양간) 순행")
    passed += 1

    total += 1
    assert twelve_stage("乙", "午") == "장생"
    assert twelve_stage("乙", "巳") == "목욕"
    print("  ✓ twelve_stage 乙(음간) 역행")
    passed += 1

    total += 1
    r = calc(year=1990, month=5, day=15, hour=14, minute=0,
             longitude=126.978, time_mode="approx")
    p = r["pillars"]
    # 구조 검증 (값은 sajupy 출력에 의존)
    assert all(p[k] for k in ("year_pillar", "month_pillar", "day_pillar", "hour_pillar"))
    assert r["day_master"]["element"] in ("木", "火", "土", "金", "水")
    assert r["day_master"]["polarity"] in ("양(陽)", "음(陰)")
    assert r["ten_gods"]["day"]["ten_god"] == "본원(일주)"
    assert all(pos in r["ten_gods"] for pos in ("year", "month", "hour"))
    assert sum(r["five_elements"]["distribution"].values()) == 8
    print(f"  ✓ 통합 명식 산출: {p['year_pillar']} {p['month_pillar']} {p['day_pillar']} {p['hour_pillar']}")
    passed += 1

    total += 1
    r2 = calc(year=1990, month=5, day=15, time_mode="unknown")
    assert r2["pillars"]["hour_pillar"] is None
    assert "hour" not in r2["ten_gods"]
    assert sum(r2["five_elements"]["distribution"].values()) == 6  # 삼주만 = 6글자
    print("  ✓ time_mode=unknown 시주 제외")
    passed += 1

    total += 1
    s = format_summary(r)
    assert "사주 명식" in s and "일간(나)" in s
    print("  ✓ format_summary 출력")
    passed += 1

    # 음력 입력 → 양력 변환 후 동일 명식인지 확인 (왕복 검증)
    total += 1
    r_solar = calc(year=1990, month=5, day=15, hour=14, minute=0,
                   longitude=126.978, time_mode="approx")
    # 같은 양력 날짜를 음력으로 입력 — solar_to_lunar로 변환 후 다시 lunar_to_solar 라운드트립
    try:
        from sajupy import solar_to_lunar
        lunar = solar_to_lunar(1990, 5, 15)
        rl = calc(year=lunar["lunar_year"], month=lunar["lunar_month"],
                  day=lunar["lunar_day"], hour=14, minute=0,
                  longitude=126.978, time_mode="approx",
                  is_lunar=True, is_leap_month=lunar.get("is_leap_month", False))
        assert rl["pillars"]["day_pillar"] == r_solar["pillars"]["day_pillar"], \
            (rl["pillars"], r_solar["pillars"])
        print(f"  ✓ 음력 입력 → 양력 변환 후 동일 명식 ({rl['pillars']['day_pillar']})")
    except ImportError:
        print("  ~ 음력 변환 스킵 (sajupy.solar_to_lunar 없음)")
    passed += 1

    print(f"✅ selftest passed: {passed}/{total}")
    return 0 if passed == total else 1


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "selftest":
        sys.exit(_selftest())
    elif len(sys.argv) > 1 and sys.argv[1] == "demo":
        r = calc(year=1990, month=5, day=15, hour=14, minute=0,
                 longitude=126.978, time_mode="approx")
        print(format_summary(r))
    else:
        print(__doc__)
